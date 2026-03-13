import os
import sys
import subprocess
import tempfile
import json
import csv
import numpy as np
import pandas as pd
from pathlib import Path

def create_data():
    """Generate synthetic Argo float profile data"""
    np.random.seed(42)
    
    # Create 5 profiles with different characteristics
    profiles = []
    
    for profile_id in range(1, 6):
        # Generate profile metadata
        lat = np.random.uniform(-60, 60)
        lon = np.random.uniform(-180, 180)
        
        # Generate pressure levels (0 to 2000 dbar)
        n_levels = np.random.randint(80, 120)
        pressure = np.sort(np.random.uniform(0, 2000, n_levels))
        pressure[0] = 5  # Ensure we have near-surface data
        
        # Generate realistic temperature profile (decreasing with depth)
        surface_temp = np.random.uniform(15, 28)
        temp_gradient = np.random.uniform(0.005, 0.015)
        temperature = surface_temp - temp_gradient * pressure + np.random.normal(0, 0.5, n_levels)
        
        # Generate realistic salinity profile
        surface_sal = np.random.uniform(34, 36)
        salinity = surface_sal + np.random.normal(0, 0.2, n_levels)
        
        # Add some missing values (NaN)
        missing_indices = np.random.choice(n_levels, size=int(0.05 * n_levels), replace=False)
        temperature[missing_indices] = np.nan
        salinity[missing_indices] = np.nan
        
        # Add some bad quality data
        if profile_id == 4:  # Make profile 4 poor quality
            bad_indices = np.random.choice(n_levels, size=int(0.6 * n_levels), replace=False)
            temperature[bad_indices] = np.nan
            salinity[bad_indices] = np.nan
        
        profile_data = {
            'profile_id': profile_id,
            'latitude': lat,
            'longitude': lon,
            'pressure': pressure.tolist(),
            'temperature': temperature.tolist(),
            'salinity': salinity.tolist()
        }
        profiles.append(profile_data)
    
    return profiles

def run_test():
    results = {'passed': 0, 'failed': 0, 'tests': []}
    
    def test_condition(condition, description):
        if condition:
            results['passed'] += 1
            results['tests'].append(f"PASS: {description}")
        else:
            results['failed'] += 1
            results['tests'].append(f"FAIL: {description}")
        return condition
    
    # Create test data
    test_data = create_data()
    
    # Save test data to JSON file
    data_file = 'argo_profiles.json'
    with open(data_file, 'w') as f:
        json.dump(test_data, f)
    
    # Define output files
    csv_output = 'profile_stats.csv'
    json_output = 'profile_analysis.json'
    
    # Test different argument name variations
    possible_args = [
        ['--input', data_file, '--csv-output', csv_output, '--json-output', json_output],
        ['--data', data_file, '--csv', csv_output, '--json', json_output],
        ['-i', data_file, '-c', csv_output, '-j', json_output],
        ['--input-file', data_file, '--output-csv', csv_output, '--output-json', json_output]
    ]
    
    script_ran = False
    for args in possible_args:
        try:
            result = subprocess.run([sys.executable, 'generated.py'] + args, 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                script_ran = True
                break
        except:
            continue
    
    test_condition(script_ran, "Script runs without errors")
    
    if not script_ran:
        # Print available files for debugging
        print("Available files:", os.listdir('.'))
        return results
    
    # Test output files exist
    csv_exists = test_condition(os.path.exists(csv_output), "CSV output file created")
    json_exists = test_condition(os.path.exists(json_output), "JSON output file created")
    
    if not (csv_exists and json_exists):
        return results
    
    # Load and test CSV output
    try:
        df = pd.read_csv(csv_output)
        test_condition(len(df) == 5, "CSV contains correct number of profiles")
        
        required_columns = ['profile_id', 'latitude', 'longitude', 'max_depth', 
                          'mixed_layer_depth', 'mean_temp_ml', 'mean_sal_ml', 'surface_density']
        csv_has_columns = all(col in df.columns for col in required_columns)
        test_condition(csv_has_columns, "CSV has all required columns")
        
        # Test mixed layer depth values are reasonable
        mld_reasonable = test_condition(
            df['mixed_layer_depth'].between(0, 500).all(),
            "Mixed layer depths are within reasonable range (0-500m)"
        )
        
        # Test surface density values
        density_reasonable = test_condition(
            df['surface_density'].between(1020, 1030).all(),
            "Surface density values are reasonable (1020-1030 kg/m³)"
        )
        
        # Test quality control - profile 4 should be flagged as poor quality
        if 'quality_flag' in df.columns:
            test_condition(
                df[df['profile_id'] == 4]['quality_flag'].iloc[0] == 'poor quality',
                "Poor quality profile correctly flagged"
            )
        
    except Exception as e:
        test_condition(False, f"CSV file readable and properly formatted: {e}")
    
    # Load and test JSON output
    try:
        with open(json_output, 'r') as f:
            json_data = json.load(f)
        
        test_condition(len(json_data) == 5, "JSON contains correct number of profiles")
        
        # Test JSON structure
        first_profile = json_data[0] if json_data else {}
        json_has_structure = all(key in first_profile for key in 
                               ['profile_id', 'density', 'valid_data_percentage'])
        test_condition(json_has_structure, "JSON has required structure with density data")
        
        # Test density calculations exist
        has_density = test_condition(
            'density' in first_profile and len(first_profile['density']) > 0,
            "Density calculations included in JSON output"
        )
        
        # Test valid data percentage calculation
        valid_pct_exists = test_condition(
            'valid_data_percentage' in first_profile,
            "Valid data percentage calculated"
        )
        
    except Exception as e:
        test_condition(False, f"JSON file readable and properly formatted: {e}")
    
    # Calculate scores
    try:
        # Score 1: Data processing accuracy (based on reasonable output values)
        processing_score = 0.0
        if csv_exists and os.path.exists(csv_output):
            df = pd.read_csv(csv_output)
            if len(df) == 5:
                processing_score += 0.4
            if df['mixed_layer_depth'].between(0, 500).all():
                processing_score += 0.3
            if df['surface_density'].between(1020, 1030).all():
                processing_score += 0.3
        
        results['tests'].append(f"SCORE: Data processing accuracy: {processing_score:.2f}")
        
        # Score 2: Output completeness
        completeness_score = 0.0
        if csv_exists:
            completeness_score += 0.4
        if json_exists:
            completeness_score += 0.4
        if csv_exists and json_exists:
            try:
                df = pd.read_csv(csv_output)
                with open(json_output, 'r') as f:
                    json_data = json.load(f)
                if len(df) == len(json_data) == 5:
                    completeness_score += 0.2
            except:
                pass
        
        results['tests'].append(f"SCORE: Output completeness: {completeness_score:.2f}")
        
    except Exception as e:
        results['tests'].append(f"SCORE: Data processing accuracy: 0.00")
        results['tests'].append(f"SCORE: Output completeness: 0.00")
    
    return results

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Copy the generated script to temp directory
        import shutil
        if os.path.exists('../generated.py'):
            shutil.copy('../generated.py', 'generated.py')
        elif os.path.exists('generated.py'):
            pass  # Already in correct location
        else:
            print("FAIL: generated.py not found")
            sys.exit(1)
        
        results = run_test()
        
        for test in results['tests']:
            print(test)
        
        print(f"\nSummary: {results['passed']} passed, {results['failed']} failed")
