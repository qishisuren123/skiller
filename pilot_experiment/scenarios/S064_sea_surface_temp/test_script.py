import subprocess
import tempfile
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path

def create_data():
    """Generate synthetic SST data for testing"""
    np.random.seed(42)
    
    # Create realistic SST field with spatial patterns
    lat_grid, lon_grid = np.meshgrid(np.linspace(-60, 60, 50), np.linspace(-180, 180, 100))
    
    # Base temperature field with latitudinal gradient
    base_temp = 25 - 0.3 * np.abs(lat_grid) + np.random.normal(0, 2, lat_grid.shape)
    
    # Add some warm and cold anomaly regions
    warm_anomaly = 3 * np.exp(-((lat_grid - 10)**2 + (lon_grid - 50)**2) / 500)
    cold_anomaly = -2.5 * np.exp(-((lat_grid + 20)**2 + (lon_grid + 100)**2) / 300)
    
    sst_data = base_temp + warm_anomaly + cold_anomaly
    
    return sst_data, lat_grid, lon_grid

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        sst_data, lat_grid, lon_grid = create_data()
        
        # Save test data
        np.savetxt('sst_input.csv', sst_data, delimiter=',')
        
        # Test different argument name variations
        possible_args = [
            ['--input', 'sst_input.csv', '--output', 'results.json', '--anomaly-grid', 'anomalies.csv'],
            ['--input-file', 'sst_input.csv', '--output-file', 'results.json', '--anomaly-file', 'anomalies.csv'],
            ['-i', 'sst_input.csv', '-o', 'results.json', '--anomaly-output', 'anomalies.csv']
        ]
        
        success = False
        for args in possible_args:
            try:
                result = subprocess.run(['python', 'generated.py'] + args, 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            # Try with minimal args
            try:
                result = subprocess.run(['python', 'generated.py', 'sst_input.csv'], 
                                      capture_output=True, text=True, timeout=30)
                success = result.returncode == 0
            except:
                pass
        
        # Load results
        results_file = None
        anomaly_file = None
        
        for f in ['results.json', 'output.json', 'sst_results.json']:
            if os.path.exists(f):
                results_file = f
                break
                
        for f in ['anomalies.csv', 'anomaly_grid.csv', 'sst_anomalies.csv']:
            if os.path.exists(f):
                anomaly_file = f
                break
        
        # Test conditions
        tests_passed = 0
        total_tests = 13
        
        # Test 1: Script runs successfully
        if success:
            tests_passed += 1
            print("PASS: Script executed successfully")
        else:
            print("FAIL: Script failed to execute")
        
        # Test 2: JSON results file exists
        if results_file and os.path.exists(results_file):
            tests_passed += 1
            print("PASS: Results JSON file created")
        else:
            print("FAIL: Results JSON file not found")
            return tests_passed, total_tests, 0.0, 0.0
        
        # Test 3: Anomaly CSV file exists
        if anomaly_file and os.path.exists(anomaly_file):
            tests_passed += 1
            print("PASS: Anomaly CSV file created")
        else:
            print("FAIL: Anomaly CSV file not found")
        
        # Load and validate results
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
        except:
            print("FAIL: Could not load results JSON")
            return tests_passed, total_tests, 0.0, 0.0
        
        try:
            anomaly_data = pd.read_csv(anomaly_file, header=None).values
        except:
            print("FAIL: Could not load anomaly CSV")
            anomaly_data = None
        
        # Calculate expected values
        climatology = np.mean(sst_data)
        expected_anomalies = sst_data - climatology
        expected_mean_anomaly = np.mean(expected_anomalies)
        expected_std_anomaly = np.std(expected_anomalies)
        
        # Test 4: Mean anomaly is approximately zero
        if 'mean_anomaly' in results and abs(results['mean_anomaly']) < 1e-10:
            tests_passed += 1
            print("PASS: Mean anomaly is approximately zero")
        else:
            print("FAIL: Mean anomaly is not approximately zero")
        
        # Test 5: Standard deviation is reasonable
        if 'std_anomaly' in results and 0 < results['std_anomaly'] < 10:
            tests_passed += 1
            print("PASS: Standard deviation is reasonable")
        else:
            print("FAIL: Standard deviation is unreasonable")
        
        # Test 6: Climatology value exists and is reasonable
        if 'climatology' in results and 0 < results['climatology'] < 40:
            tests_passed += 1
            print("PASS: Climatology value is reasonable")
        else:
            print("FAIL: Climatology value is unreasonable")
        
        # Test 7: Percentage above 1°C threshold exists
        if 'percent_above_1C' in results and 0 <= results['percent_above_1C'] <= 100:
            tests_passed += 1
            print("PASS: Percentage above 1°C threshold is valid")
        else:
            print("FAIL: Percentage above 1°C threshold is invalid")
        
        # Test 8: Percentage above 2°C threshold exists
        if 'percent_above_2C' in results and 0 <= results['percent_above_2C'] <= 100:
            tests_passed += 1
            print("PASS: Percentage above 2°C threshold is valid")
        else:
            print("FAIL: Percentage above 2°C threshold is invalid")
        
        # Test 9: Maximum anomaly location exists
        if 'max_anomaly_location' in results and len(results['max_anomaly_location']) == 2:
            tests_passed += 1
            print("PASS: Maximum anomaly location is provided")
        else:
            print("FAIL: Maximum anomaly location is missing or invalid")
        
        # Test 10: Minimum anomaly location exists
        if 'min_anomaly_location' in results and len(results['min_anomaly_location']) == 2:
            tests_passed += 1
            print("PASS: Minimum anomaly location is provided")
        else:
            print("FAIL: Minimum anomaly location is missing or invalid")
        
        # Test 11: Anomaly grid has correct dimensions
        if anomaly_data is not None and anomaly_data.shape == sst_data.shape:
            tests_passed += 1
            print("PASS: Anomaly grid has correct dimensions")
        else:
            print("FAIL: Anomaly grid has incorrect dimensions")
        
        # Test 12: Anomaly values are reasonable
        if anomaly_data is not None and -10 < np.mean(anomaly_data) < 10:
            tests_passed += 1
            print("PASS: Anomaly values are reasonable")
        else:
            print("FAIL: Anomaly values are unreasonable")
        
        # Test 13: Threshold percentages are consistent
        if ('percent_above_1C' in results and 'percent_above_2C' in results and 
            results['percent_above_2C'] <= results['percent_above_1C']):
            tests_passed += 1
            print("PASS: Threshold percentages are consistent")
        else:
            print("FAIL: Threshold percentages are inconsistent")
        
        # Calculate scores
        accuracy_score = 0.0
        if anomaly_data is not None:
            # Compare computed anomalies with expected
            correlation = np.corrcoef(anomaly_data.flatten(), expected_anomalies.flatten())[0,1]
            accuracy_score = max(0, correlation) if not np.isnan(correlation) else 0.0
        
        completeness_score = 0.0
        required_keys = ['mean_anomaly', 'std_anomaly', 'climatology', 'percent_above_1C', 
                        'percent_above_2C', 'max_anomaly_location', 'min_anomaly_location']
        completeness_score = sum(1 for key in required_keys if key in results) / len(required_keys)
        
        print(f"SCORE: {accuracy_score:.3f}")
        print(f"SCORE: {completeness_score:.3f}")
        
        return tests_passed, total_tests, accuracy_score, completeness_score

if __name__ == "__main__":
    run_test()
