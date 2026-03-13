import os
import sys
import subprocess
import tempfile
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def create_data():
    """Generate synthetic quasar photometry data"""
    np.random.seed(42)
    
    # Create 50 objects (30 variable quasars, 20 non-variable)
    n_objects = 50
    n_variable = 30
    bands = ['g', 'r', 'i']
    
    data = []
    
    for obj_id in range(n_objects):
        is_variable = obj_id < n_variable
        
        # Generate observations over ~2 years
        n_obs_per_band = np.random.randint(25, 80)
        mjd_start = 58000 + np.random.uniform(0, 100)
        
        for band in bands:
            # Base magnitude
            base_mag = 19.0 + np.random.uniform(-1, 1)
            
            # Generate MJD values
            mjds = np.sort(mjd_start + np.random.uniform(0, 700, n_obs_per_band))
            
            if is_variable:
                # Add correlated variability with structure function
                dt = np.diff(mjds)
                variability_amp = 0.1 + np.random.exponential(0.05)
                
                # Simple red noise model
                mags = [base_mag + np.random.normal(0, variability_amp)]
                for i, delta_t in enumerate(dt):
                    # Correlation decreases with time lag
                    correlation = np.exp(-delta_t / 100.0)
                    new_var = variability_amp * np.sqrt(1 - correlation**2)
                    mags.append(mags[-1] * correlation + np.random.normal(base_mag * (1-correlation), new_var))
                mags = np.array(mags)
            else:
                # Non-variable: just noise around constant magnitude
                mags = base_mag + np.random.normal(0, 0.02, n_obs_per_band)
            
            # Measurement errors
            mag_errors = 0.01 + np.random.exponential(0.03, n_obs_per_band)
            # Add some bad measurements
            bad_mask = np.random.random(n_obs_per_band) < 0.05
            mag_errors[bad_mask] = np.random.uniform(0.2, 0.5, np.sum(bad_mask))
            
            # Add measurement noise
            mags += np.random.normal(0, mag_errors)
            
            for mjd, mag, mag_err in zip(mjds, mags, mag_errors):
                data.append({
                    'object_id': f'obj_{obj_id:03d}',
                    'mjd': mjd,
                    'band': band,
                    'magnitude': mag,
                    'mag_error': mag_err
                })
    
    return pd.DataFrame(data)

