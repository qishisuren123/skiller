import numpy as np
import matplotlib.pyplot as plt
import json
import subprocess
import tempfile
import os
import sys
from pathlib import Path

def create_data():
    """Generate synthetic audio data with echo artifacts"""
    np.random.seed(42)
    
    # Create original clean signal (mix of sine waves and noise)
    duration = 2.0  # seconds
    sample_rate = 8000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Original signal: combination of tones and some noise
    original = (0.5 * np.sin(2 * np.pi * 440 * t) + 
               0.3 * np.sin(2 * np.pi * 880 * t) + 
               0.2 * np.sin(2 * np.pi * 220 * t) +
               0.1 * np.random.randn(len(t)))
    
    # Normalize
    original = original / np.max(np.abs(original)) * 0.8
    
    # Add echo
    echo_delay = 200  # samples
    echo_attenuation = 0.4
    
    # Create echo signal
    echo_signal = np.zeros_like(original)
    echo_signal[echo_delay:] = original[:-echo_delay] * echo_attenuation
    
    # Combine original with echo
    audio_with_echo = original + echo_signal
    
    # Normalize final signal
    audio_with_echo = audio_with_echo / np.max(np.abs(audio_with_echo)) * 0.9
    
    return {
        'audio_with_echo': audio_with_echo,
        'original_clean': original,
        'true_echo_delay': echo_delay,
        'true_echo_attenuation': echo_attenuation
    }

