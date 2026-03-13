import subprocess
import json
import pandas as pd
import numpy as np
import tempfile
import os
import sys
from pathlib import Path

def create_data():
    """Generate synthetic DSC data with known thermal events"""
    # This function creates the expected synthetic data parameters
    # The actual data generation should be done by the student's script
    return {
        'temp_range': (-50, 250),
        'heating_rate': 10.0,
        'num_points': 1000,
        'expected_peaks': [
            {'temp': 60, 'type': 'endothermic', 'magnitude': -15},
            {'temp': 120, 'type': 'exothermic', 'magnitude': 8},
            {'temp': 180, 'type': 'endothermic', 'magnitude': -25}
        ]
    }

def run_test():
    test_data = create_data()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Test cases with different argument variations
        test_cases = [
            {
                'args': [
                    '--temperature-range', '-50,250',
                    '--heating-rate', '10',
                    '--num-points', '1000',
                    '--baseline-method', 'linear',
                    '--sensitivity', '0.5',
                    '--output', 'results1.json'
                ],
                'output_file': 'results1.json'
            },
            {
                'args': [
                    '--temperature-range', '0,200',
                    '--heating-rate', '5',
                    '--num-points', '500',
                    '--baseline-method', 'polynomial',
                    '--sensitivity', '0.3',
                    '--output', 'results2.json'
                ],
                'output_file': 'results2.json'
            }
        ]
        
        results = []
        total_score = 0
        max_score = 0
        
        for i, test_case in enumerate(test_cases):
            print(f"\n=== Test Case {i+1} ===")
            
            try:
                # Run the generated script
                result = subprocess.run([
                    sys.executable, 'generated.py'
                ] + test_case['args'], 
                capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    print(f"FAIL: Script execution failed")
                    print(f"Error: {result.stderr}")
                    continue
                
                # Test 1: Check if output JSON file exists
                json_file = test_case['output_file']
                if os.path.exists(json_file):
                    print("PASS: Output JSON file created")
                    total_score += 1
                else:
                    print("FAIL: Output JSON file not created")
                max_score += 1
                
                # Test 2: Check if CSV file exists
                csv_files = list(Path('.').glob('*.csv'))
                if csv_files:
                    print("PASS: CSV data file created")
                    total_score += 1
                    csv_file = csv_files[0]
                else:
                    print("FAIL: CSV data file not created")
                    csv_file = None
                max_score += 1
                
                if os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        output_data = json.load(f)
                    
                    # Test 3: Check JSON structure
                    required_keys = ['processing_parameters', 'detected_peaks', 'baseline_correction']
                    if all(key in output_data for key in required_keys):
                        print("PASS: JSON contains required top-level keys")
                        total_score += 1
                    else:
                        print("FAIL: JSON missing required keys")
                    max_score += 1
                    
                    # Test 4: Check processing parameters
                    params = output_data.get('processing_parameters', {})
                    expected_temp_range = test_case['args'][1].split(',')
                    temp_min, temp_max = float(expected_temp_range[0]), float(expected_temp_range[1])
                    
                    if ('temperature_range' in params and 
                        'heating_rate' in params and 
                        'baseline_method' in params):
                        print("PASS: Processing parameters recorded")
                        total_score += 1
                    else:
                        print("FAIL: Processing parameters incomplete")
                    max_score += 1
                    
                    # Test 5: Check detected peaks structure
                    peaks = output_data.get('detected_peaks', [])
                    if isinstance(peaks, list) and len(peaks) > 0:
                        print("PASS: Peaks detected and stored as list")
                        total_score += 1
                    else:
                        print("FAIL: No peaks detected or wrong format")
                    max_score += 1
                    
                    # Test 6: Check peak properties
                    if peaks and isinstance(peaks[0], dict):
                        peak_keys = ['temperature', 'magnitude', 'onset', 'area', 'width']
                        if any(key in peaks[0] for key in peak_keys[:3]):  # At least basic properties
                            print("PASS: Peak properties include required fields")
                            total_score += 1
                        else:
                            print("FAIL: Peak properties missing required fields")
                    else:
                        print("FAIL: Peak data structure invalid")
                    max_score += 1
                    
                    # Test 7: Check baseline correction stats
                    baseline_stats = output_data.get('baseline_correction', {})
                    if 'r_squared' in baseline_stats or 'correction_range' in baseline_stats:
                        print("PASS: Baseline correction statistics provided")
                        total_score += 1
                    else:
                        print("FAIL: Baseline correction statistics missing")
                    max_score += 1
                
                # Test 8: Check CSV structure
                if csv_file and os.path.exists(csv_file):
                    try:
                        df = pd.read_csv(csv_file)
                        expected_cols = ['temperature', 'raw_heat_flow', 'corrected_heat_flow', 'baseline']
                        if any(col in df.columns for col in expected_cols[:2]):
                            print("PASS: CSV contains temperature and heat flow data")
                            total_score += 1
                        else:
                            print("FAIL: CSV missing required columns")
                    except Exception as e:
                        print(f"FAIL: Error reading CSV file: {e}")
                else:
                    print("FAIL: CSV file not accessible")
                max_score += 1
                
                # Test 9: Check data range consistency
                if csv_file and os.path.exists(csv_file):
                    try:
                        df = pd.read_csv(csv_file)
                        temp_col = None
                        for col in ['temperature', 'temp', 'T']:
                            if col in df.columns:
                                temp_col = col
                                break
                        
                        if temp_col is not None:
                            temp_range_actual = (df[temp_col].min(), df[temp_col].max())
                            expected_range = (temp_min, temp_max)
                            
                            if (abs(temp_range_actual[0] - expected_range[0]) < 10 and 
                                abs(temp_range_actual[1] - expected_range[1]) < 10):
                                print("PASS: Temperature range matches input parameters")
                                total_score += 1
                            else:
                                print("FAIL: Temperature range doesn't match parameters")
                        else:
                            print("FAIL: No temperature column found")
                    except:
                        print("FAIL: Error validating temperature range")
                else:
                    print("FAIL: Cannot validate temperature range")
                max_score += 1
                
                # Test 10: Check number of data points
                if csv_file and os.path.exists(csv_file):
                    try:
                        df = pd.read_csv(csv_file)
                        expected_points = int(test_case['args'][5])  # num_points argument
                        actual_points = len(df)
                        
                        if abs(actual_points - expected_points) <= expected_points * 0.1:  # 10% tolerance
                            print("PASS: Number of data points approximately correct")
                            total_score += 1
                        else:
                            print(f"FAIL: Expected ~{expected_points} points, got {actual_points}")
                    except:
                        print("FAIL: Error checking data points count")
                max_score += 1
                
                # Test 11: Validate baseline method was applied
                baseline_method = test_case['args'][7]  # baseline_method argument
                if os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        output_data = json.load(f)
                    
                    params = output_data.get('processing_parameters', {})
                    if params.get('baseline_method') == baseline_method:
                        print("PASS: Baseline method parameter recorded correctly")
                        total_score += 1
                    else:
                        print("FAIL: Baseline method not recorded correctly")
                else:
                    print("FAIL: Cannot verify baseline method")
                max_score += 1
                
                # Test 12: Check for reasonable peak detection
                if os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        output_data = json.load(f)
                    
                    peaks = output_data.get('detected_peaks', [])
                    if 1 <= len(peaks) <= 10:  # Reasonable number of peaks
                        print("PASS: Reasonable number of peaks detected")
                        total_score += 1
                    else:
                        print(f"FAIL: Unreasonable number of peaks: {len(peaks)}")
                max_score += 1
                
            except subprocess.TimeoutExpired:
                print("FAIL: Script execution timed out")
                max_score += 12  # Add all missed tests
            except Exception as e:
                print(f"FAIL: Unexpected error: {e}")
                max_score += 12
        
        # SCORE metrics
        if max_score > 0:
            completion_score = total_score / max_score
            print(f"\nSCORE: {completion_score:.3f}")
        else:
            print(f"\nSCORE: 0.000")
        
        # Calculate accuracy score based on peak detection quality
        accuracy_score = 0.0
        try:
            if os.path.exists('results1.json'):
                with open('results1.json', 'r') as f:
                    data = json.load(f)
                peaks = data.get('detected_peaks', [])
                
                # Score based on having detected some peaks with reasonable properties
                if len(peaks) > 0:
                    accuracy_score = min(1.0, len(peaks) / 3.0)  # Up to 3 peaks expected
                    
                    # Bonus for having proper peak properties
                    if peaks and isinstance(peaks[0], dict):
                        required_props = ['temperature', 'magnitude']
                        if all(prop in peaks[0] for prop in required_props):
                            accuracy_score = min(1.0, accuracy_score + 0.3)
        except:
            pass
        
        print(f"SCORE: {accuracy_score:.3f}")

if __name__ == "__main__":
    run_test()
