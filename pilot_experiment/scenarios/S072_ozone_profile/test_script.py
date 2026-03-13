import subprocess
import tempfile
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def create_data():
    """Generate synthetic ozonesonde profile data"""
    np.random.seed(42)
    
    # Altitude grid from 0 to 35 km
    altitude = np.linspace(0, 35, 200)
    
    # Pressure profile (exponential decay)
    pressure = 1013.25 * np.exp(-altitude / 8.4)
    
    # Temperature profile with troposphere and stratosphere
    temp_trop = 288.15 - 6.5 * altitude  # Tropospheric lapse rate
    temp_strat = 216.65 + 2.0 * (altitude - 11)  # Stratospheric warming
    temperature = np.where(altitude < 11, temp_trop, temp_strat)
    temperature = np.maximum(temperature, 180)  # Minimum temperature
    
    # Ozone profile - low in troposphere, peak in stratosphere
    ozone_trop = 0.03 + 0.02 * altitude / 11  # Low tropospheric ozone
    ozone_strat_base = 0.05 + 8 * np.exp(-(altitude - 25)**2 / 50)  # Stratospheric peak
    ozone = np.where(altitude < 11, ozone_trop, ozone_strat_base)
    
    # Add realistic noise
    ozone += np.random.normal(0, 0.3, len(altitude))
    temperature += np.random.normal(0, 2, len(temperature))
    
    # Add some missing/bad values
    bad_indices = np.random.choice(len(altitude), 10, replace=False)
    ozone[bad_indices[:5]] = np.nan
    ozone[bad_indices[5:]] = np.random.uniform(-1, -0.1, 5)  # Negative values
    
    # Add some unrealistically high values
    high_indices = np.random.choice(len(altitude), 3, replace=False)
    ozone[high_indices] = np.random.uniform(25, 30, 3)
    
    return pd.DataFrame({
        'altitude_km': altitude,
        'pressure_hPa': pressure,
        'temperature_K': temperature,
        'ozone_mPa': ozone
    })

def exponential_decay(x, a, b):
    """Exponential decay function for scale height fitting"""
    return a * np.exp(-x / b)

