import os
import sys
import tempfile
import subprocess
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
import shutil

def create_data():
    """Generate synthetic ocean buoy data"""
    # Create 6 hours of data at 2 Hz sampling
    dt = 0.5  # seconds
    duration = 6 * 3600  # 6 hours
    t = np.arange(0, duration, dt)
    
    # Generate realistic wave spectrum with multiple components
    np.random.seed(42)
    
    # Primary swell (0.08 Hz, ~12.5s period)
    wave1 = 1.5 * np.sin(2 * np.pi * 0.08 * t + np.random.uniform(0, 2*np.pi))
    
    # Secondary swell (0.12 Hz, ~8.3s period)  
    wave2 = 1.0 * np.sin(2 * np.pi * 0.12 * t + np.random.uniform(0, 2*np.pi))
    
    # Wind waves (0.25 Hz, 4s period)
    wave3 = 0.8 * np.sin(2 * np.pi * 0.25 * t + np.random.uniform(0, 2*np.pi))
    
    # Add some random phase modulation and noise
    phase_noise = 0.1 * np.cumsum(np.random.randn(len(t))) * dt
    elevation = wave1 + wave2 + wave3 + 0.3 * np.random.randn(len(t))
    elevation += 0.2 * np.sin(2 * np.pi * 0.05 * t + phase_noise)  # Low frequency component
    
    # Add a small linear trend
    elevation += 0.0001 * t
    
    # Create timestamps
    timestamps = pd.date_range('2024-01-01 00:00:00', periods=len(t), freq='0.5S')
    
    # Create some data gaps (5% of data)
    gap_indices = np.random.choice(len(t), size=int(0.05 * len(t)), replace=False)
    elevation[gap_indices] = np.nan
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'elevation': elevation
    })

def run_test():
    results = {'passed': 0, 'failed': 0, 'tests': []}
    
    def test_condition(name, condition, points=1):
        if condition:
            results['passed'] += points
            results['tests'].append(f"PASS: {name}")
            return True
        else:
            results['failed'] += points  
            results['tests'].append(f"FAIL: {name}")
            return False
    
    # Create test data
    data = create_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save input data
        input_file = os.path.join(tmpdir, 'buoy_data.csv')
        data.to_csv(input_file, index=False)
        
        output_dir = os.path.join(tmpdir, 'output')
        os.makedirs(output_dir)
        
        # Test different argument name variations
        possible_args = [
            ['--input', input_file, '--output', output_dir],
            ['--input_file', input_file, '--output_dir', output_dir],
            ['-i', input_file, '-o', output_dir],
            ['--data', input_file, '--outdir', output_dir]
        ]
        
        success = False
        for args in possible_args:
            try:
                result = subprocess.run([sys.executable, 'generated.py'] + args, 
                                      capture_output=True, text=True, cwd=tmpdir, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        test_condition("Script runs without errors", success)
        
        if not success:
            print("Failed to run script with any argument combination")
            return results
        
        # Check for required output files
        json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
        csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
        plot_files = [f for f in os.listdir(output_dir) if f.endswith(('.png', '.pdf', '.jpg'))]
        
        test_condition("JSON summary file created", len(json_files) >= 1)
        test_condition("CSV spectrum file created", len(csv_files) >= 1)  
        test_condition("Spectrum plot created", len(plot_files) >= 1)
        
        if len(json_files) == 0:
            return results
            
        # Load and validate JSON output
        json_file = os.path.join(output_dir, json_files[0])
        try:
            with open(json_file, 'r') as f:
                summary = json.load(f)
        except:
            test_condition("JSON file is valid", False)
            return results
            
        test_condition("JSON file is valid", True)
        
        # Check required parameters in JSON
        required_params = ['significant_wave_height', 'peak_frequency', 'mean_frequency']
        has_params = all(param in summary for param in required_params)
        test_condition("JSON contains required wave parameters", has_params)
        
        if has_params:
            hs = summary.get('significant_wave_height', 0)
            fp = summary.get('peak_frequency', 0)
            fm = summary.get('mean_frequency', 0)
            
            # Validate parameter ranges (based on synthetic data)
            test_condition("Significant wave height in reasonable range (1-4m)", 1.0 <= hs <= 4.0)
            test_condition("Peak frequency in wave band (0.05-0.5 Hz)", 0.05 <= fp <= 0.5)
            test_condition("Mean frequency is positive", fm > 0)
            test_condition("Peak frequency near expected value (~0.08 Hz)", abs(fp - 0.08) < 0.05)
        
        # Validate CSV spectrum file
        if len(csv_files) > 0:
            csv_file = os.path.join(output_dir, csv_files[0])
            try:
                spectrum_data = pd.read_csv(csv_file)
                
                required_cols = ['frequency', 'power_spectral_density']
                has_cols = all(col in spectrum_data.columns for col in required_cols)
                test_condition("CSV contains frequency and PSD columns", has_cols)
                
                if has_cols:
                    freqs = spectrum_data['frequency'].values
                    psd = spectrum_data['power_spectral_density'].values
                    
                    test_condition("Frequency values are positive and increasing", 
                                 np.all(freqs > 0) and np.all(np.diff(freqs) > 0))
                    test_condition("PSD values are non-negative", np.all(psd >= 0))
                    test_condition("Frequency range covers wave band", 
                                 freqs.min() <= 0.06 and freqs.max() >= 0.3)
                    
            except Exception as e:
                test_condition("CSV file is readable", False)
        
        # Quality control checks
        qc_flags = summary.get('quality_flags', {})
        test_condition("Quality control flags present", isinstance(qc_flags, dict))
        
        # Calculate scores
        if has_params and len(csv_files) > 0:
            # Score 1: Accuracy of peak frequency detection
            expected_peak = 0.08  # Hz
            actual_peak = summary.get('peak_frequency', 0)
            freq_accuracy = max(0, 1 - abs(actual_peak - expected_peak) / 0.02)
            
            # Score 2: Spectral resolution and coverage
            try:
                spectrum_data = pd.read_csv(os.path.join(output_dir, csv_files[0]))
                freqs = spectrum_data['frequency'].values
                freq_resolution = np.mean(np.diff(freqs))
                coverage_score = 1.0 if (freqs.min() <= 0.05 and freqs.max() >= 0.4) else 0.5
                resolution_score = 1.0 if freq_resolution <= 0.01 else 0.5
                spectral_score = (coverage_score + resolution_score) / 2
            except:
                spectral_score = 0.0
        else:
            freq_accuracy = 0.0
            spectral_score = 0.0
        
        results['tests'].append(f"SCORE: Peak frequency accuracy: {freq_accuracy:.3f}")
        results['tests'].append(f"SCORE: Spectral quality: {spectral_score:.3f}")
    
    return results

if __name__ == "__main__":
    results = run_test()
    
    for test in results['tests']:
        print(test)
    
    print(f"\nPassed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Score: {results['passed']}/{results['passed'] + results['failed']}")
