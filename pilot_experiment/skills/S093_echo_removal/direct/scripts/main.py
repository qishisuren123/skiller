import numpy as np
import matplotlib.pyplot as plt
import json
import argparse
from scipy.signal import find_peaks
import os

def load_audio_signal(filepath):
    """Load and validate audio signal from .npy file."""
    try:
        signal = np.load(filepath)
        if signal.ndim != 1:
            raise ValueError("Audio signal must be 1-dimensional")
        if np.max(np.abs(signal)) > 1.0:
            print("Warning: Signal not normalized, clipping to [-1, 1]")
            signal = np.clip(signal, -1.0, 1.0)
        return signal
    except Exception as e:
        raise IOError(f"Error loading audio file: {e}")

def detect_echo_parameters(signal, min_delay=50, max_delay=500):
    """Detect echo delay and attenuation using autocorrelation analysis."""
    # Calculate normalized autocorrelation
    autocorr = np.correlate(signal, signal, mode='full')
    autocorr = autocorr[len(autocorr)//2:]  # Take positive lags only
    autocorr = autocorr / autocorr[0]  # Normalize
    
    # Search for echo in specified delay range
    search_region = autocorr[min_delay:min(max_delay, len(autocorr))]
    
    # Find peaks with minimum prominence to avoid noise
    peaks, properties = find_peaks(search_region, prominence=0.1, distance=20)
    
    if len(peaks) == 0:
        return None, None, autocorr
    
    # Select strongest peak as echo delay
    strongest_peak_idx = peaks[np.argmax(search_region[peaks])]
    delay = strongest_peak_idx + min_delay
    attenuation = autocorr[delay]
    
    # Clamp attenuation to realistic range
    attenuation = np.clip(np.abs(attenuation), 0.2, 0.7)
    
    return delay, attenuation, autocorr

def cancel_echo(signal, delay, attenuation):
    """Apply echo cancellation using detected parameters."""
    if delay is None or attenuation is None:
        return signal
    
    output = signal.copy().astype(np.float64)
    
    # Subtract delayed and attenuated version
    for i in range(delay, len(signal)):
        output[i] = signal[i] - attenuation * signal[i - delay]
    
    # Ensure output stays in valid range
    output = np.clip(output, -1.0, 1.0)
    return output

def calculate_quality_metrics(original, processed, delay, attenuation):
    """Calculate ERLE and Signal-to-Echo Ratio improvement."""
    if delay is None:
        return {"ERLE_dB": 0.0, "SER_improvement_dB": 0.0}
    
    # Create echo component for analysis
    echo_original = np.zeros_like(original)
    echo_original[delay:] = attenuation * original[:-delay]
    
    echo_processed = np.zeros_like(processed)
    echo_processed[delay:] = attenuation * processed[:-delay]
    
    # Calculate echo power
    echo_power_orig = np.mean(echo_original**2)
    echo_power_proc = np.mean(echo_processed**2)
    
    # ERLE calculation
    erle_db = 10 * np.log10(max(echo_power_orig / max(echo_power_proc, 1e-10), 1e-10))
    
    # Signal-to-Echo Ratio improvement
    signal_power = np.mean(original**2)
    ser_orig = 10 * np.log10(signal_power / max(echo_power_orig, 1e-10))
    ser_proc = 10 * np.log10(signal_power / max(echo_power_proc, 1e-10))
    ser_improvement = ser_proc - ser_orig
    
    return {
        "ERLE_dB": float(erle_db),
        "SER_improvement_dB": float(ser_improvement)
    }

def create_visualization(original, processed, autocorr, delay, output_dir):
    """Create comparison plots for analysis."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    # Time domain comparison
    time_axis = np.arange(len(original))
    axes[0, 0].plot(time_axis, original, label='Original + Echo', alpha=0.7)
    axes[0, 0].plot(time_axis, processed, label='Echo Cancelled', alpha=0.7)
    axes[0, 0].set_title('Time Domain Comparison')
    axes[0, 0].set_xlabel('Sample')
    axes[0, 0].set_ylabel('Amplitude')
    axes[0, 0].legend()
    axes[0, 0].grid(True)
    
    # Autocorrelation function
    lag_axis = np.arange(len(autocorr))
    axes[0, 1].plot(lag_axis, autocorr)
    if delay is not None:
        axes[0, 1].axvline(x=delay, color='r', linestyle='--', label=f'Detected Echo Delay: {delay}')
        axes[0, 1].legend()
    axes[0, 1].set_title('Autocorrelation Function')
    axes[0, 1].set_xlabel('Lag (samples)')
    axes[0, 1].set_ylabel('Correlation')
    axes[0, 1].grid(True)
    
    # Spectral comparison
    axes[1, 0].specgram(original, Fs=1, alpha=0.7)
    axes[1, 0].set_title('Original Signal Spectrogram')
    axes[1, 0].set_ylabel('Frequency')
    
    axes[1, 1].specgram(processed, Fs=1, alpha=0.7)
    axes[1, 1].set_title('Processed Signal Spectrogram')
    axes[1, 1].set_ylabel('Frequency')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'echo_cancellation_analysis.png'), dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Adaptive Echo Cancellation for Audio Signals')
    parser.add_argument('input_file', help='Input .npy file containing audio signal')
    parser.add_argument('--output_dir', default='.', help='Output directory for results')
    parser.add_argument('--min_delay', type=int, default=50, help='Minimum echo delay in samples')
    parser.add_argument('--max_delay', type=int, default=500, help='Maximum echo delay in samples')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load audio signal
    print("Loading audio signal...")
    signal = load_audio_signal(args.input_file)
    print(f"Loaded signal with {len(signal)} samples")
    
    # Detect echo parameters
    print("Detecting echo parameters...")
    delay, attenuation, autocorr = detect_echo_parameters(signal, args.min_delay, args.max_delay)
    
    if delay is None:
        print("No significant echo detected")
        delay_samples, attenuation_factor = 0, 0.0
    else:
        delay_samples, attenuation_factor = delay, attenuation
        print(f"Detected echo: delay={delay_samples} samples, attenuation={attenuation_factor:.3f}")
    
    # Apply echo cancellation
    print("Applying echo cancellation...")
    processed_signal = cancel_echo(signal, delay, attenuation)
    
    # Calculate quality metrics
    print("Calculating quality metrics...")
    metrics = calculate_quality_metrics(signal, processed_signal, delay, attenuation)
    
    # Generate outputs
    output_signal_path = os.path.join(args.output_dir, 'echo_cancelled_signal.npy')
    np.save(output_signal_path, processed_signal)
    
    # Create report
    report = {
        "echo_delay_samples": int(delay_samples),
        "attenuation_factor": float(attenuation_factor),
        "quality_metrics": metrics,
        "processing_parameters": {
            "min_delay": args.min_delay,
            "max_delay": args.max_delay
        }
    }
    
    report_path = os.path.join(args.output_dir, 'echo_cancellation_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Create visualization
    print("Generating visualization...")
    create_visualization(signal, processed_signal, autocorr, delay, args.output_dir)
    
    print(f"\nResults saved to {args.output_dir}")
    print(f"ERLE: {metrics['ERLE_dB']:.2f} dB")
    print(f"SER Improvement: {metrics['SER_improvement_dB']:.2f} dB")

if __name__ == "__main__":
    main()