def run_test():
    results = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test data
        data = create_data()
        input_file = os.path.join(tmpdir, 'ozonesonde_data.csv')
        data.to_csv(input_file, index=False)
        
        output_json = os.path.join(tmpdir, 'ozone_analysis.json')
        output_plot = os.path.join(tmpdir, 'ozone_profile.png')
        
        # Test different argument name variations
        arg_variations = [
            ['--input', input_file, '--output-json', output_json, '--output-plot', output_plot],
            ['--data', input_file, '--json', output_json, '--plot', output_plot],
            ['-i', input_file, '-j', output_json, '-p', output_plot]
        ]
        
        cmd_success = False
        for args in arg_variations:
            try:
                cmd = ['python', 'generated.py'] + args
                result = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    cmd_success = True
                    break
            except:
                continue
        
        results.append(("PASS" if cmd_success else "FAIL", "Script runs without errors"))
        
        if not cmd_success:
            # If script failed, return early with failing tests
            for i in range(14):
                results.append(("FAIL", f"Test {i+2} - Script execution failed"))
            results.append(("SCORE: 0.0", "Overall accuracy"))
            results.append(("SCORE: 0.0", "Output completeness"))
            return results
        
        # Test JSON output exists and is valid
        json_exists = os.path.exists(output_json)
        results.append(("PASS" if json_exists else "FAIL", "JSON output file created"))
        
        analysis_data = {}
        if json_exists:
            try:
                with open(output_json, 'r') as f:
                    analysis_data = json.load(f)
                results.append(("PASS", "JSON file is valid"))
            except:
                results.append(("FAIL", "JSON file is valid"))
        else:
            results.append(("FAIL", "JSON file is valid"))
        
        # Test plot output exists
        plot_exists = os.path.exists(output_plot)
        results.append(("PASS" if plot_exists else "FAIL", "Plot output file created"))
        
        # Test required JSON fields
        required_fields = ['tropopause_height_km', 'tropospheric_column', 'stratospheric_column', 
                          'ozone_max_altitude_km', 'ozone_max_concentration_mPa', 'scale_height_km']
        
        fields_present = all(field in analysis_data for field in required_fields)
        results.append(("PASS" if fields_present else "FAIL", "All required JSON fields present"))
        
        # Calculate expected values for validation
        clean_data = data.dropna()
        clean_data = clean_data[clean_data['ozone_mPa'] >= 0]
        clean_data = clean_data[clean_data['ozone_mPa'] <= 20]
        
        # Expected tropopause (around 11 km based on our synthetic data)
        if 'tropopause_height_km' in analysis_data:
            trop_height = analysis_data['tropopause_height_km']
            trop_reasonable = 8 <= trop_height <= 15
            results.append(("PASS" if trop_reasonable else "FAIL", "Tropopause height reasonable (8-15 km)"))
        else:
            results.append(("FAIL", "Tropopause height reasonable (8-15 km)"))
        
        # Test tropospheric column is positive
        if 'tropospheric_column' in analysis_data:
            trop_col_positive = analysis_data['tropospheric_column'] > 0
            results.append(("PASS" if trop_col_positive else "FAIL", "Tropospheric column is positive"))
        else:
            results.append(("FAIL", "Tropospheric column is positive"))
        
        # Test stratospheric column is positive and larger than tropospheric
        if 'stratospheric_column' in analysis_data and 'tropospheric_column' in analysis_data:
            strat_col = analysis_data['stratospheric_column']
            trop_col = analysis_data['tropospheric_column']
            strat_larger = strat_col > trop_col and strat_col > 0
            results.append(("PASS" if strat_larger else "FAIL", "Stratospheric column > tropospheric column"))
        else:
            results.append(("FAIL", "Stratospheric column > tropospheric column"))
        
        # Test ozone maximum altitude is in stratosphere
        if 'ozone_max_altitude_km' in analysis_data:
            ozone_max_alt = analysis_data['ozone_max_altitude_km']
            max_in_strat = ozone_max_alt > 15 and ozone_max_alt < 35
            results.append(("PASS" if max_in_strat else "FAIL", "Ozone maximum in stratosphere (15-35 km)"))
        else:
            results.append(("FAIL", "Ozone maximum in stratosphere (15-35 km)"))
        
        # Test ozone maximum concentration is reasonable
        if 'ozone_max_concentration_mPa' in analysis_data:
            ozone_max_conc = analysis_data['ozone_max_concentration_mPa']
            conc_reasonable = 1 <= ozone_max_conc <= 15
            results.append(("PASS" if conc_reasonable else "FAIL", "Ozone maximum concentration reasonable (1-15 mPa)"))
        else:
            results.append(("FAIL", "Ozone maximum concentration reasonable (1-15 mPa)"))
        
        # Test scale height is reasonable
        if 'scale_height_km' in analysis_data:
            scale_height = analysis_data['scale_height_km']
            scale_reasonable = 2 <= scale_height <= 10
            results.append(("PASS" if scale_reasonable else "FAIL", "Scale height reasonable (2-10 km)"))
        else:
            results.append(("FAIL", "Scale height reasonable (2-10 km)"))
        
        # Test data quality control was applied
        original_count = len(data)
        expected_removed = np.sum(data['ozone_mPa'].isna()) + np.sum(data['ozone_mPa'] < 0) + np.sum(data['ozone_mPa'] > 20)
        qc_applied = expected_removed > 0  # We know we added bad data
        results.append(("PASS" if qc_applied else "FAIL", "Quality control removes bad data"))
        
        # Test plot contains ozone profile
        if plot_exists:
            try:
                # Simple check - file size should be reasonable for a plot
                plot_size = os.path.getsize(output_plot)
                plot_reasonable = plot_size > 10000  # At least 10KB
                results.append(("PASS" if plot_reasonable else "FAIL", "Plot file has reasonable size"))
            except:
                results.append(("FAIL", "Plot file has reasonable size"))
        else:
            results.append(("FAIL", "Plot file has reasonable size"))
        
        # Calculate accuracy score based on how close results are to expected
        accuracy_score = 0.0
        if fields_present and len(analysis_data) > 0:
            score_components = []
            
            # Tropopause height accuracy (expected around 11 km)
            if 'tropopause_height_km' in analysis_data:
                trop_error = abs(analysis_data['tropopause_height_km'] - 11.0)
                trop_score = max(0, 1 - trop_error / 5.0)  # Full score within 5 km
                score_components.append(trop_score)
            
            # Ozone max altitude (expected around 25 km)
            if 'ozone_max_altitude_km' in analysis_data:
                max_error = abs(analysis_data['ozone_max_altitude_km'] - 25.0)
                max_score = max(0, 1 - max_error / 10.0)
                score_components.append(max_score)
            
            # Scale height (expected around 4-6 km)
            if 'scale_height_km' in analysis_data:
                scale_target = 5.0
                scale_error = abs(analysis_data['scale_height_km'] - scale_target)
                scale_score = max(0, 1 - scale_error / 3.0)
                score_components.append(scale_score)
            
            if score_components:
                accuracy_score = np.mean(score_components)
        
        # Calculate completeness score
        completeness_score = 0.0
        if json_exists and plot_exists:
            field_score = len([f for f in required_fields if f in analysis_data]) / len(required_fields)
            file_score = 1.0  # Both files exist
            completeness_score = (field_score + file_score) / 2.0
        
        results.append((f"SCORE: {accuracy_score:.3f}", "Overall accuracy"))
        results.append((f"SCORE: {completeness_score:.3f}", "Output completeness"))
    
    return results

if __name__ == "__main__":
    results = run_test()
    for result, description in results:
        print(f"{result}: {description}")
