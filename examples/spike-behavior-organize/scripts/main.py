#!/usr/bin/env python3
"""
Standardize multi-format neural spike and behavior data into unified HDF5.

Supported input formats:
  - XDS .mat files (TrialData / xds struct)
  - NWB files (.nwb) via pynwb
  - PyalData .mat files (trial-structured arrays)

Output: a single HDF5 file with a uniform schema per trial:
  /dataset/session/trial_NNN/{timestamps, spikes, behavior/{position, velocity, acceleration}}

Usage:
  python main.py config.json
  python main.py config.json --bin-size 0.02 --output standardized.h5
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import h5py
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter1d
from scipy.io import loadmat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("spike_behavior_organize")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_BIN_SIZE_S = 0.02  # 20 ms

# Mapping: source_type -> (field_name, success_value)
# If field_name is None the source has no outcome field and all trials are kept.
SUCCESS_MARKERS: Dict[str, Tuple[Optional[str], Any]] = {
    "xds": ("result", "R"),
    "pyaldata": ("result", 1),
    "nwb_000121": ("outcome", "success"),
    "nwb_000070": (None, None),
}

# Quality-check bitmask flags
QC_FLAG_EMPTY_UNITS = 1 << 0       # some units have zero spikes
QC_FLAG_HIGH_FR = 1 << 1           # any unit > 300 Hz mean firing rate
QC_FLAG_NAN_BEHAVIOR = 1 << 2      # NaN values in behavior arrays
QC_FLAG_SHORT_TRIAL = 1 << 3       # trial duration < minimum threshold
QC_FLAG_LOW_SPIKE_COUNT = 1 << 4   # total spike count suspiciously low
QC_FLAG_CONSTANT_BEHAVIOR = 1 << 5 # behavior channel is constant (no variance)

# ===================================================================
# Data Loaders
# ===================================================================


def _unwrap_matlab_struct(mat_struct: np.ndarray) -> Any:
    """Recursively unwrap a MATLAB struct loaded by scipy.io.loadmat.

    MATLAB structs are stored as numpy structured arrays.  The canonical
    access pattern is ``mat_struct[0, 0]`` to get the first (and usually
    only) element, then field access via ``dtype.names``.
    """
    if isinstance(mat_struct, np.ndarray):
        if mat_struct.dtype.names is not None:
            # It is a structured array / MATLAB struct
            elem = mat_struct[0, 0] if mat_struct.ndim >= 2 else mat_struct[0]
            return elem
    return mat_struct


def load_xds_mat(filepath: str) -> Dict[str, Any]:
    """Load an XDS-format .mat file.

    Returns a dict with keys:
      - spike_times: list of np.ndarray, one per unit
      - cursor_vel: (T, 2) or None
      - cursor_pos: (T, 2) or None
      - emg: (T, N_muscles) or None
      - trial_info_table: pd.DataFrame with trial metadata
      - time_frame: (T,) timestamps for continuous signals
    """
    logger.info("Loading XDS .mat: %s", filepath)
    raw = loadmat(filepath, squeeze_me=False, struct_as_record=True)

    # Locate the main struct — common names: xds, trial_data, BCI_data
    struct_key = None
    for key in raw:
        if not key.startswith("__"):
            struct_key = key
            break
    if struct_key is None:
        raise ValueError(f"No data struct found in {filepath}")

    xds = _unwrap_matlab_struct(raw[struct_key])
    field_names = xds.dtype.names
    logger.info("XDS fields: %s", field_names)

    # -- Spike times (cell array -> list of arrays) --
    spike_times: List[np.ndarray] = []
    spike_field = None
    for candidate in ("spike_times", "spikes", "unit_spike_times"):
        if candidate in field_names:
            spike_field = candidate
            break
    if spike_field is None:
        raise KeyError("Cannot find spike_times field in XDS struct")

    raw_spikes = xds[spike_field]
    # raw_spikes is typically a (N_units, 1) object array of arrays
    raw_spikes = np.asarray(raw_spikes).squeeze()
    if raw_spikes.ndim == 0:
        raw_spikes = np.array([raw_spikes])
    for i in range(len(raw_spikes)):
        unit_st = np.asarray(raw_spikes[i]).flatten().astype(np.float64)
        spike_times.append(unit_st)

    # -- Continuous signals --
    def _get_field(name: str) -> Optional[np.ndarray]:
        if name in field_names:
            arr = np.asarray(xds[name]).squeeze()
            if arr.size == 0:
                return None
            return arr.astype(np.float64)
        return None

    cursor_vel = _get_field("cursor_vel")
    cursor_pos = _get_field("cursor_pos")
    emg = _get_field("EMG") or _get_field("emg")
    time_frame = _get_field("time_frame") or _get_field("t")

    # -- Trial info --
    trial_info_table = pd.DataFrame()
    for ti_name in ("trial_info_table", "trial_info", "trials"):
        if ti_name in field_names:
            ti_struct = xds[ti_name]
            ti_elem = _unwrap_matlab_struct(np.asarray(ti_struct))
            if ti_elem.dtype.names is not None:
                data_dict = {}
                for col in ti_elem.dtype.names:
                    vals = np.asarray(ti_elem[col]).squeeze()
                    data_dict[col] = vals
                trial_info_table = pd.DataFrame(data_dict)
            break

    return {
        "spike_times": spike_times,
        "cursor_vel": cursor_vel,
        "cursor_pos": cursor_pos,
        "emg": emg,
        "trial_info_table": trial_info_table,
        "time_frame": time_frame,
    }


def load_nwb_data(nwb_path: str) -> Dict[str, Any]:
    """Load an NWB file using pynwb.

    Returns a dict with keys:
      - spike_times: list of np.ndarray per unit
      - behavior: dict of {name: (data, timestamps)} for each behavior timeseries
      - trials: pd.DataFrame of trial information
    """
    import pynwb

    logger.info("Loading NWB: %s", nwb_path)
    io = pynwb.NWBHDF5IO(nwb_path, mode="r", load_namespaces=True)
    nwbfile = io.read()

    # -- Spike times via units table --
    spike_times: List[np.ndarray] = []
    if nwbfile.units is not None:
        n_units = len(nwbfile.units)
        logger.info("NWB units: %d", n_units)
        for idx in range(n_units):
            st = nwbfile.units.get_unit_spike_times(idx)
            spike_times.append(np.asarray(st, dtype=np.float64))
    else:
        logger.warning("No units table found in NWB file.")

    # -- Behavior timeseries --
    behavior: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

    # First look in processing['behavior']
    if "behavior" in nwbfile.processing:
        behavior_module = nwbfile.processing["behavior"]
        for ts_name in behavior_module.data_interfaces:
            ts = behavior_module.data_interfaces[ts_name]
            if hasattr(ts, "data") and hasattr(ts, "timestamps"):
                data = np.asarray(ts.data[:], dtype=np.float64)
                timestamps = np.asarray(ts.timestamps[:], dtype=np.float64)
                behavior[ts_name] = (data, timestamps)
                logger.info("  behavior/processing: %s  shape=%s", ts_name, data.shape)
            # Handle SpatialSeries inside a Position container
            elif hasattr(ts, "spatial_series"):
                for ss_name, ss in ts.spatial_series.items():
                    data = np.asarray(ss.data[:], dtype=np.float64)
                    timestamps = np.asarray(ss.timestamps[:], dtype=np.float64)
                    behavior[ss_name] = (data, timestamps)
                    logger.info("  behavior/spatial: %s  shape=%s", ss_name, data.shape)

    # Fallback: look in acquisition
    if not behavior:
        logger.info("No behavior in processing; checking acquisition...")
        for acq_name in nwbfile.acquisition:
            ts = nwbfile.acquisition[acq_name]
            if hasattr(ts, "data") and hasattr(ts, "timestamps"):
                data = np.asarray(ts.data[:], dtype=np.float64)
                timestamps = np.asarray(ts.timestamps[:], dtype=np.float64)
                behavior[acq_name] = (data, timestamps)
                logger.info("  acquisition: %s  shape=%s", acq_name, data.shape)

    # -- Trials --
    trials = pd.DataFrame()
    if nwbfile.trials is not None:
        trials = nwbfile.trials.to_dataframe().reset_index(drop=True)
        logger.info("NWB trials: %d rows, columns=%s", len(trials), list(trials.columns))

    # NOTE: we intentionally do NOT close the io here so that lazy data
    # references remain valid.  The caller should keep the reference alive.
    return {
        "spike_times": spike_times,
        "behavior": behavior,
        "trials": trials,
        "_nwb_io": io,
    }


def load_pyaldata(filepath: str, bin_size_s: Optional[float] = None) -> Dict[str, Any]:
    """Load a PyalData-format .mat file (trial-structured arrays).

    The .mat file contains a struct array of shape (N_trials, 1) or (1, N_trials).
    Each element is one trial with fields like:
      - M1_spikes, PMd_spikes, ...  (already binned spike counts)
      - vel, pos, hand_pos, cursor_pos, ...
      - bin_size (scalar, in seconds)

    Returns a dict with keys:
      - trials: list of dicts, one per trial
      - spike_field_names: list of field names matching '*spikes*'
      - bin_size_s: detected or overridden bin size
    """
    logger.info("Loading PyalData .mat: %s", filepath)
    raw = loadmat(filepath, squeeze_me=False, struct_as_record=True)

    # Locate struct array
    struct_key = None
    for key in raw:
        if not key.startswith("__"):
            struct_key = key
            break
    if struct_key is None:
        raise ValueError(f"No struct array found in {filepath}")

    struct_arr = raw[struct_key]
    # Handle (N, 1) or (1, N)
    if struct_arr.ndim == 2:
        if struct_arr.shape[0] == 1:
            struct_arr = struct_arr[0, :]
        elif struct_arr.shape[1] == 1:
            struct_arr = struct_arr[:, 0]
        else:
            struct_arr = struct_arr.ravel()
    else:
        struct_arr = struct_arr.ravel()

    n_trials = len(struct_arr)
    logger.info("PyalData: %d trials", n_trials)

    field_names = struct_arr.dtype.names
    logger.info("PyalData fields: %s", field_names)

    # Auto-detect spike fields matching '*spikes*'
    spike_field_names = [f for f in field_names if "spikes" in f.lower()]
    logger.info("Detected spike fields: %s", spike_field_names)

    # Auto-detect bin size
    detected_bin_size = None
    if "bin_size" in field_names:
        bs_val = np.asarray(struct_arr[0]["bin_size"]).flatten()
        if bs_val.size > 0:
            detected_bin_size = float(bs_val[0])
            logger.info("Detected bin_size from data: %.4f s", detected_bin_size)

    effective_bin_size = bin_size_s if bin_size_s is not None else detected_bin_size
    if effective_bin_size is None:
        effective_bin_size = DEFAULT_BIN_SIZE_S
        logger.warning("Could not detect bin_size; using default %.4f s", effective_bin_size)

    # Parse each trial
    trials: List[Dict[str, Any]] = []
    for i in range(n_trials):
        trial_struct = struct_arr[i]
        trial_dict: Dict[str, Any] = {}
        for fname in field_names:
            val = np.asarray(trial_struct[fname]).squeeze()
            # Scalars
            if val.ndim == 0:
                trial_dict[fname] = val.item()
            else:
                trial_dict[fname] = val.astype(np.float64)
        # Merge multi-brain-area spikes with np.hstack
        if spike_field_names:
            merged_parts = []
            for sf in spike_field_names:
                arr = trial_dict.get(sf)
                if arr is not None and isinstance(arr, np.ndarray) and arr.ndim >= 1:
                    if arr.ndim == 1:
                        arr = arr.reshape(-1, 1)
                    merged_parts.append(arr)
            if merged_parts:
                # All must have same number of time bins (axis=0)
                trial_dict["_merged_spikes"] = np.hstack(merged_parts)
        trials.append(trial_dict)

    return {
        "trials": trials,
        "spike_field_names": spike_field_names,
        "bin_size_s": effective_bin_size,
    }


# ===================================================================
# Trial Filtering
# ===================================================================


def filter_successful_trials(
    trial_info: pd.DataFrame,
    source_type: str,
    min_duration_s: float = 0.1,
) -> pd.DataFrame:
    """Filter trials to keep only successful ones, using the SUCCESS_MARKERS dict.

    Parameters
    ----------
    trial_info : pd.DataFrame
        DataFrame of trial metadata.
    source_type : str
        One of 'xds', 'pyaldata', 'nwb_000121', 'nwb_000070', etc.
    min_duration_s : float
        Minimum trial duration in seconds.  Trials shorter than this are dropped.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame (may have reset index).
    """
    if source_type not in SUCCESS_MARKERS:
        logger.warning("Unknown source_type '%s'; keeping all trials.", source_type)
        return trial_info.copy()

    field_name, success_value = SUCCESS_MARKERS[source_type]

    filtered = trial_info.copy()

    # Filter by outcome
    if field_name is not None and field_name in filtered.columns:
        # Handle byte-strings from MATLAB
        col = filtered[field_name]
        if col.dtype == object:
            col = col.apply(
                lambda x: x.decode("utf-8").strip() if isinstance(x, bytes) else str(x).strip()
            )
        mask = col == success_value
        n_before = len(filtered)
        filtered = filtered[mask]
        logger.info(
            "Outcome filter (%s == %s): %d -> %d trials",
            field_name, success_value, n_before, len(filtered),
        )
    elif field_name is not None:
        logger.warning(
            "Outcome field '%s' not found in trial_info; keeping all %d trials.",
            field_name, len(filtered),
        )

    # Filter by minimum duration
    start_col, end_col = None, None
    for s_cand in ("start_time", "startTime", "trial_start", "t_start"):
        if s_cand in filtered.columns:
            start_col = s_cand
            break
    for e_cand in ("end_time", "endTime", "trial_end", "t_end"):
        if e_cand in filtered.columns:
            end_col = e_cand
            break

    if start_col and end_col:
        durations = filtered[end_col].astype(float) - filtered[start_col].astype(float)
        n_before = len(filtered)
        filtered = filtered[durations >= min_duration_s]
        logger.info(
            "Duration filter (>= %.3f s): %d -> %d trials",
            min_duration_s, n_before, len(filtered),
        )

    return filtered.reset_index(drop=True)


# ===================================================================
# Time Alignment
# ===================================================================


def create_uniform_bins(
    t_start: float, t_end: float, bin_size_s: float = DEFAULT_BIN_SIZE_S,
) -> Tuple[np.ndarray, np.ndarray]:
    """Create uniform time bins.

    Returns
    -------
    bin_edges : np.ndarray, shape (N_bins + 1,)
    bin_centers : np.ndarray, shape (N_bins,)
    """
    bin_edges = np.arange(t_start, t_end + bin_size_s * 0.5, bin_size_s)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    return bin_edges, bin_centers


def bin_spike_times(
    spike_times_list: List[np.ndarray], bin_edges: np.ndarray,
) -> np.ndarray:
    """Bin spike times into counts per bin per unit.

    Parameters
    ----------
    spike_times_list : list of np.ndarray
        Each element is a 1-D array of spike times for one unit.
    bin_edges : np.ndarray, shape (N_bins + 1,)

    Returns
    -------
    spike_counts : np.ndarray, shape (N_bins, N_units), dtype int32
    """
    n_bins = len(bin_edges) - 1
    n_units = len(spike_times_list)
    spike_counts = np.zeros((n_bins, n_units), dtype=np.int32)
    for uid, st in enumerate(spike_times_list):
        if st.size == 0:
            continue
        counts, _ = np.histogram(st, bins=bin_edges)
        spike_counts[:, uid] = counts.astype(np.int32)
    return spike_counts


def resample_behavior(
    behavior_data: np.ndarray,
    behavior_timestamps: np.ndarray,
    target_bin_centers: np.ndarray,
) -> np.ndarray:
    """Resample behavior data onto target time bins using linear interpolation.

    Parameters
    ----------
    behavior_data : np.ndarray, shape (T_orig,) or (T_orig, D)
    behavior_timestamps : np.ndarray, shape (T_orig,)
    target_bin_centers : np.ndarray, shape (N_bins,)

    Returns
    -------
    resampled : np.ndarray, shape (N_bins,) or (N_bins, D)
    """
    if behavior_data.ndim == 1:
        f = interp1d(
            behavior_timestamps, behavior_data,
            kind="linear", fill_value="extrapolate", assume_sorted=True,
        )
        return f(target_bin_centers).astype(np.float64)
    else:
        n_dims = behavior_data.shape[1]
        resampled = np.zeros((len(target_bin_centers), n_dims), dtype=np.float64)
        for d in range(n_dims):
            f = interp1d(
                behavior_timestamps, behavior_data[:, d],
                kind="linear", fill_value="extrapolate", assume_sorted=True,
            )
            resampled[:, d] = f(target_bin_centers)
        return resampled


def resample_already_binned(
    binned_data: np.ndarray,
    orig_bin_size_s: float,
    target_bin_size_s: float,
) -> np.ndarray:
    """Resample already-binned data (e.g., PyalData spike counts) to a new bin size.

    Only supports integer-ratio rebinning.  If the ratio is not an integer,
    the data is interpolated to the closest feasible size.

    Parameters
    ----------
    binned_data : np.ndarray, shape (N_orig,) or (N_orig, D)
    orig_bin_size_s : float
    target_bin_size_s : float

    Returns
    -------
    rebinned : np.ndarray
    """
    if np.isclose(orig_bin_size_s, target_bin_size_s, rtol=1e-6):
        return binned_data.copy()

    ratio = target_bin_size_s / orig_bin_size_s

    if binned_data.ndim == 1:
        binned_data = binned_data.reshape(-1, 1)
        squeeze = True
    else:
        squeeze = False

    n_orig, n_dims = binned_data.shape

    int_ratio = int(round(ratio))
    if int_ratio < 1:
        int_ratio = 1

    if abs(ratio - int_ratio) < 1e-6 and int_ratio >= 1:
        # Exact integer ratio: sum consecutive bins
        n_new = n_orig // int_ratio
        trimmed = binned_data[: n_new * int_ratio, :]
        rebinned = trimmed.reshape(n_new, int_ratio, n_dims).sum(axis=1)
    else:
        # Non-integer ratio: use interpolation
        logger.warning(
            "Non-integer bin ratio (%.4f); using interpolation instead of summation.",
            ratio,
        )
        orig_centers = np.arange(n_orig) * orig_bin_size_s + orig_bin_size_s / 2.0
        total_time = n_orig * orig_bin_size_s
        n_new = int(total_time / target_bin_size_s)
        new_centers = np.arange(n_new) * target_bin_size_s + target_bin_size_s / 2.0
        rebinned = np.zeros((n_new, n_dims), dtype=np.float64)
        for d in range(n_dims):
            f = interp1d(
                orig_centers, binned_data[:, d],
                kind="linear", fill_value="extrapolate",
            )
            rebinned[:, d] = f(new_centers) * ratio  # scale counts

    if squeeze:
        rebinned = rebinned.squeeze(axis=1)

    return rebinned


# ===================================================================
# Behavior Unification
# ===================================================================


def compute_kinematics(
    data: np.ndarray,
    data_type: str,
    bin_size_s: float,
    smooth_sigma: float = 2.0,
) -> Dict[str, np.ndarray]:
    """Compute position, velocity, and acceleration from any single kinematic.

    Parameters
    ----------
    data : np.ndarray, shape (T, D)
        Input kinematic data.
    data_type : str
        One of 'position', 'velocity', 'acceleration'.
    bin_size_s : float
        Bin width in seconds for derivative / integral computation.
    smooth_sigma : float
        Gaussian smoothing sigma (in bins) applied before differentiation.

    Returns
    -------
    dict with keys 'position', 'velocity', 'acceleration', each (T, D).
    """
    if data.ndim == 1:
        data = data.reshape(-1, 1)

    # Make a copy to avoid modifying caller's data
    data = data.copy()

    # Apply smoothing to reduce differentiation noise
    if smooth_sigma > 0:
        for d in range(data.shape[1]):
            data[:, d] = gaussian_filter1d(data[:, d], sigma=smooth_sigma)

    result: Dict[str, np.ndarray] = {}

    if data_type == "position":
        position = data
        velocity = np.gradient(position, bin_size_s, axis=0)
        acceleration = np.gradient(velocity, bin_size_s, axis=0)
    elif data_type == "velocity":
        velocity = data
        position = np.cumsum(velocity, axis=0) * bin_size_s
        acceleration = np.gradient(velocity, bin_size_s, axis=0)
    elif data_type == "acceleration":
        acceleration = data
        velocity = np.cumsum(acceleration, axis=0) * bin_size_s
        position = np.cumsum(velocity, axis=0) * bin_size_s
    else:
        raise ValueError(f"Unknown data_type: {data_type}")

    result["position"] = position.astype(np.float64)
    result["velocity"] = velocity.astype(np.float64)
    result["acceleration"] = acceleration.astype(np.float64)
    return result


def unify_behavior(
    raw_behavior: Dict[str, Any],
    source_type: str,
    bin_size_s: float,
) -> Dict[str, np.ndarray]:
    """Route behavior data through compute_kinematics based on source type.

    Parameters
    ----------
    raw_behavior : dict
        Keys depend on source_type.  For XDS: cursor_vel, cursor_pos, emg.
        For NWB: named timeseries.  For PyalData: vel, pos, hand_pos, etc.
    source_type : str
    bin_size_s : float

    Returns
    -------
    dict with 'position', 'velocity', 'acceleration', and optionally 'emg'.
    """
    result: Dict[str, np.ndarray] = {}

    if source_type == "xds":
        # Prefer velocity if available, fall back to position
        if "cursor_vel" in raw_behavior and raw_behavior["cursor_vel"] is not None:
            kinematics = compute_kinematics(
                raw_behavior["cursor_vel"], "velocity", bin_size_s
            )
            result.update(kinematics)
        elif "cursor_pos" in raw_behavior and raw_behavior["cursor_pos"] is not None:
            kinematics = compute_kinematics(
                raw_behavior["cursor_pos"], "position", bin_size_s
            )
            result.update(kinematics)
        if "emg" in raw_behavior and raw_behavior["emg"] is not None:
            result["emg"] = raw_behavior["emg"].astype(np.float64)

    elif source_type.startswith("nwb"):
        # NWB behavior dict: {name: ndarray}
        # Try common names
        pos_keys = ["hand_pos", "cursor_pos", "Position", "position", "hand_position"]
        vel_keys = ["hand_vel", "cursor_vel", "Velocity", "velocity", "hand_velocity"]
        found = False
        for vk in vel_keys:
            if vk in raw_behavior and raw_behavior[vk] is not None:
                kinematics = compute_kinematics(
                    raw_behavior[vk], "velocity", bin_size_s
                )
                result.update(kinematics)
                found = True
                break
        if not found:
            for pk in pos_keys:
                if pk in raw_behavior and raw_behavior[pk] is not None:
                    kinematics = compute_kinematics(
                        raw_behavior[pk], "position", bin_size_s
                    )
                    result.update(kinematics)
                    found = True
                    break
        if not found:
            # Use whatever is available
            for key, val in raw_behavior.items():
                if isinstance(val, np.ndarray) and val.ndim >= 1:
                    kinematics = compute_kinematics(val, "position", bin_size_s)
                    result.update(kinematics)
                    break

    elif source_type == "pyaldata":
        # Look for vel / pos / hand_pos
        for vk in ("vel", "hand_vel", "cursor_vel"):
            if vk in raw_behavior and raw_behavior[vk] is not None:
                kinematics = compute_kinematics(
                    raw_behavior[vk], "velocity", bin_size_s
                )
                result.update(kinematics)
                return result
        for pk in ("pos", "hand_pos", "cursor_pos"):
            if pk in raw_behavior and raw_behavior[pk] is not None:
                kinematics = compute_kinematics(
                    raw_behavior[pk], "position", bin_size_s
                )
                result.update(kinematics)
                return result

    return result


# ===================================================================
# Quality Check
# ===================================================================


def quality_check_trial(
    trial_data: Dict[str, Any],
    bin_size_s: float,
    max_fr_hz: float = 300.0,
    min_duration_s: float = 0.1,
    min_total_spikes: int = 5,
) -> int:
    """Run quality checks on a single processed trial and return a bitmask of flags.

    Parameters
    ----------
    trial_data : dict
        Must have keys: 'spikes' (N_bins, N_units), 'timestamps' (N_bins,),
        and optionally 'behavior' dict.
    bin_size_s : float
    max_fr_hz : float
        Maximum acceptable mean firing rate per unit.
    min_duration_s : float
    min_total_spikes : int

    Returns
    -------
    int : bitmask of QC_FLAG_* constants.  0 means all checks passed.
    """
    flags = 0
    spikes = trial_data.get("spikes")
    timestamps = trial_data.get("timestamps")
    behavior = trial_data.get("behavior", {})

    if spikes is None or timestamps is None:
        return flags

    n_bins, n_units = spikes.shape

    # Check empty units
    unit_counts = spikes.sum(axis=0)
    if np.any(unit_counts == 0):
        flags |= QC_FLAG_EMPTY_UNITS

    # Check high firing rate
    duration = n_bins * bin_size_s
    if duration > 0:
        mean_fr = unit_counts / duration
        if np.any(mean_fr > max_fr_hz):
            flags |= QC_FLAG_HIGH_FR

    # Check NaN in behavior
    for key, val in behavior.items():
        if isinstance(val, np.ndarray) and np.any(np.isnan(val)):
            flags |= QC_FLAG_NAN_BEHAVIOR
            break

    # Check short trial
    if duration < min_duration_s:
        flags |= QC_FLAG_SHORT_TRIAL

    # Check low spike count
    if unit_counts.sum() < min_total_spikes:
        flags |= QC_FLAG_LOW_SPIKE_COUNT

    # Check constant behavior
    for key, val in behavior.items():
        if isinstance(val, np.ndarray) and val.size > 1:
            if np.all(np.var(val, axis=0) < 1e-12):
                flags |= QC_FLAG_CONSTANT_BEHAVIOR
                break

    return flags


def describe_qc_flags(flags: int) -> List[str]:
    """Convert a bitmask to a list of human-readable flag descriptions."""
    descriptions = []
    if flags & QC_FLAG_EMPTY_UNITS:
        descriptions.append("EMPTY_UNITS")
    if flags & QC_FLAG_HIGH_FR:
        descriptions.append("HIGH_FR")
    if flags & QC_FLAG_NAN_BEHAVIOR:
        descriptions.append("NAN_BEHAVIOR")
    if flags & QC_FLAG_SHORT_TRIAL:
        descriptions.append("SHORT_TRIAL")
    if flags & QC_FLAG_LOW_SPIKE_COUNT:
        descriptions.append("LOW_SPIKE_COUNT")
    if flags & QC_FLAG_CONSTANT_BEHAVIOR:
        descriptions.append("CONSTANT_BEHAVIOR")
    return descriptions


# ===================================================================
# HDF5 Output
# ===================================================================


def write_standardized_hdf5(
    output_path: str,
    all_datasets: Dict[str, Dict[str, List[Dict[str, Any]]]],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Write standardized data to HDF5.

    Structure:
      /<dataset_name>/<session_name>/trial_NNN/
        timestamps   (N_bins,)           float64
        spikes       (N_bins, N_units)   int32
        behavior/
          position      (N_bins, D)      float64
          velocity      (N_bins, D)      float64
          acceleration  (N_bins, D)      float64
          [emg]         (N_bins, N_mus)  float64   (optional)

    Parameters
    ----------
    output_path : str
    all_datasets : nested dict  {dataset_name: {session_name: [trial_dict, ...]}}
        Each trial_dict has 'timestamps', 'spikes', 'behavior' sub-dict,
        and optionally 'qc_flags'.
    metadata : optional dict
        Global metadata to store as HDF5 root attributes.
    """
    logger.info("Writing HDF5 to: %s", output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with h5py.File(output_path, "w") as f:
        # Global metadata
        if metadata:
            for k, v in metadata.items():
                try:
                    f.attrs[k] = v
                except TypeError:
                    f.attrs[k] = str(v)

        for ds_name, sessions in all_datasets.items():
            ds_grp = f.create_group(ds_name)
            for sess_name, trials in sessions.items():
                sess_grp = ds_grp.create_group(sess_name)
                sess_grp.attrs["n_trials"] = len(trials)

                for tidx, trial in enumerate(trials):
                    trial_grp = sess_grp.create_group(f"trial_{tidx:04d}")

                    # Timestamps
                    ts = trial.get("timestamps")
                    if ts is not None:
                        trial_grp.create_dataset(
                            "timestamps", data=ts.astype(np.float64),
                            compression="gzip", compression_opts=4,
                        )
                        trial_grp.attrs["duration_s"] = float(ts[-1] - ts[0]) if len(ts) > 1 else 0.0
                        trial_grp.attrs["n_bins"] = len(ts)

                    # Spikes
                    sp = trial.get("spikes")
                    if sp is not None:
                        trial_grp.create_dataset(
                            "spikes", data=sp.astype(np.int32),
                            compression="gzip", compression_opts=4,
                        )
                        trial_grp.attrs["n_units"] = sp.shape[1] if sp.ndim == 2 else 0

                    # Behavior
                    beh = trial.get("behavior", {})
                    if beh:
                        beh_grp = trial_grp.create_group("behavior")
                        for beh_key, beh_val in beh.items():
                            if isinstance(beh_val, np.ndarray):
                                beh_grp.create_dataset(
                                    beh_key, data=beh_val.astype(np.float64),
                                    compression="gzip", compression_opts=4,
                                )
                                beh_grp[beh_key].attrs["shape"] = list(beh_val.shape)

                    # Quality check flags
                    qc = trial.get("qc_flags", 0)
                    trial_grp.attrs["qc_flags"] = int(qc)
                    if qc != 0:
                        trial_grp.attrs["qc_issues"] = ",".join(describe_qc_flags(qc))

    logger.info("HDF5 written successfully: %s", output_path)


def verify_hdf5(filepath: str) -> bool:
    """Read back the HDF5 file and validate shapes / structure.

    Returns True if verification passes.
    """
    logger.info("Verifying HDF5: %s", filepath)
    ok = True
    with h5py.File(filepath, "r") as f:
        logger.info("Root attrs: %s", dict(f.attrs))

        def _visit(name: str, obj: Any) -> None:
            nonlocal ok
            if isinstance(obj, h5py.Dataset):
                logger.info("  %s  shape=%s  dtype=%s", name, obj.shape, obj.dtype)
                data = obj[:]
                if np.any(np.isnan(data)) and "behavior" in name:
                    logger.warning("  NaN values found in %s", name)
            elif isinstance(obj, h5py.Group):
                attrs_str = {k: v for k, v in obj.attrs.items()}
                if attrs_str:
                    logger.info("  %s  attrs=%s", name, attrs_str)

        f.visititems(_visit)

    logger.info("Verification %s", "PASSED" if ok else "FAILED")
    return ok


# ===================================================================
# Full Pipeline
# ===================================================================


def _process_xds_session(
    filepath: str,
    session_name: str,
    bin_size_s: float,
    source_type: str = "xds",
    run_qc: bool = True,
) -> List[Dict[str, Any]]:
    """Process one XDS session into a list of standardized trial dicts."""
    xds = load_xds_mat(filepath)
    trial_info = xds["trial_info_table"]

    if not trial_info.empty:
        trial_info = filter_successful_trials(trial_info, source_type)
    else:
        logger.warning("No trial_info_table; processing as single continuous segment.")

    time_frame = xds["time_frame"]
    spike_times = xds["spike_times"]

    # Build behavior dict for unification
    raw_behavior: Dict[str, Any] = {}
    for key in ("cursor_vel", "cursor_pos", "emg"):
        if xds.get(key) is not None:
            raw_behavior[key] = xds[key]

    processed_trials: List[Dict[str, Any]] = []

    if trial_info.empty:
        # Single segment
        if time_frame is not None:
            t_start, t_end = float(time_frame[0]), float(time_frame[-1])
        else:
            all_st = np.concatenate([st for st in spike_times if st.size > 0])
            t_start, t_end = float(all_st.min()), float(all_st.max())

        bin_edges, bin_centers = create_uniform_bins(t_start, t_end, bin_size_s)
        spikes = bin_spike_times(spike_times, bin_edges)

        # Resample behavior
        beh_resampled: Dict[str, np.ndarray] = {}
        for key in ("cursor_vel", "cursor_pos", "emg"):
            if key in raw_behavior and time_frame is not None:
                beh_resampled[key] = resample_behavior(
                    raw_behavior[key], time_frame, bin_centers
                )

        behavior = unify_behavior(beh_resampled, source_type, bin_size_s)

        trial_dict = {
            "timestamps": bin_centers,
            "spikes": spikes,
            "behavior": behavior,
        }
        if run_qc:
            trial_dict["qc_flags"] = quality_check_trial(trial_dict, bin_size_s)
        processed_trials.append(trial_dict)
    else:
        # Per-trial processing
        start_col, end_col = None, None
        for s in ("start_time", "startTime", "trial_start", "t_start"):
            if s in trial_info.columns:
                start_col = s
                break
        for e in ("end_time", "endTime", "trial_end", "t_end"):
            if e in trial_info.columns:
                end_col = e
                break

        if start_col is None or end_col is None:
            logger.error("Cannot find start/end time columns in trial_info.")
            return processed_trials

        for _, row in trial_info.iterrows():
            t_start = float(row[start_col])
            t_end = float(row[end_col])

            bin_edges, bin_centers = create_uniform_bins(t_start, t_end, bin_size_s)
            if len(bin_centers) < 2:
                continue

            spikes = bin_spike_times(spike_times, bin_edges)

            beh_resampled = {}
            for key in ("cursor_vel", "cursor_pos", "emg"):
                if key in raw_behavior and time_frame is not None:
                    # Slice behavior to trial window (with some margin)
                    mask = (time_frame >= t_start - bin_size_s) & (
                        time_frame <= t_end + bin_size_s
                    )
                    if mask.sum() > 1:
                        beh_resampled[key] = resample_behavior(
                            raw_behavior[key][mask] if raw_behavior[key].ndim == 1
                            else raw_behavior[key][mask, :],
                            time_frame[mask],
                            bin_centers,
                        )

            behavior = unify_behavior(beh_resampled, source_type, bin_size_s)

            trial_dict = {
                "timestamps": bin_centers,
                "spikes": spikes,
                "behavior": behavior,
            }
            if run_qc:
                trial_dict["qc_flags"] = quality_check_trial(trial_dict, bin_size_s)
            processed_trials.append(trial_dict)

    logger.info("XDS session '%s': %d trials processed.", session_name, len(processed_trials))
    return processed_trials


def _process_nwb_session(
    filepath: str,
    session_name: str,
    bin_size_s: float,
    source_type: str = "nwb_000121",
    run_qc: bool = True,
) -> List[Dict[str, Any]]:
    """Process one NWB session into standardized trial dicts."""
    nwb = load_nwb_data(filepath)
    trials_df = nwb["trials"]
    spike_times = nwb["spike_times"]
    behavior_raw = nwb["behavior"]  # {name: (data, timestamps)}

    if not trials_df.empty:
        trials_df = filter_successful_trials(trials_df, source_type)

    processed_trials: List[Dict[str, Any]] = []

    if trials_df.empty or ("start_time" not in trials_df.columns):
        # Process as single segment
        all_st = np.concatenate([st for st in spike_times if st.size > 0])
        t_start, t_end = float(all_st.min()), float(all_st.max())

        bin_edges, bin_centers = create_uniform_bins(t_start, t_end, bin_size_s)
        spikes = bin_spike_times(spike_times, bin_edges)

        beh_resampled: Dict[str, Any] = {}
        for bname, (bdata, bts) in behavior_raw.items():
            beh_resampled[bname] = resample_behavior(bdata, bts, bin_centers)

        behavior = unify_behavior(beh_resampled, source_type, bin_size_s)
        trial_dict = {
            "timestamps": bin_centers,
            "spikes": spikes,
            "behavior": behavior,
        }
        if run_qc:
            trial_dict["qc_flags"] = quality_check_trial(trial_dict, bin_size_s)
        processed_trials.append(trial_dict)
    else:
        stop_col = "stop_time" if "stop_time" in trials_df.columns else "end_time"
        for _, row in trials_df.iterrows():
            t_start = float(row["start_time"])
            t_end = float(row.get(stop_col, row["start_time"] + 5.0))

            bin_edges, bin_centers = create_uniform_bins(t_start, t_end, bin_size_s)
            if len(bin_centers) < 2:
                continue

            spikes = bin_spike_times(spike_times, bin_edges)

            beh_resampled = {}
            for bname, (bdata, bts) in behavior_raw.items():
                mask = (bts >= t_start - bin_size_s) & (bts <= t_end + bin_size_s)
                if mask.sum() > 1:
                    beh_resampled[bname] = resample_behavior(
                        bdata[mask] if bdata.ndim == 1 else bdata[mask, :],
                        bts[mask],
                        bin_centers,
                    )

            behavior = unify_behavior(beh_resampled, source_type, bin_size_s)
            trial_dict = {
                "timestamps": bin_centers,
                "spikes": spikes,
                "behavior": behavior,
            }
            if run_qc:
                trial_dict["qc_flags"] = quality_check_trial(trial_dict, bin_size_s)
            processed_trials.append(trial_dict)

    # Close NWB io
    try:
        nwb["_nwb_io"].close()
    except Exception:
        pass

    logger.info("NWB session '%s': %d trials processed.", session_name, len(processed_trials))
    return processed_trials


def _process_pyaldata_session(
    filepath: str,
    session_name: str,
    bin_size_s: float,
    source_type: str = "pyaldata",
    run_qc: bool = True,
) -> List[Dict[str, Any]]:
    """Process one PyalData session into standardized trial dicts."""
    pyaldata = load_pyaldata(filepath, bin_size_s=None)
    orig_bin_size = pyaldata["bin_size_s"]
    raw_trials = pyaldata["trials"]

    # Build a DataFrame from trial metadata for filtering
    meta_fields = []
    if raw_trials:
        for k, v in raw_trials[0].items():
            if not isinstance(v, np.ndarray) or (isinstance(v, np.ndarray) and v.ndim == 0):
                meta_fields.append(k)

    trial_meta = pd.DataFrame([{k: t.get(k) for k in meta_fields} for t in raw_trials])
    trial_meta = filter_successful_trials(trial_meta, source_type)
    keep_indices = set(trial_meta.index)

    processed_trials: List[Dict[str, Any]] = []
    for tidx, trial in enumerate(raw_trials):
        if tidx not in keep_indices:
            continue

        merged_spikes = trial.get("_merged_spikes")
        if merged_spikes is None:
            continue

        # Resample spikes if bin sizes differ
        if not np.isclose(orig_bin_size, bin_size_s, rtol=1e-6):
            merged_spikes = resample_already_binned(merged_spikes, orig_bin_size, bin_size_s)

        n_bins = merged_spikes.shape[0]
        # Create timestamps (relative to trial start)
        t_offset = 0.0
        for t_field in ("t_start", "start_time", "trial_start"):
            if t_field in trial and not isinstance(trial[t_field], np.ndarray):
                t_offset = float(trial[t_field])
                break

        timestamps = t_offset + np.arange(n_bins) * bin_size_s + bin_size_s / 2.0

        # Behavior
        raw_beh: Dict[str, Any] = {}
        for beh_key in ("vel", "pos", "hand_vel", "hand_pos", "cursor_vel", "cursor_pos"):
            if beh_key in trial and isinstance(trial[beh_key], np.ndarray) and trial[beh_key].ndim >= 1:
                beh_data = trial[beh_key]
                if not np.isclose(orig_bin_size, bin_size_s, rtol=1e-6):
                    beh_data = resample_already_binned(beh_data, orig_bin_size, bin_size_s)
                raw_beh[beh_key] = beh_data

        behavior = unify_behavior(raw_beh, source_type, bin_size_s)

        trial_dict = {
            "timestamps": timestamps,
            "spikes": merged_spikes.astype(np.int32) if merged_spikes.dtype != np.int32 else merged_spikes,
            "behavior": behavior,
        }
        if run_qc:
            trial_dict["qc_flags"] = quality_check_trial(trial_dict, bin_size_s)
        processed_trials.append(trial_dict)

    logger.info("PyalData session '%s': %d trials processed.", session_name, len(processed_trials))
    return processed_trials


def run_full_pipeline(config: Dict[str, Any]) -> str:
    """Orchestrate the full pipeline: load -> filter -> bin -> resample -> unify -> QC -> write.

    Parameters
    ----------
    config : dict
        Expected keys:
          - datasets: list of dicts, each with:
              - name: str (dataset identifier)
              - sessions: list of dicts, each with:
                  - name: str (session identifier)
                  - filepath: str (path to data file)
                  - format: str ('xds', 'nwb', 'pyaldata')
                  - source_type: str (optional, for trial filtering)
          - bin_size_s: float (optional, default 0.02)
          - output_path: str
          - quality_check: bool (optional, default True)

    Returns
    -------
    str : path to the output HDF5 file.
    """
    bin_size_s = config.get("bin_size_s", DEFAULT_BIN_SIZE_S)
    output_path = config["output_path"]
    run_qc = config.get("quality_check", True)

    all_datasets: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for ds_cfg in config["datasets"]:
        ds_name = ds_cfg["name"]
        all_datasets[ds_name] = {}

        for sess_cfg in ds_cfg["sessions"]:
            sess_name = sess_cfg["name"]
            filepath = sess_cfg["filepath"]
            fmt = sess_cfg["format"].lower()
            source_type = sess_cfg.get("source_type", fmt)

            logger.info(
                "Processing dataset='%s' session='%s' format='%s' source='%s'",
                ds_name, sess_name, fmt, source_type,
            )

            try:
                if fmt == "xds":
                    trials = _process_xds_session(
                        filepath, sess_name, bin_size_s, source_type, run_qc
                    )
                elif fmt == "nwb":
                    trials = _process_nwb_session(
                        filepath, sess_name, bin_size_s, source_type, run_qc
                    )
                elif fmt == "pyaldata":
                    trials = _process_pyaldata_session(
                        filepath, sess_name, bin_size_s, source_type, run_qc
                    )
                else:
                    logger.error("Unknown format '%s'; skipping session '%s'.", fmt, sess_name)
                    continue
            except Exception as exc:
                logger.error(
                    "Failed to process session '%s': %s", sess_name, exc, exc_info=True
                )
                continue

            all_datasets[ds_name][sess_name] = trials

    # Gather metadata
    metadata = {
        "bin_size_s": bin_size_s,
        "created_by": "spike_behavior_organize",
        "config": json.dumps(config, default=str),
    }

    write_standardized_hdf5(output_path, all_datasets, metadata=metadata)
    verify_hdf5(output_path)

    # Summary
    total_trials = sum(
        len(trials)
        for sessions in all_datasets.values()
        for trials in sessions.values()
    )
    logger.info(
        "Pipeline complete. %d total trials written to %s", total_trials, output_path
    )
    return output_path


# ===================================================================
# CLI
# ===================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Standardize multi-format neural spike and behavior data into unified HDF5.",
    )
    parser.add_argument(
        "config_file",
        type=str,
        help="Path to JSON config file describing datasets, sessions, and formats.",
    )
    parser.add_argument(
        "--bin-size",
        type=float,
        default=None,
        help=f"Bin size in seconds (overrides config; default {DEFAULT_BIN_SIZE_S}).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output HDF5 path (overrides config).",
    )
    parser.add_argument(
        "--no-quality-check",
        action="store_true",
        help="Skip quality-check step.",
    )

    args = parser.parse_args()

    # Load config
    config_path = Path(args.config_file)
    if not config_path.exists():
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)

    with open(config_path, "r") as f:
        config = json.load(f)

    # CLI overrides
    if args.bin_size is not None:
        config["bin_size_s"] = args.bin_size
    if args.output is not None:
        config["output_path"] = args.output
    if args.no_quality_check:
        config["quality_check"] = False

    # Validate
    if "output_path" not in config:
        logger.error("No output_path specified in config or via --output.")
        sys.exit(1)
    if "datasets" not in config:
        logger.error("No 'datasets' key in config file.")
        sys.exit(1)

    run_full_pipeline(config)


if __name__ == "__main__":
    main()
