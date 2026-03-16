#!/usr/bin/env python3
"""
Ocean Wave Frequency Spectrum Analysis Tool
Processes synthetic ocean buoy data to compute wave frequency spectra
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
from scipy.interpolate import interp1d


def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def detect_columns(df):
    """Automatically detect time and elevation columns"""
    columns = df.columns.str.lower()
    
    # Common time column names
    time_candidates = ['time', 'timestamp', 'datetime', 'date_time', 'date', 't']
    time_col = None
    for candidate in time_candidates:
        matches = [col for col in df.columns if candidate in col.lower()]
        if matches:
            time_col = matches[0]
            break
    
    # Common elevation column names
    elevation_candidates = ['elevation', 'sea_level', 'sealevel', 'height', 'wave_height', 
                          'surface_elevation', 'eta', 'z', 'elev', 'level']
    elevation_col = None
    for candidate in elevation_candidates:
        matches = [col for col in df.columns if candidate in col.lower()]
        if matches:
            elevation_col = matches[0]
            break
    
    if time_col is None:
        raise ValueError(f"Could not identify time column. Available columns: {list(df.columns)}")
    if elevation_col is None:
        raise ValueError(f"Could not identify elevation column. Available columns: {list(df.columns)}")
    
    logging.info(f"Detected time column: '{time_col}', elevation column: '{elevation_col}'")
    return time_col, elevation_col


def load_buoy_data(filepath):
    """Load buoy data from CSV file"""
    logging.info(f"Loading buoy data from {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        
        # Auto-detect column names
        time_col, elevation_col = detect_columns(df)
        
        # Standardize column names
        df = df.rename(columns={time_col: 'timestamp', elevation_col: 'elevation'})
        
        # Convert timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        logging.info(f"Loaded {len(df)} data points")
        return df
        
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        sys.exit(1)


def quality_control(df):
    """Perform quality control checks on the data"""
    logging.info("Performing quality control checks")
    
    # Check for unrealistic elevation values (> 20m)
    unrealistic_mask = np.abs(df['elevation']) > 20.0
    if unrealistic_mask.any():
        logging.warning(f"Found {unrealistic_mask.sum()} unrealistic elevation values")
        df.loc[unrealistic_mask, 'elevation'] = np.nan
    
    # Check for data gaps
    time_diff = df['timestamp'].diff()
    median_dt = time_diff.median()
    large_gaps = time_diff > 10 * median_dt
    
    if large_gaps.any():
        total_gap_time = (time_diff[large_gaps] - median_dt).sum()
        record_length = df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]
        gap_percentage = total_gap_time / record_length * 100
        
        if gap_percentage > 10:
            logging.warning(f"Data gaps exceed 10% of record ({gap_percentage:.1f}%)")
    
    return df


def preprocess_data(df):
    """Preprocess the elevation data"""
    logging.info("Preprocessing elevation data")
    
    # Remove mean (detrend)
    elevation = df['elevation'].values
    elevation_clean = elevation[~np.isnan(elevation)]
    
    if len(elevation_clean) < len(elevation) * 0.8:
        logging.error("Too many missing values in elevation data")
        sys.exit(1)
    
    # Linear detrending
    elevation_detrended = signal.detrend(elevation_clean)
    
    # Calculate sampling frequency
    time_diff = df['timestamp'].diff().dropna()
    dt = time_diff.median().total_seconds()
    fs = 1.0 / dt
    
    logging.info(f"Sampling frequency: {fs:.3f} Hz")
    logging.info(f"Elevation std dev: {np.std(elevation_detrended):.3f} m")
    
    return elevation_detrended, fs


def compute_spectrum(elevation, fs):
    """Compute power spectral density using Welch's method"""
    logging.info("Computing power spectral density")
    
    # Use Welch's method with Hanning window
    nperseg = min(len(elevation) // 4, 1024)  # Window length
    
    frequencies, psd = signal.welch(
        elevation,
        fs=fs,
        window='hann',
        nperseg=nperseg,
        noverlap=nperseg//2,
        scaling='density'
    )
    
    logging.info(f"Frequency range: {frequencies[1]:.4f} to {frequencies[-1]:.4f} Hz")
    logging.info(f"PSD range: {np.min(psd):.6f} to {np.max(psd):.6f} m²/Hz")
    
    return frequencies, psd


def calculate_wave_parameters(frequencies, psd):
    """Calculate wave parameters from spectrum"""
    logging.info("Calculating wave parameters")
    
    # Calculate frequency resolution
    df_freq = frequencies[1] - frequencies[0]
    logging.info(f"Frequency resolution: {df_freq:.6f} Hz")
    
    # First calculate total energy from full spectrum for validation
    total_energy = np.trapz(psd, frequencies)
    logging.info(f"Total energy in full spectrum: {total_energy:.6f} m²")
    
    # Filter to wave frequency band (0.05 - 0.5 Hz)
    wave_mask = (frequencies >= 0.05) & (frequencies <= 0.5)
    wave_freq = frequencies[wave_mask]
    wave_psd = psd[wave_mask]
    
    if len(wave_psd) == 0:
        logging.error("No data in wave frequency band")
        return None
    
    # Zeroth moment (variance) - integrate over wave frequencies only
    m0 = np.trapz(wave_psd, wave_freq)
    logging.info(f"Zeroth moment (m0): {m0:.6f} m²")
    
    # Sanity check - wave energy should be less than total energy
    if m0 > total_energy:
        logging.error(f"Wave band energy ({m0:.3f}) exceeds total energy ({total_energy:.3f})")
        return None
    
    # Significant wave height (Hs = 4 * sqrt(m0))
    hs = 4 * np.sqrt(m0)
    
    # Peak frequency
    peak_idx = np.argmax(wave_psd)
    fp = wave_freq[peak_idx]
    
    # Mean frequency
    m1 = np.trapz(wave_freq * wave_psd, wave_freq)
    mean_freq = m1 / m0
    
    # Spectral bandwidth
    m2 = np.trapz(wave_freq**2 * wave_psd, wave_freq)
    bandwidth = np.sqrt(m2/m0 - mean_freq**2) / mean_freq
    
    # Check energy in wave band
    wave_energy_fraction = m0 / total_energy
    
    if wave_energy_fraction < 0.1:
        logging.warning("Low energy in wave frequency band")
    
    parameters = {
        'significant_wave_height_m': float(hs),
        'peak_frequency_hz': float(fp),
        'mean_frequency_hz': float(mean_freq),
        'spectral_bandwidth': float(bandwidth),
        'wave_energy_fraction': float(wave_energy_fraction),
        'total_variance_m2': float(m0)
    }
    
    return parameters


def create_visualization(frequencies, psd, parameters, output_dir):
    """Create publication-quality spectrum plot"""
    logging.info("Creating visualization")
    
    plt.figure(figsize=(10, 6))
    plt.loglog(frequencies, psd, 'b-', linewidth=1.5, label='Power Spectral Density')
    
    # Mark peak frequency
    fp = parameters['peak_frequency_hz']
    fp_idx = np.argmin(np.abs(frequencies - fp))
    plt.loglog(fp, psd[fp_idx], 'ro', markersize=8, label=f'Peak frequency: {fp:.3f} Hz')
    
    # Shade wave frequency band
    wave_mask = (frequencies >= 0.05) & (frequencies <= 0.5)
    plt.fill_between(frequencies[wave_mask], psd[wave_mask], alpha=0.3, color='lightblue', 
                     label='Wave frequency band')
    
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Power Spectral Density (m²/Hz)')
    plt.title('Ocean Wave Frequency Spectrum')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Add text box with parameters
    textstr = f'Hs = {parameters["significant_wave_height_m"]:.2f} m\n'
    textstr += f'fp = {parameters["peak_frequency_hz"]:.3f} Hz\n'
    textstr += f'Mean freq = {parameters["mean_frequency_hz"]:.3f} Hz'
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    
    plot_path = Path(output_dir) / 'wave_spectrum.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Plot saved to {plot_path}")


def save_results(frequencies, psd, parameters, output_dir):
    """Save results in JSON and CSV formats"""
    logging.info("Saving results")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save JSON summary
    json_path = output_path / 'wave_analysis_summary.json'
    with open(json_path, 'w') as f:
        json.dump(parameters, f, indent=2)
    
    # Save CSV spectrum data
    cumulative_energy = np.cumsum(psd * np.gradient(frequencies))
    
    spectrum_df = pd.DataFrame({
        'frequency_hz': frequencies,
        'power_spectral_density_m2_hz': psd,
        'cumulative_energy_m2': cumulative_energy
    })
    
    csv_path = output_path / 'wave_spectrum_data.csv'
    spectrum_df.to_csv(csv_path, index=False)
    
    logging.info(f"Results saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Ocean Wave Frequency Spectrum Analysis')
    parser.add_argument('input_file', help='Input CSV file with buoy data')
    parser.add_argument('-o', '--output', default='output', help='Output directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Load and process data
    df = load_buoy_data(args.input_file)
    df = quality_control(df)
    elevation, fs = preprocess_data(df)
    
    # Compute spectrum
    frequencies, psd = compute_spectrum(elevation, fs)
    
    # Calculate parameters
    parameters = calculate_wave_parameters(frequencies, psd)
    if parameters is None:
        sys.exit(1)
    
    # Create outputs
    create_visualization(frequencies, psd, parameters, args.output)
    save_results(frequencies, psd, parameters, args.output)
    
    logging.info("Analysis complete!")


if __name__ == '__main__':
    main()
