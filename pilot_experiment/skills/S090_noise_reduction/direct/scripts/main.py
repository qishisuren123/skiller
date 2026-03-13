import numpy as np
import argparse
import json
import os

def generate_test_signals(duration=2.0, fs=8000):
    """Generate composite test signal with sine waves and noise"""
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    
    # Clean signal components
    signal_440 = 0.5 * np.sin(2 * np.pi * 440 * t)
    signal_880 = 0.3 * np.sin(2 * np.pi * 880 * t)
    clean_signal = signal_440 + signal_880
    
    # Broadband noise
    noise = 0.4 * np.random.randn(len(t))
    
    # Primary signal (clean + noise)
    primary_signal = clean_signal + noise
    
    # Reference noise (correlated but delayed/scaled)
    delay_samples = 5
    reference_noise = 0.8 * np.roll(noise, delay_samples) + 0.1 * np.random.randn(len(t))
    
    return primary_signal, reference_noise, clean_signal, fs

def lms_adaptive_filter(primary, reference, step_size, filter_length):
    """Implement LMS adaptive noise cancellation algorithm"""
    N = len(primary)
    w = np.zeros(filter_length)  # Filter coefficients
    output = np.zeros(N)
    error_signal = np.zeros(N)
    mse_history = []
    
    for n in range(filter_length, N):
        # Extract input vector (reversed for convolution)
        x = reference[n-filter_length:n][::-1]
        
        # Filter output (noise estimate)
        y = np.dot(w, x)
        
        # Error signal (cleaned output)
        error_signal[n] = primary[n] - y
        output[n] = error_signal[n]
        
        # Update filter coefficients using LMS rule
        w += step_size * error_signal[n] * x
        
        # Coefficient bounds for stability
        w = np.clip(w, -10, 10)
        
        # Track MSE for convergence analysis
        if n % 100 == 0:
            recent_error = error_signal[max(0, n-100):n+1]
            mse_history.append(np.mean(recent_error**2))
    
    return output, error_signal, w, mse_history

def calculate_snr(signal, noise_estimate):
    """Calculate Signal-to-Noise Ratio in dB"""
    signal_power = np.mean(signal**2)
    noise_power = np.mean(noise_estimate**2)
    
    if noise_power < 1e-10:  # Avoid division by zero
        return float('inf')
    
    snr_db = 10 * np.log10(signal_power / noise_power)
    return snr_db

def calculate_metrics(original, cleaned, reference_clean):
    """Calculate comprehensive performance metrics"""
    # SNR calculations
    original_noise = original - reference_clean
    cleaned_noise = cleaned - reference_clean
    
    snr_original = calculate_snr(reference_clean, original_noise)
    snr_cleaned = calculate_snr(reference_clean, cleaned_noise)
    snr_improvement = snr_cleaned - snr_original
    
    # MSE calculations
    mse_original = np.mean((original - reference_clean)**2)
    mse_cleaned = np.mean((cleaned - reference_clean)**2)
    mse_reduction = ((mse_original - mse_cleaned) / mse_original) * 100
    
    return {
        'snr_original_db': float(snr_original),
        'snr_cleaned_db': float(snr_cleaned),
        'snr_improvement_db': float(snr_improvement),
        'mse_original': float(mse_original),
        'mse_cleaned': float(mse_cleaned),
        'mse_reduction_percent': float(mse_reduction)
    }

def validate_parameters(step_size, filter_length):
    """Validate algorithm parameters for stability"""
    if not (0.001 <= step_size <= 0.1):
        raise ValueError(f"Step size {step_size} must be between 0.001 and 0.1")
    
    if not (8 <= filter_length <= 128):
        raise ValueError(f"Filter length {filter_length} must be between 8 and 128")

def main():
    parser = argparse.ArgumentParser(description='Adaptive Noise Cancellation using LMS Algorithm')
    parser.add_argument('--input-signal', required=True, help='Path to save noisy input signal')
    parser.add_argument('--output-signal', required=True, help='Path to save cleaned signal')
    parser.add_argument('--reference-noise', required=True, help='Path to save reference noise signal')
    parser.add_argument('--step-size', type=float, default=0.01, help='LMS learning rate')
    parser.add_argument('--filter-length', type=int, default=32, help='Number of filter taps')
    parser.add_argument('--metrics-file', required=True, help='Path to save performance metrics JSON')
    
    args = parser.parse_args()
    
    try:
        # Validate parameters
        validate_parameters(args.step_size, args.filter_length)
        
        # Validate output directories exist
        for path in [args.input_signal, args.output_signal, args.reference_noise, args.metrics_file]:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        print("Generating test signals...")
        primary_signal, reference_noise, clean_signal, fs = generate_test_signals()
        
        print(f"Applying LMS adaptive filter (step_size={args.step_size}, filter_length={args.filter_length})...")
        cleaned_signal, error_signal, final_coeffs, mse_history = lms_adaptive_filter(
            primary_signal, reference_noise, args.step_size, args.filter_length
        )
        
        print("Calculating performance metrics...")
        metrics = calculate_metrics(primary_signal, cleaned_signal, clean_signal)
        
        # Add convergence analysis
        if len(mse_history) > 10:
            initial_mse = np.mean(mse_history[:5])
            final_mse = np.mean(mse_history[-5:])
            convergence_rate = (initial_mse - final_mse) / initial_mse * 100
            metrics['convergence_rate_percent'] = float(convergence_rate)
        
        # Add algorithm parameters to metrics
        metrics['parameters'] = {
            'step_size': args.step_size,
            'filter_length': args.filter_length,
            'sampling_rate': fs,
            'signal_duration': 2.0
        }
        
        # Save outputs
        print("Saving results...")
        np.save(args.input_signal, primary_signal)
        np.save(args.output_signal, cleaned_signal)
        np.save(args.reference_noise, reference_noise)
        
        with open(args.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Print summary
        print("\n=== Adaptive Noise Cancellation Results ===")
        print(f"SNR Improvement: {metrics['snr_improvement_db']:.2f} dB")
        print(f"MSE Reduction: {metrics['mse_reduction_percent']:.1f}%")
        if 'convergence_rate_percent' in metrics:
            print(f"Filter Convergence: {metrics['convergence_rate_percent']:.1f}%")
        print(f"Final filter coefficients range: [{np.min(final_coeffs):.3f}, {np.max(final_coeffs):.3f}]")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
