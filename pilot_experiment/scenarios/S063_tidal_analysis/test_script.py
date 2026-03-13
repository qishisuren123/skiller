import subprocess
import tempfile
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
import sys

def create_data():
    """Create synthetic tidal data parameters for testing"""
    # Known tidal constituents with periods in hours
    constituents = {
        'M2': {'period': 12.42, 'amplitude': 1.2},
        'S2': {'period': 12.0, 'amplitude': 0.4},
        'O1': {'period': 25.82, 'amplitude': 0.3},
        'K1': {'period': 23.93, 'amplitude': 0.2},
        'N2': {'period': 12.66, 'amplitude': 0.25}
    }
    return constituents

def run_test():
    score = 0
    max_score = 15
    amplitude_score = 0.0
    frequency_score = 0.0
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Test parameters
        duration = 7  # days
        sampling_interval = 0.5  # hours
        min_amplitude = 0.15  # meters
        harmonics_file = "tidal_harmonics.json"
        plot_file = "tidal_plot.png"
        
        # Run the script with various argument name possibilities
        cmd_variations = [
            ["python", "generated.py", "--duration", str(duration), 
             "--sampling_interval", str(sampling_interval),
             "--output_harmonics", harmonics_file,
             "--output_plot", plot_file,
             "--min_amplitude", str(min_amplitude)],
            ["python", "generated.py", "--duration", str(duration), 
             "--sampling-interval", str(sampling_interval),
             "--output-harmonics", harmonics_file,
             "--output-plot", plot_file,
             "--min-amplitude", str(min_amplitude)]
        ]
        
        result = None
        for cmd in cmd_variations:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    break
            except:
                continue
        
        if result is None or result.returncode != 0:
            print("FAIL: Script execution failed")
            print("SCORE: amplitude_accuracy: 0.0")
            print("SCORE: frequency_identification: 0.0")
            return
        
        # Test 1: Check if harmonics JSON file exists
        if os.path.exists(harmonics_file):
            print("PASS: Harmonics JSON file created")
            score += 1
        else:
            print("FAIL: Harmonics JSON file not created")
        
        # Test 2: Check if plot PNG file exists
        if os.path.exists(plot_file):
            print("PASS: Plot PNG file created")
            score += 1
        else:
            print("FAIL: Plot PNG file not created")
        
        # Load and validate JSON results
        try:
            with open(harmonics_file, 'r') as f:
                results = json.load(f)
            
            # Test 3: Check JSON structure
            if isinstance(results, list) and len(results) > 0:
                print("PASS: JSON contains list of results")
                score += 1
            else:
                print("FAIL: JSON structure invalid")
            
            # Test 4: Check required keys in results
            required_keys = ['constituent', 'period_hours', 'amplitude_m', 'phase_degrees']
            if all(all(key in item for key in required_keys) for item in results):
                print("PASS: All required keys present in results")
                score += 1
            else:
                print("FAIL: Missing required keys in results")
            
            # Test 5: Check amplitude filtering
            amplitudes = [item['amplitude_m'] for item in results]
            if all(amp >= min_amplitude for amp in amplitudes):
                print("PASS: Amplitude filtering applied correctly")
                score += 1
            else:
                print("FAIL: Amplitude filtering not applied correctly")
            
            # Test 6: Check for major tidal constituents
            found_constituents = [item['constituent'] for item in results]
            major_constituents = ['M2', 'S2']
            if any(const in found_constituents for const in major_constituents):
                print("PASS: Major tidal constituents identified")
                score += 1
            else:
                print("FAIL: Major tidal constituents not identified")
            
            # Test 7: Check period values are reasonable
            periods = [item['period_hours'] for item in results]
            if all(6 < p < 30 for p in periods):
                print("PASS: Period values are in reasonable range")
                score += 1
            else:
                print("FAIL: Period values outside reasonable range")
            
            # Test 8: Check amplitude values are positive
            if all(amp > 0 for amp in amplitudes):
                print("PASS: All amplitudes are positive")
                score += 1
            else:
                print("FAIL: Some amplitudes are not positive")
            
            # Test 9: Check phase values are in valid range
            phases = [item['phase_degrees'] for item in results]
            if all(-360 <= phase <= 360 for phase in phases):
                print("PASS: Phase values in valid range")
                score += 1
            else:
                print("FAIL: Phase values outside valid range")
            
            # Test 10: Check for duplicate constituents
            if len(found_constituents) == len(set(found_constituents)):
                print("PASS: No duplicate constituents")
                score += 1
            else:
                print("FAIL: Duplicate constituents found")
            
            # Calculate amplitude accuracy score
            known_constituents = create_data()
            amplitude_errors = []
            for result in results:
                const_name = result['constituent']
                if const_name in known_constituents:
                    expected_amp = known_constituents[const_name]['amplitude']
                    actual_amp = result['amplitude_m']
                    error = abs(expected_amp - actual_amp) / expected_amp
                    amplitude_errors.append(error)
            
            if amplitude_errors:
                amplitude_score = max(0, 1 - np.mean(amplitude_errors))
            
            # Calculate frequency identification score
            frequency_matches = 0
            for result in results:
                const_name = result['constituent']
                if const_name in known_constituents:
                    expected_period = known_constituents[const_name]['period']
                    actual_period = result['period_hours']
                    if abs(expected_period - actual_period) / expected_period < 0.1:
                        frequency_matches += 1
            
            if len(results) > 0:
                frequency_score = frequency_matches / len(known_constituents)
            
        except Exception as e:
            print(f"FAIL: Error reading JSON results: {e}")
        
        # Test 11: Check plot file size (should contain actual plot)
        try:
            plot_size = os.path.getsize(plot_file)
            if plot_size > 1000:  # At least 1KB
                print("PASS: Plot file has reasonable size")
                score += 1
            else:
                print("FAIL: Plot file too small")
        except:
            print("FAIL: Cannot check plot file size")
        
        # Test 12: Verify script handles different durations
        try:
            result2 = subprocess.run([
                "python", "generated.py", "--duration", "3",
                "--sampling_interval", "1.0",
                "--output_harmonics", "test2.json",
                "--output_plot", "test2.png",
                "--min_amplitude", "0.1"
            ], capture_output=True, text=True, timeout=30)
            
            if result2.returncode == 0 and os.path.exists("test2.json"):
                print("PASS: Script handles different parameters")
                score += 1
            else:
                print("FAIL: Script doesn't handle different parameters")
        except:
            print("FAIL: Script doesn't handle different parameters")
        
        # Test 13: Check for reasonable number of constituents
        try:
            if 1 <= len(results) <= 10:
                print("PASS: Reasonable number of constituents identified")
                score += 1
            else:
                print("FAIL: Unreasonable number of constituents")
        except:
            print("FAIL: Cannot check number of constituents")
        
        # Test 14: Verify JSON is properly formatted
        try:
            json_str = json.dumps(results, indent=2)
            if len(json_str) > 50:
                print("PASS: JSON properly formatted")
                score += 1
            else:
                print("FAIL: JSON not properly formatted")
        except:
            print("FAIL: JSON formatting error")
        
        # Test 15: Check constituent names are strings
        try:
            if all(isinstance(item['constituent'], str) for item in results):
                print("PASS: Constituent names are strings")
                score += 1
            else:
                print("FAIL: Constituent names not all strings")
        except:
            print("FAIL: Cannot check constituent name types")
    
    print(f"SCORE: amplitude_accuracy: {amplitude_score:.3f}")
    print(f"SCORE: frequency_identification: {frequency_score:.3f}")

if __name__ == "__main__":
    run_test()