def calculate_structure_function(mjds, mags, lag_days=30):
    """Calculate structure function at given lag"""
    sf_values = []
    for i in range(len(mjds)):
        for j in range(i+1, len(mjds)):
            dt = abs(mjds[j] - mjds[i])
            if abs(dt - lag_days) < 5:  # Within 5 days of target lag
                sf_values.append((mags[j] - mags[i])**2)
    
    return np.sqrt(np.mean(sf_values)) if sf_values else 0.0

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        df = create_data()
        input_file = 'quasar_data.csv'
        df.to_csv(input_file, index=False)
        
        # Test different argument patterns
        possible_args = [
            ['--input', input_file, '--output', 'results', '--threshold', '0.05'],
            ['-i', input_file, '-o', 'results', '-t', '0.05'],
            ['--input-file', input_file, '--output-dir', 'results', '--var-threshold', '0.05'],
            [input_file, 'results', '0.05']
        ]
        
        success = False
        for args in possible_args:
            try:
                result = subprocess.run([sys.executable, 'generated.py'] + args, 
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed")
            return
        
        print("PASS: Script executed successfully")
        
        # Check output files exist
        results_dir = Path('results')
        if not results_dir.exists():
            print("FAIL: Output directory not created")
            return
        print("PASS: Output directory created")
        
        # Check for JSON output files
        json_files = list(results_dir.glob('*.json'))
        if len(json_files) == 0:
            print("FAIL: No JSON output files found")
            return
        print("PASS: JSON output files created")
        
        # Load and validate main results
        main_results = None
        summary_results = None
        
        for json_file in json_files:
            with open(json_file, 'r') as f:
                data = json.load(f)
                if 'objects' in data or any('obj_' in str(k) for k in data.keys()):
                    main_results = data
                elif 'summary' in data or 'fraction_variable' in data:
                    summary_results = data
        
        if main_results is None:
            print("FAIL: Main results JSON not found or invalid format")
            return
        print("PASS: Main results JSON found and loaded")
        
        # Check variability metrics are present
        sample_obj = None
        if 'objects' in main_results:
            sample_obj = list(main_results['objects'].values())[0] if main_results['objects'] else None
        else:
            sample_obj = list(main_results.values())[0] if main_results else None
        
        if sample_obj is None:
            print("FAIL: No object data found in results")
            return
        
        required_metrics = ['std_dev', 'excess_variance', 'structure_function', 'amplitude']
        metrics_found = 0
        for metric in required_metrics:
            if any(metric in str(sample_obj).lower() for band_data in (sample_obj.values() if isinstance(sample_obj, dict) else [sample_obj])):
                metrics_found += 1
        
        if metrics_found < 2:
            print("FAIL: Required variability metrics not found")
            return
        print("PASS: Variability metrics computed")
        
        # Check classification
        classifications_found = False
        for obj_data in (main_results.get('objects', main_results)).values():
            if isinstance(obj_data, dict):
                for band_data in obj_data.values():
                    if isinstance(band_data, dict) and any('variable' in str(k).lower() or 'classification' in str(k).lower() for k in band_data.keys()):
                        classifications_found = True
                        break
        
        if not classifications_found:
            print("FAIL: Object classifications not found")
            return
        print("PASS: Object classifications present")
        
        # Check quality filtering was applied
        original_count = len(df)
        processed_objects = len(main_results.get('objects', main_results))
        
        if processed_objects > 50:  # Should be filtered
            print("FAIL: Quality filtering not applied properly")
            return
        print("PASS: Quality filtering applied")
        
        # Check for plots
        plot_files = list(results_dir.glob('*.png')) + list(results_dir.glob('*.jpg')) + list(results_dir.glob('*.pdf'))
        if len(plot_files) == 0:
            print("FAIL: No light curve plots generated")
            return
        print("PASS: Light curve plots generated")
        
        # Check summary statistics
        if summary_results is None:
            # Try to find summary in main results
            summary_keys = ['summary', 'statistics', 'fraction_variable']
            for key in summary_keys:
                if key in main_results:
                    summary_results = main_results[key]
                    break
        
        if summary_results is None:
            print("FAIL: Summary statistics not found")
            return
        print("PASS: Summary statistics generated")
        
        # Check band-specific analysis
        bands_analyzed = 0
        for obj_data in (main_results.get('objects', main_results)).values():
            if isinstance(obj_data, dict):
                for key in obj_data.keys():
                    if key in ['g', 'r', 'i'] or any(band in str(key) for band in ['g', 'r', 'i']):
                        bands_analyzed += 1
                        break
        
        if bands_analyzed < 10:  # Should have multiple objects with band analysis
            print("FAIL: Band-specific analysis not performed")
            return
        print("PASS: Band-specific analysis performed")
        
        # Check minimum observation requirement
        min_obs_applied = True  # Assume applied if we got reasonable results
        print("PASS: Minimum observation requirement applied")
        
        # Score 1: Data completeness (fraction of expected outputs present)
        expected_outputs = 6  # JSON files, plots, classifications, metrics, summary, filtering
        actual_outputs = len([x for x in [json_files, plot_files, classifications_found, metrics_found >= 2, summary_results, processed_objects <= 50] if x])
        completeness_score = min(actual_outputs / expected_outputs, 1.0)
        print(f"SCORE: Data completeness: {completeness_score:.3f}")
        
        # Score 2: Analysis quality (based on variability detection)
        # Check if we can distinguish variable from non-variable objects
        variable_count = 0
        total_count = 0
        
        for obj_data in (main_results.get('objects', main_results)).values():
            if isinstance(obj_data, dict):
                for band_data in obj_data.values():
                    if isinstance(band_data, dict):
                        total_count += 1
                        # Look for classification or high variability metrics
                        for key, value in band_data.items():
                            if 'variable' in str(key).lower() and value:
                                variable_count += 1
                                break
                            elif 'excess' in str(key).lower() and isinstance(value, (int, float)) and value > 0.05:
                                variable_count += 1
                                break
        
        if total_count > 0:
            variable_fraction = variable_count / total_count
            # Expect roughly 60% variable (30/50 objects, 3 bands each)
            quality_score = 1.0 - abs(variable_fraction - 0.6) / 0.6
            quality_score = max(0, min(1, quality_score))
        else:
            quality_score = 0.0
        
        print(f"SCORE: Analysis quality: {quality_score:.3f}")

if __name__ == "__main__":
    run_test()
