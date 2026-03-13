import numpy as np
import json
import subprocess
import tempfile
import os
import sys
from pathlib import Path

def create_data():
    """Generate synthetic noisy audio signal data"""
    # Signal parameters
    fs = 8000  # 8kHz sampling rate
    duration = 2.0  # 2 seconds
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    
    # Clean signal components
    signal1 = 0.8 * np.sin(2 * np.pi * 440 * t)  # 440Hz sine
    signal2 = 0.6 * np.sin(2 * np.pi * 880 * t)  # 880Hz sine
    clean_signal = signal1 + signal2
    
    # Noise components
    np.random.seed(42)
    primary_noise = 0.5 * np.random.randn(len(t))
    
    # Correlated reference noise (delayed and scaled)
    delay_samples = 10
    reference_noise = 0.7 * np.roll(primary_noise, delay_samples) + 0.2 * np.random.randn(len(t))
    
    # Noisy signal
    noisy_signal = clean_signal + primary_noise
    
    return {
        'noisy_signal': noisy_signal,
        'clean_signal': clean_signal,
        'reference_noise': reference_noise,
        'sampling_rate': fs,
        'time': t
    }

def calculate_snr(signal, noise):
    """Calculate Signal-to-Noise Ratio"""
    signal_power = np.mean(signal**2)
    noise_power = np.mean(noise**2)
    if noise_power == 0:
        return float('inf')
    return 10 * np.log10(signal_power / noise_power)

def test_script():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Generate test data
        data = create_data()
        
        # Save input data
        input_signal_file = tmpdir / "input_signal.npy"
        reference_noise_file = tmpdir / "reference_noise.npy"
        np.save(input_signal_file, data['noisy_signal'])
        np.save(reference_noise_file, data['reference_noise'])
        
        # Define output files
        output_signal_file = tmpdir / "output_signal.npy"
        metrics_file = tmpdir / "metrics.json"
        
        # Test with default parameters
        cmd = [
            sys.executable, "generated.py",
            "--input-signal", str(input_signal_file),
            "--output-signal", str(output_signal_file),
            "--reference-noise", str(reference_noise_file),
            "--metrics-file", str(metrics_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            print("PASS: Script executed without timeout")
        except subprocess.TimeoutExpired:
            print("FAIL: Script execution timed out")
            return
        except Exception as e:
            print(f"FAIL: Script execution failed: {e}")
            return
        
        if result.returncode != 0:
            print(f"FAIL: Script returned non-zero exit code: {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return
        else:
            print("PASS: Script returned zero exit code")
        
        # Test output files exist
        if output_signal_file.exists():
            print("PASS: Output signal file created")
        else:
            print("FAIL: Output signal file not created")
            return
        
        if metrics_file.exists():
            print("PASS: Metrics file created")
        else:
            print("FAIL: Metrics file not created")
            return
        
        # Load and validate outputs
        try:
            output_signal = np.load(output_signal_file)
            print("PASS: Output signal file is valid NumPy array")
        except:
            print("FAIL: Output signal file is not a valid NumPy array")
            return
        
        try:
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
            print("PASS: Metrics file is valid JSON")
        except:
            print("FAIL: Metrics file is not valid JSON")
            return
        
        # Test signal dimensions
        if len(output_signal) == len(data['noisy_signal']):
            print("PASS: Output signal has correct length")
        else:
            print("FAIL: Output signal has incorrect length")
        
        # Test metrics content
        required_metrics = ['snr_before', 'snr_after', 'mse_before', 'mse_after']
        missing_metrics = [m for m in required_metrics if m not in metrics]
        if not missing_metrics:
            print("PASS: All required metrics present")
        else:
            print(f"FAIL: Missing metrics: {missing_metrics}")
        
        # Test SNR improvement
        if 'snr_before' in metrics and 'snr_after' in metrics:
            if metrics['snr_after'] > metrics['snr_before']:
                print("PASS: SNR improved after noise cancellation")
            else:
                print("FAIL: SNR did not improve after noise cancellation")
        
        # Test MSE reduction
        if 'mse_before' in metrics and 'mse_after' in metrics:
            if metrics['mse_after'] < metrics['mse_before']:
                print("PASS: MSE reduced after noise cancellation")
            else:
                print("FAIL: MSE did not reduce after noise cancellation")
        
        # Test with custom parameters
        cmd_custom = [
            sys.executable, "generated.py",
            "--input-signal", str(input_signal_file),
            "--output-signal", str(tmpdir / "output_custom.npy"),
            "--reference-noise", str(reference_noise_file),
            "--step-size", "0.005",
            "--filter-length", "64",
            "--metrics-file", str(tmpdir / "metrics_custom.json")
        ]
        
        try:
            result_custom = subprocess.run(cmd_custom, capture_output=True, text=True, timeout=30)
            if result_custom.returncode == 0:
                print("PASS: Script works with custom parameters")
            else:
                print("FAIL: Script failed with custom parameters")
        except:
            print("FAIL: Script failed with custom parameters")
        
        # Test parameter validation - invalid step size
        cmd_invalid = [
            sys.executable, "generated.py",
            "--input-signal", str(input_signal_file),
            "--output-signal", str(tmpdir / "output_invalid.npy"),
            "--reference-noise", str(reference_noise_file),
            "--step-size", "0.5",  # Too large
            "--metrics-file", str(tmpdir / "metrics_invalid.json")
        ]
        
        try:
            result_invalid = subprocess.run(cmd_invalid, capture_output=True, text=True, timeout=30)
            if result_invalid.returncode != 0:
                print("PASS: Script properly validates step size bounds")
            else:
                print("FAIL: Script should reject invalid step size")
        except:
            print("PASS: Script properly validates step size bounds")
        
        # Test noise reduction effectiveness
        original_noise_level = np.std(data['noisy_signal'] - data['clean_signal'])
        output_noise_level = np.std(output_signal - data['clean_signal'])
        
        if output_noise_level < original_noise_level:
            print("PASS: Noise level reduced in output signal")
        else:
            print("FAIL: Noise level not reduced in output signal")
        
        # Test signal preservation
        clean_correlation_before = np.corrcoef(data['noisy_signal'], data['clean_signal'])[0, 1]
        clean_correlation_after = np.corrcoef(output_signal, data['clean_signal'])[0, 1]
        
        if clean_correlation_after > clean_correlation_before:
            print("PASS: Clean signal correlation improved")
        else:
            print("FAIL: Clean signal correlation not improved")
        
        # Calculate performance scores
        if 'snr_before' in metrics and 'snr_after' in metrics:
            snr_improvement = metrics['snr_after'] - metrics['snr_before']
            snr_score = min(1.0, max(0.0, snr_improvement / 10.0))  # Normalize to 0-1
            print(f"SCORE: SNR improvement score: {snr_score:.3f}")
        else:
            print("SCORE: SNR improvement score: 0.000")
        
        # Noise reduction score
        noise_reduction_ratio = 1.0 - (output_noise_level / original_noise_level)
        noise_score = min(1.0, max(0.0, noise_reduction_ratio))
        print(f"SCORE: Noise reduction score: {noise_score:.3f}")

if __name__ == "__main__":
    test_script()
