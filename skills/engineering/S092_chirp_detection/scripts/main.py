#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import json
import argparse
import logging
from scipy import ndimage
from sklearn.linear_model import LinearRegression
import os

def load_spectrogram(filepath):
    """Load spectrogram with robust error handling."""
    try:
        # First try loading without pickle
        data = np.load(filepath)
    except ValueError as e:
        if "allow_pickle" in str(e):
            # Try with pickle enabled
            logging.info("Attempting to load with pickle=True")
            data = np.load(filepath, allow_pickle=True)
        else:
            raise e
    
    # Handle different data formats
    if isinstance(data, np.ndarray):
        spectrogram = data
    elif hasattr(data, 'item'):  # Scalar array containing object
        spectrogram = data.item()
    else:
        raise ValueError(f"Unexpected data type: {type(data)}")
    
    # Ensure it's a 2D numeric array
    spectrogram = np.asarray(spectrogram, dtype=np.float64)
    
    if spectrogram.ndim != 2:
        raise ValueError(f"Expected 2D spectrogram, got {spectrogram.ndim}D array")
    
    return spectrogram

def detect_chirps(spectrogram, threshold=0.5, window_size=10):
    """
    Detect chirp signals in a spectrogram using sliding window approach.
    
    Args:
        spectrogram: 2D numpy array (frequency x time)
        threshold: minimum confidence threshold
        window_size: size of sliding window in time bins
    
    Returns:
        list of detected chirps with metadata
    """
    freq_bins, time_bins = spectrogram.shape
    chirps = []
    
    # Handle NaN values - replace with minimum finite value
    spec_clean = spectrogram.copy()
    nan_mask = ~np.isfinite(spec_clean)
    if np.any(nan_mask):
        finite_values = spec_clean[np.isfinite(spec_clean)]
        if len(finite_values) > 0:
            fill_value = np.min(finite_values)
        else:
            fill_value = 0.0
        spec_clean[nan_mask] = fill_value
        logging.info(f"Replaced {np.sum(nan_mask)} NaN/inf values with {fill_value}")
    
    # Keep original values for signal strength calculation
    spec_orig = spec_clean.copy()
    
    # Normalize spectrogram with robust statistics for peak finding
    spec_mean = np.mean(spec_clean)
    spec_std = np.std(spec_clean)
    
    if spec_std == 0 or not np.isfinite(spec_std):
        logging.warning("Zero or invalid standard deviation, using raw values")
        spec_norm = spec_clean
    else:
        spec_norm = (spec_clean - spec_mean) / spec_std
    
    logging.info(f"Processing {time_bins // (window_size // 2)} windows...")
    candidates_found = 0
    
    # Slide window across time dimension
    for t_start in range(0, time_bins - window_size, window_size // 2):
        t_end = min(t_start + window_size, time_bins)
        window_norm = spec_norm[:, t_start:t_end]
        window_orig = spec_orig[:, t_start:t_end]
        
        # Skip windows with insufficient valid data
        if np.sum(np.isfinite(window_norm)) < window_norm.size * 0.5:
            continue
            
        # Find peak frequency at each time step in window
        peak_freqs = np.argmax(window_norm, axis=0)
        time_indices = np.arange(len(peak_freqs))
        
        # Fit linear regression to frequency trajectory
        if len(peak_freqs) > 3:  # Need minimum points for regression
            # Ensure all values are finite
            valid_mask = np.isfinite(peak_freqs)
            if np.sum(valid_mask) < 3:
                continue
                
            valid_times = time_indices[valid_mask]
            valid_freqs = peak_freqs[valid_mask]
            
            lr = LinearRegression()
            lr.fit(valid_times.reshape(-1, 1), valid_freqs)
            
            # Calculate R-squared
            r_squared = lr.score(valid_times.reshape(-1, 1), valid_freqs)
            
            # Calculate signal strength using original (non-normalized) values
            # Get the actual peak values at each time step
            peak_values = []
            for t_idx, f_idx in enumerate(peak_freqs):
                if t_idx < window_orig.shape[1] and f_idx < window_orig.shape[0]:
                    peak_values.append(window_orig[f_idx, t_idx])
            
            if len(peak_values) > 0:
                signal_strength = np.mean(peak_values)
                # For dB data, calculate SNR-like metric
                window_background = np.percentile(window_orig, 25)  # Use 25th percentile as background
                snr_db = signal_strength - window_background
                
                # Convert to linear scale for weighting (assuming dB values)
                # Clamp to reasonable range to avoid overflow
                snr_db = np.clip(snr_db, 0, 30)  # 0 to 30 dB range
                signal_weight = snr_db / 30.0  # Normalize to 0-1 range
            else:
                signal_weight = 0.0
                snr_db = 0.0
            
            # Confidence combines linearity (R²) with signal quality
            # Both components are now in 0-1 range
            confidence = r_squared * signal_weight
            
            candidates_found += 1
            
            # Debug output for first few candidates
            if candidates_found <= 3:
                logging.info(f"Candidate {candidates_found}: R²={r_squared:.3f}, "
                           f"SNR={snr_db:.1f}dB, signal_weight={signal_weight:.3f}, confidence={confidence:.3f}")
            
            if confidence > threshold and np.isfinite(confidence):
                start_freq = lr.predict([[0]])[0]
                end_freq = lr.predict([[len(peak_freqs)-1]])[0]
                
                chirps.append({
                    'start_time': t_start,
                    'end_time': t_end - 1,
                    'start_frequency': int(start_freq),
                    'end_frequency': int(end_freq),
                    'confidence': float(confidence)
                })
    
    logging.info(f"Evaluated {candidates_found} candidates, found {len(chirps)} chirps above threshold")
    return chirps

def visualize_detections(spectrogram, chirps, output_path):
    """Create visualization of spectrogram with detected chirps overlaid."""
    plt.figure(figsize=(12, 8))
    
    # Handle NaN values for visualization
    spec_vis = spectrogram.copy()
    if np.any(~np.isfinite(spec_vis)):
        finite_values = spec_vis[np.isfinite(spec_vis)]
        if len(finite_values) > 0:
            spec_vis[~np.isfinite(spec_vis)] = np.min(finite_values)
    
    plt.imshow(spec_vis, aspect='auto', origin='lower', cmap='viridis')
    plt.colorbar(label='Power (dB)')
    plt.xlabel('Time bins')
    plt.ylabel('Frequency bins')
    plt.title('Spectrogram with Detected Chirps')
    
    # Overlay detected chirps as rectangles
    for i, chirp in enumerate(chirps):
        rect = plt.Rectangle(
            (chirp['start_time'], min(chirp['start_frequency'], chirp['end_frequency'])),
            chirp['end_time'] - chirp['start_time'],
            abs(chirp['end_frequency'] - chirp['start_frequency']),
            linewidth=2, edgecolor='red', facecolor='none', alpha=0.8
        )
        plt.gca().add_patch(rect)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Detect chirp signals in spectrograms')
    parser.add_argument('--input', required=True, help='Input .npy spectrogram file')
    parser.add_argument('--output', required=True, help='Output JSON file for results')
    parser.add_argument('--threshold', type=float, default=0.5, 
                       help='Detection confidence threshold (default: 0.5)')
    parser.add_argument('--window-size', type=int, default=10,
                       help='Sliding window size in time bins (default: 10)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load spectrogram
    logger.info(f"Loading spectrogram from {args.input}")
    spectrogram = load_spectrogram(args.input)
    logger.info(f"Spectrogram shape: {spectrogram.shape}")
    logger.info(f"Data range: {np.min(spectrogram):.3f} to {np.max(spectrogram):.3f}")
    
    # Detect chirps
    logger.info("Detecting chirp signals...")
    chirps = detect_chirps(spectrogram, threshold=args.threshold, window_size=args.window_size)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(chirps, f, indent=2)
    
    # Generate visualization
    output_stem = os.path.splitext(args.output)[0]
    viz_path = f"{output_stem}_detected.png"
    visualize_detections(spectrogram, chirps, viz_path)
    
    # Print statistics
    if chirps:
        avg_confidence = np.mean([c['confidence'] for c in chirps])
        print(f"Total chirps detected: {len(chirps)}")
        print(f"Average confidence score: {avg_confidence:.3f}")
    else:
        print("No chirps detected above threshold")

if __name__ == "__main__":
    main()