def test_echo_removal():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        data = create_data()
        
        # Save input data
        input_file = 'audio_with_echo.npy'
        output_file = 'cleaned_audio.npy'
        report_file = 'metrics.json'
        plot_file = 'comparison.png'
        
        np.save(input_file, data['audio_with_echo'])
        
        # Test different argument name variations
        cmd_variations = [
            ['--input', input_file, '--output', output_file, '--report', report_file, '--plot', plot_file],
            ['-i', input_file, '-o', output_file, '-r', report_file, '-p', plot_file],
            ['--input_file', input_file, '--output_file', output_file, '--report_file', report_file, '--plot_file', plot_file]
        ]
        
        success = False
        for cmd_args in cmd_variations:
            try:
                result = subprocess.run([sys.executable, 'generated.py'] + cmd_args, 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed with all argument variations")
            return
        
        # Test 1: Script runs successfully
        print("PASS: Script executed successfully")
        
        # Test 2: Output audio file exists
        if os.path.exists(output_file):
            print("PASS: Output audio file created")
        else:
            print("FAIL: Output audio file not created")
            return
        
        # Test 3: Report JSON file exists
        if os.path.exists(report_file):
            print("PASS: Report JSON file created")
        else:
            print("FAIL: Report JSON file not created")
            return
        
        # Test 4: Plot file exists
        if os.path.exists(plot_file):
            print("PASS: Comparison plot created")
        else:
            print("FAIL: Comparison plot not created")
        
        # Load results
        try:
            cleaned_audio = np.load(output_file)
            with open(report_file, 'r') as f:
                report = json.load(f)
        except Exception as e:
            print(f"FAIL: Could not load results: {e}")
            return
        
        # Test 5: Output audio has correct shape
        if cleaned_audio.shape == data['audio_with_echo'].shape:
            print("PASS: Output audio has correct dimensions")
        else:
            print("FAIL: Output audio has incorrect dimensions")
        
        # Test 6: Output audio is properly normalized
        if np.max(np.abs(cleaned_audio)) <= 1.0:
            print("PASS: Output audio is properly normalized")
        else:
            print("FAIL: Output audio exceeds normalized range")
        
        # Test 7: Report contains required fields
        required_fields = ['echo_delay', 'attenuation_factor', 'erle', 'sir_improvement']
        if all(field in report for field in required_fields):
            print("PASS: Report contains all required metrics")
        else:
            print("FAIL: Report missing required metrics")
            return
        
        # Test 8: Echo delay detection accuracy
        detected_delay = report['echo_delay']
        delay_error = abs(detected_delay - data['true_echo_delay'])
        if delay_error <= 20:  # Allow 20 sample tolerance
            print("PASS: Echo delay detected with reasonable accuracy")
        else:
            print("FAIL: Echo delay detection inaccurate")
        
        # Test 9: Attenuation factor is reasonable
        detected_attenuation = report['attenuation_factor']
        if 0.1 <= detected_attenuation <= 0.8:
            print("PASS: Detected attenuation factor is reasonable")
        else:
            print("FAIL: Detected attenuation factor is unreasonable")
        
        # Test 10: ERLE is positive (echo reduction achieved)
        erle = report['erle']
        if erle > 0:
            print("PASS: ERLE indicates echo reduction")
        else:
            print("FAIL: ERLE does not indicate echo reduction")
        
        # Test 11: SIR improvement is positive
        sir_improvement = report['sir_improvement']
        if sir_improvement > 0:
            print("PASS: Signal-to-echo ratio improved")
        else:
            print("FAIL: Signal-to-echo ratio not improved")
        
        # Test 12: Cleaned audio has reduced echo correlation
        # Calculate autocorrelation at echo delay
        original_autocorr = np.correlate(data['audio_with_echo'], data['audio_with_echo'], mode='full')
        cleaned_autocorr = np.correlate(cleaned_audio, cleaned_audio, mode='full')
        
        center = len(original_autocorr) // 2
        echo_pos = center + data['true_echo_delay']
        
        if echo_pos < len(original_autocorr):
            original_echo_corr = abs(original_autocorr[echo_pos])
            cleaned_echo_corr = abs(cleaned_autocorr[echo_pos])
            
            if cleaned_echo_corr < original_echo_corr:
                print("PASS: Echo correlation reduced in cleaned signal")
            else:
                print("FAIL: Echo correlation not reduced")
        else:
            print("PASS: Echo correlation test skipped (boundary issue)")
        
        # Test 13: Output values are finite
        if np.all(np.isfinite(cleaned_audio)):
            print("PASS: All output values are finite")
        else:
            print("FAIL: Output contains non-finite values")
        
        # Test 14: Plot file is valid image
        try:
            from PIL import Image
            img = Image.open(plot_file)
            if img.size[0] > 100 and img.size[1] > 100:
                print("PASS: Plot file is valid and reasonable size")
            else:
                print("FAIL: Plot file too small")
        except:
            print("FAIL: Plot file is not a valid image")
        
        # Test 15: JSON report is properly formatted
        try:
            # Check if all values are numeric
            numeric_check = all(isinstance(report[field], (int, float)) for field in required_fields)
            if numeric_check:
                print("PASS: All report metrics are numeric")
            else:
                print("FAIL: Some report metrics are not numeric")
        except:
            print("FAIL: Error checking report format")
        
        # SCORE 1: Echo removal effectiveness (0-1)
        # Based on reduction in echo correlation
        try:
            echo_reduction_ratio = min(1.0, cleaned_echo_corr / (original_echo_corr + 1e-10))
            echo_effectiveness = max(0.0, 1.0 - echo_reduction_ratio)
            print(f"SCORE: Echo removal effectiveness: {echo_effectiveness:.3f}")
        except:
            print("SCORE: Echo removal effectiveness: 0.000")
        
        # SCORE 2: Overall signal quality preservation (0-1)
        # Based on correlation with original clean signal and avoiding over-processing
        try:
            # Measure how well the cleaned signal correlates with original
            correlation = np.corrcoef(cleaned_audio[:len(data['original_clean'])], 
                                    data['original_clean'][:len(cleaned_audio)])[0,1]
            
            # Measure signal power preservation
            original_power = np.mean(data['original_clean']**2)
            cleaned_power = np.mean(cleaned_audio**2)
            power_ratio = min(cleaned_power / (original_power + 1e-10), 1.0)
            
            # Combined quality score
            quality_score = max(0.0, (abs(correlation) * 0.7 + power_ratio * 0.3))
            print(f"SCORE: Signal quality preservation: {quality_score:.3f}")
        except:
            print("SCORE: Signal quality preservation: 0.000")

if __name__ == "__main__":
    test_echo_removal()
