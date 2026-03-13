import numpy as np
import pandas as pd
import h5py
import json
import subprocess
import tempfile
import os
import sys
from scipy import signal
from scipy.fft import fft, fftfreq

def create_data():
    """Generate synthetic test signals and expected results"""
    np.random.seed(42)
    
    # Signal parameters
    fs = 1000  # Sampling frequency
    duration = 2.0
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    
    # Multi-component signal
    freqs = [50, 120, 200]
    amps = [1.0, 0.7, 0.5]
    phases = [0, np.pi/4, np.pi/2]
    
    signal_clean = sum(a * np.sin(2 * np.pi * f * t + p) 
                      for f, a, p in zip(freqs, amps, phases))
    
    # Add noise
    noise_level = 0.1
    noise = np.random.normal(0, noise_level, len(t))
    signal_noisy = signal_clean + noise
    
    return {
        'signal': signal_noisy,
        'fs': fs,
        'freqs': freqs,
        'amps': amps,
        'duration': duration,
        'noise_level': noise_level
    }

def calculate_window_metrics(window):
    """Calculate window characteristics"""
    # Main lobe width (first nulls)
    fft_win = np.abs(fft(window, 8 * len(window)))
    fft_win = fft_win / np.max(fft_win)
    
    # Find main lobe width
    center = len(fft_win) // 2
    main_lobe_width = 0
    for i in range(1, center):
        if fft_win[center + i] < 0.01:  # -40 dB
            main_lobe_width = 2 * i / len(fft_win)
            break
    
    # Side lobe suppression
    main_lobe_end = int(center + main_lobe_width * len(fft_win) / 2)
    if main_lobe_end < len(fft_win):
        max_sidelobe = np.max(fft_win[main_lobe_end:])
        sidelobe_suppression = -20 * np.log10(max_sidelobe) if max_sidelobe > 0 else 100
    else:
        sidelobe_suppression = 100
    
    return main_lobe_width, sidelobe_suppression

