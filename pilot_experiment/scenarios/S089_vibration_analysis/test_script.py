import os
import sys
import json
import tempfile
import subprocess
import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import zscore
import argparse

def create_data():
    """Generate test parameters for vibration analysis"""
    return {
        'basic_case': {
            'sampling_rate': 1000,
            'duration': 5,
            'fundamental_freq': 30,
            'noise_level': 0.05,
            'output': 'basic_results.json'
        },
        'fault_case': {
            'sampling_rate': 2000,
            'duration': 8,
            'fundamental_freq': 25,
            'noise_level': 0.1,
            'output': 'fault_results.json',
            'save_spectrum': 'fault_spectrum.csv'
        },
        'high_noise_case': {
            'sampling_rate': 500,
            'duration': 10,
            'fundamental_freq': 15,
            'noise_level': 0.3,
            'output': 'noisy_results.json'
        }
    }

def run_test():
    test_data = create_data()
    
    # Test basic functionality
    basic_params = test_data['basic_case']
    cmd = [
        sys.executable, 'generated.py',
        '--sampling_rate', str(basic_params['sampling_rate']),
        '--duration', str(basic_params['duration']),
        '--fundamental_freq', str(basic_params['fundamental_freq']),
        '--noise_level', str(basic_params['noise_level']),
        '--output', basic_params['output']
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        basic_success = result.returncode == 0
    except:
        basic_success = False
    
    # Test with spectrum output
    fault_params = test_data['fault_case']
    cmd_fault = [
        sys.executable, 'generated.py',
        '--sampling_rate', str(fault_params['sampling_rate']),
        '--duration', str(fault_params['duration']),
        '--fundamental_freq', str(fault_params['fundamental_freq']),
        '--noise_level', str(fault_params['noise_level']),
        '--output', fault_params['output'],
        '--save_spectrum', fault_params['save_spectrum']
    ]
    
    try:
        result_fault = subprocess.run(cmd_fault, capture_output=True, text=True, timeout=30)
        fault_success = result_fault.returncode == 0
    except:
        fault_success = False
    
    # Test high noise case
    noise_params = test_data['high_noise_case']
    cmd_noise = [
        sys.executable, 'generated.py',
        '--sampling_rate', str(noise_params['sampling_rate']),
        '--duration', str(noise_params['duration']),
        '--fundamental_freq', str(noise_params['fundamental_freq']),
        '--noise_level', str(noise_params['noise_level']),
        '--output', noise_params['output']
    ]
    
    try:
        result_noise = subprocess.run(cmd_noise, capture_output=True, text=True, timeout=30)
        noise_success = result_noise.returncode == 0
    except:
        noise_success = False
    
    # Load and validate results
    results_valid = False
    spectrum_valid = False
    peaks_detected = False
    harmonics_found = False
    fault_analysis_present = False
    json_structure_valid = False
    spectrum_file_valid = False
    peak_frequencies_reasonable = False
    harmonic_ratios_valid = False
    fault_indicators_present = False
    frequency_resolution_appropriate = False
    amplitude_values_reasonable = False
    
    spectral_accuracy = 0.0
    fault_detection_score = 0.0
    
    try:
        # Validate basic results
        if os.path.exists(basic_params['output']):
            with open(basic_params['output'], 'r') as f:
                basic_results = json.load(f)
            
            # Check JSON structure
            required_keys = ['peaks', 'harmonics', 'fault_indicators', 'summary']
            json_structure_valid = all(key in basic_results for key in required_keys)
            results_valid = True
            
            # Check peaks detection
            if 'peaks' in basic_results and isinstance(basic_results['peaks'], list):
                peaks_detected = len(basic_results['peaks']) > 0
                
                # Validate peak structure and values
                if peaks_detected:
                    peak_valid = True
                    for peak in basic_results['peaks']:
                        if not all(key in peak for key in ['frequency', 'amplitude']):
                            peak_valid = False
                            break
                        if not (0 < peak['frequency'] < basic_params['sampling_rate']/2):
                            peak_valid = False
                            break
                    peak_frequencies_reasonable = peak_valid
            
            # Check harmonics analysis
            if 'harmonics' in basic_results:
                harmonics_found = isinstance(basic_results['harmonics'], dict)
                if harmonics_found and 'fundamental' in basic_results['harmonics']:
                    fund_freq = basic_results['harmonics'].get('fundamental', 0)
                    expected_fund = basic_params['fundamental_freq']
                    harmonic_ratios_valid = abs(fund_freq - expected_fund) < expected_fund * 0.2
            
            # Check fault analysis
            if 'fault_indicators' in basic_results:
                fault_analysis_present = isinstance(basic_results['fault_indicators'], dict)
                fault_keys = ['bearing_fault_risk', 'misalignment_risk', 'imbalance_risk']
                fault_indicators_present = any(key in basic_results['fault_indicators'] for key in fault_keys)
        
        # Validate spectrum file
        if os.path.exists(fault_params['save_spectrum']):
            spectrum_df = pd.read_csv(fault_params['save_spectrum'])
            spectrum_file_valid = True
            
            required_cols = ['frequency', 'power']
            spectrum_valid = all(col in spectrum_df.columns for col in required_cols)
            
            if spectrum_valid:
                # Check frequency resolution
                freq_diff = np.diff(spectrum_df['frequency'].values)
                frequency_resolution_appropriate = np.std(freq_diff) < np.mean(freq_diff) * 0.1
                
                # Check amplitude reasonableness
                power_values = spectrum_df['power'].values
                amplitude_values_reasonable = np.all(power_values >= 0) and np.any(power_values > 0)
        
        # Calculate spectral accuracy score
        if results_valid and peaks_detected:
            accuracy_factors = [
                peak_frequencies_reasonable,
                harmonic_ratios_valid,
                frequency_resolution_appropriate,
                amplitude_values_reasonable
            ]
            spectral_accuracy = sum(accuracy_factors) / len(accuracy_factors)
        
        # Calculate fault detection score
        if fault_analysis_present:
            fault_factors = [
                fault_indicators_present,
                harmonics_found,
                json_structure_valid,
                peaks_detected
            ]
            fault_detection_score = sum(fault_factors) / len(fault_factors)
    
    except Exception as e:
        pass
    
    # Print results
    print(f"PASS: Script runs without errors (basic case): {basic_success}")
    print(f"PASS: Script runs with spectrum output: {fault_success}")
    print(f"PASS: Script handles high noise case: {noise_success}")
    print(f"PASS: Results file created and valid JSON: {results_valid}")
    print(f"PASS: Spectrum file created when requested: {spectrum_file_valid}")
    print(f"PASS: Spectral peaks detected: {peaks_detected}")
    print(f"PASS: Harmonic analysis performed: {harmonics_found}")
    print(f"PASS: Fault analysis present: {fault_analysis_present}")
    print(f"PASS: JSON structure contains required keys: {json_structure_valid}")
    print(f"PASS: Peak frequencies are reasonable: {peak_frequencies_reasonable}")
    print(f"PASS: Harmonic ratios are valid: {harmonic_ratios_valid}")
    print(f"PASS: Fault indicators present: {fault_indicators_present}")
    print(f"PASS: Frequency resolution appropriate: {frequency_resolution_appropriate}")
    print(f"PASS: Amplitude values reasonable: {amplitude_values_reasonable}")
    print(f"PASS: Spectrum CSV has correct structure: {spectrum_valid}")
    
    print(f"SCORE: Spectral analysis accuracy: {spectral_accuracy:.3f}")
    print(f"SCORE: Fault detection capability: {fault_detection_score:.3f}")

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        run_test()