def run_tests():
    test_data = create_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Save test signal
        signal_file = 'test_signal.h5'
        with h5py.File(signal_file, 'w') as f:
            f.create_dataset('signal', data=test_data['signal'])
            f.attrs['fs'] = test_data['fs']
            f.attrs['duration'] = test_data['duration']
        
        output_file = 'spectral_analysis.h5'
        json_file = 'analysis_summary.json'
        
        # Test different argument name variations
        possible_args = [
            ['--input', signal_file, '--output', output_file, '--json', json_file, 
             '--fft_size', '1024', '--noise_level', '0.1'],
            ['--input_file', signal_file, '--output_file', output_file, '--json_output', json_file,
             '--fft_length', '1024', '--noise', '0.1'],
            ['-i', signal_file, '-o', output_file, '-j', json_file, 
             '--nfft', '1024', '--noise_level', '0.1']
        ]
        
        success = False
        for args in possible_args:
            try:
                result = subprocess.run([sys.executable, 'generated.py'] + args, 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            # Try minimal arguments
            try:
                result = subprocess.run([sys.executable, 'generated.py', 
                                       '--signal_freq', '50,120,200',
                                       '--signal_amp', '1.0,0.7,0.5',
                                       '--output', output_file,
                                       '--json', json_file], 
                                      capture_output=True, text=True, timeout=30)
                success = result.returncode == 0
            except:
                pass
        
        print(f"PASS: Script execution successful: {success}")
        
        if not success:
            print("PASS: Output files created: False")
            for i in range(13):
                print("PASS: False")
            print("SCORE: 0.0")
            print("SCORE: 0.0")
            return
        
        # Test file creation
        h5_exists = os.path.exists(output_file)
        json_exists = os.path.exists(json_file)
        print(f"PASS: HDF5 output file created: {h5_exists}")
        print(f"PASS: JSON output file created: {json_exists}")
        
        if not h5_exists or not json_exists:
            for i in range(12):
                print("PASS: False")
            print("SCORE: 0.0")
            print("SCORE: 0.0")
            return
        
        # Analyze HDF5 output
        try:
            with h5py.File(output_file, 'r') as f:
                # Test signal data
                has_original = 'original_signal' in f or 'signal' in f
                has_windowed = any('windowed' in key or 'hann' in key.lower() or 'hamming' in key.lower() 
                                 for key in f.keys())
                
                # Test FFT results
                has_fft = any('fft' in key.lower() or 'spectrum' in key.lower() or 'psd' in key.lower() 
                             for key in f.keys())
                
                # Test window functions
                window_count = sum(1 for key in f.keys() 
                                 if any(w in key.lower() for w in ['hann', 'hamming', 'blackman', 'kaiser', 'rectangular']))
                has_multiple_windows = window_count >= 3
                
                # Test frequency data
                has_frequencies = any('freq' in key.lower() for key in f.keys())
                
                print(f"PASS: Original signal data present: {has_original}")
                print(f"PASS: Windowed signal data present: {has_windowed}")
                print(f"PASS: FFT/spectrum data present: {has_fft}")
                print(f"PASS: Multiple window functions (>=3): {has_multiple_windows}")
                print(f"PASS: Frequency data present: {has_frequencies}")
                
        except Exception as e:
            print("PASS: Original signal data present: False")
            print("PASS: Windowed signal data present: False")
            print("PASS: FFT/spectrum data present: False")
            print("PASS: Multiple window functions (>=3): False")
            print("PASS: Frequency data present: False")
        
        # Analyze JSON output
        try:
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            
            # Test window characteristics
            has_window_metrics = any('window' in key.lower() for key in json_data.keys())
            has_leakage_metrics = any(term in str(json_data).lower() 
                                    for term in ['leakage', 'sidelobe', 'suppression'])
            has_resolution_analysis = any(term in str(json_data).lower() 
                                        for term in ['resolution', 'bandwidth', 'scalloping'])
            has_recommendations = any(term in str(json_data).lower() 
                                    for term in ['recommend', 'optimal', 'best'])
            
            # Test numerical metrics
            has_numerical_metrics = any(isinstance(v, (int, float)) for v in json_data.values() 
                                      if v is not None)
            
            print(f"PASS: Window characteristics in JSON: {has_window_metrics}")
            print(f"PASS: Spectral leakage metrics: {has_leakage_metrics}")
            print(f"PASS: Resolution analysis present: {has_resolution_analysis}")
            print(f"PASS: Recommendations provided: {has_recommendations}")
            print(f"PASS: Numerical metrics present: {has_numerical_metrics}")
            
        except Exception as e:
            print("PASS: Window characteristics in JSON: False")
            print("PASS: Spectral leakage metrics: False")
            print("PASS: Resolution analysis present: False")
            print("PASS: Recommendations provided: False")
            print("PASS: Numerical metrics present: False")
        
        # Calculate quality scores
        try:
            with h5py.File(output_file, 'r') as f:
                # Data completeness score
                total_datasets = len(list(f.keys()))
                expected_min_datasets = 8  # signals, windows, ffts, frequencies
                completeness_score = min(1.0, total_datasets / expected_min_datasets)
                
            # Analysis depth score
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            
            analysis_features = [
                any('leakage' in str(json_data).lower()),
                any('sidelobe' in str(json_data).lower()),
                any('resolution' in str(json_data).lower()),
                any('scalloping' in str(json_data).lower()),
                any('bandwidth' in str(json_data).lower()),
                len([k for k in json_data.keys() if isinstance(json_data[k], (int, float))]) >= 5
            ]
            analysis_score = sum(analysis_features) / len(analysis_features)
            
        except:
            completeness_score = 0.0
            analysis_score = 0.0
        
        print(f"SCORE: {completeness_score:.3f}")
        print(f"SCORE: {analysis_score:.3f}")

if __name__ == "__main__":
    run_tests()
