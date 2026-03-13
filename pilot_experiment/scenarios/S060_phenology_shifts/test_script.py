import os
import sys
import tempfile
import subprocess
import json
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

def create_data():
    """Generate synthetic phenological time series with known shifts"""
    np.random.seed(42)
    
    # Create 50-year time series with two distinct periods
    years = np.arange(1970, 2020)
    n_years = len(years)
    
    # Base phenological timing (day of year) with gradual shift
    base_doy = 120  # Early May
    
    # Create shift at year 1995 (index 25)
    shift_year = 1995
    shift_idx = 25
    
    # Early period: stable timing with small trend
    early_doy = base_doy + np.random.normal(0, 5, shift_idx) + 0.1 * np.arange(shift_idx)
    
    # Late period: shifted timing with different trend
    late_doy = base_doy - 15 + np.random.normal(0, 4, n_years - shift_idx) - 0.3 * np.arange(n_years - shift_idx)
    
    doy_values = np.concatenate([early_doy, late_doy])
    
    # Add some missing values
    missing_indices = np.random.choice(n_years, size=3, replace=False)
    doy_values[missing_indices] = np.nan
    
    # Generate correlated climate data
    temp_anomaly = np.random.normal(0, 1.5, n_years)
    temp_anomaly[shift_idx:] += 1.2  # Warming trend
    
    precip_anomaly = np.random.normal(0, 20, n_years)
    
    # Create correlation with temperature (negative - earlier with warming)
    for i in range(1, n_years):
        if not np.isnan(doy_values[i]):
            doy_values[i] += -0.8 * temp_anomaly[i] + 0.02 * precip_anomaly[i]
    
    # Create DataFrame
    data = pd.DataFrame({
        'year': years,
        'doy': doy_values,
        'temperature_anomaly': temp_anomaly,
        'precipitation_anomaly': precip_anomaly
    })
    
    return data

def run_test():
    results = {'passed': 0, 'failed': 0, 'tests': []}
    
    def test_condition(name, condition, error_msg=""):
        if condition:
            results['passed'] += 1
            results['tests'].append(f"PASS: {name}")
            return True
        else:
            results['failed'] += 1
            results['tests'].append(f"FAIL: {name} - {error_msg}")
            return False
    
    # Create test data
    test_data = create_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save test data
        data_file = os.path.join(tmpdir, 'phenology_data.csv')
        test_data.to_csv(data_file, index=False)
        
        output_file = os.path.join(tmpdir, 'analysis_results.json')
        plot_file = os.path.join(tmpdir, 'phenology_plot.png')
        
        # Test different argument name variations
        possible_args = [
            ['--input', data_file, '--output', output_file, '--plot', plot_file],
            ['--data', data_file, '--results', output_file, '--visualization', plot_file],
            ['-i', data_file, '-o', output_file, '-p', plot_file],
            ['--input_file', data_file, '--output_file', output_file, '--plot_file', plot_file]
        ]
        
        success = False
        for args in possible_args:
            try:
                result = subprocess.run([sys.executable, 'generated.py'] + args, 
                                      capture_output=True, text=True, cwd=tmpdir, timeout=60)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        test_condition("Script execution", success, "Script failed to run with any argument variation")
        
        if not success:
            for test_name in ["Output file creation", "JSON structure", "Data processing", 
                            "Trend detection", "Climate correlation", "Statistical testing",
                            "Breakpoint analysis", "Plot generation", "Missing value handling",
                            "Outlier detection", "Change-point detection", "Significance testing",
                            "Multiple comparison correction", "Lag analysis"]:
                test_condition(test_name, False, "Script execution failed")
            
            # Score metrics
            results['tests'].append("SCORE: 0.0")
            results['tests'].append("SCORE: 0.0")
            return results
        
        # Test 1: Output file creation
        test_condition("Output file creation", os.path.exists(output_file))
        
        # Load results if available
        analysis_results = {}
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    analysis_results = json.load(f)
            except:
                pass
        
        # Test 2: JSON structure validation
        required_keys = ['change_points', 'trend_analysis', 'climate_correlations', 'statistical_tests']
        has_structure = all(key in analysis_results for key in required_keys)
        test_condition("JSON structure", has_structure, f"Missing keys: {[k for k in required_keys if k not in analysis_results]}")
        
        # Test 3: Data processing verification
        processed_data_points = len(test_data.dropna())
        data_processed = 'n_observations' in analysis_results and analysis_results.get('n_observations', 0) > 40
        test_condition("Data processing", data_processed, "Insufficient data points processed")
        
        # Test 4: Trend detection
        has_trends = 'trend_analysis' in analysis_results and len(analysis_results.get('trend_analysis', {})) > 0
        test_condition("Trend detection", has_trends, "No trend analysis found")
        
        # Test 5: Climate correlation analysis
        has_climate_corr = ('climate_correlations' in analysis_results and 
                           'temperature' in str(analysis_results.get('climate_correlations', {})))
        test_condition("Climate correlation", has_climate_corr, "Climate correlation analysis missing")
        
        # Test 6: Statistical significance testing
        has_stats = ('statistical_tests' in analysis_results and 
                    'p_values' in str(analysis_results.get('statistical_tests', {})))
        test_condition("Statistical testing", has_stats, "Statistical significance tests missing")
        
        # Test 7: Change-point detection
        has_changepoints = ('change_points' in analysis_results and 
                           len(analysis_results.get('change_points', [])) > 0)
        test_condition("Change-point detection", has_changepoints, "No change-points detected")
        
        # Test 8: Plot generation
        test_condition("Plot generation", os.path.exists(plot_file), "Visualization plot not created")
        
        # Test 9: Multiple comparison correction
        has_correction = 'multiple_comparison_correction' in str(analysis_results)
        test_condition("Multiple comparison correction", has_correction, "Multiple comparison correction not applied")
        
        # Test 10: Breakpoint analysis
        has_breakpoints = 'breakpoint' in str(analysis_results) or 'change_point' in str(analysis_results)
        test_condition("Breakpoint analysis", has_breakpoints, "Breakpoint analysis missing")
        
        # Test 11: Missing value handling
        original_missing = test_data['doy'].isna().sum()
        handles_missing = 'missing_values' in str(analysis_results) or data_processed
        test_condition("Missing value handling", handles_missing, "Missing values not properly handled")
        
        # Test 12: Lag analysis
        has_lag_analysis = 'lag' in str(analysis_results).lower()
        test_condition("Lag analysis", has_lag_analysis, "Lag analysis for climate effects missing")
        
        # Test 13: Confidence intervals
        has_confidence = 'confidence' in str(analysis_results) or 'ci' in str(analysis_results)
        test_condition("Confidence intervals", has_confidence, "Confidence intervals not calculated")
        
        # Test 14: Correlation methods
        has_multiple_corr = ('pearson' in str(analysis_results).lower() or 
                            'spearman' in str(analysis_results).lower())
        test_condition("Multiple correlation methods", has_multiple_corr, "Multiple correlation methods not used")
        
        # Score 1: Analysis completeness (0-1)
        completeness_score = 0.0
        if analysis_results:
            score_components = [
                'change_points' in analysis_results,
                'trend_analysis' in analysis_results,
                'climate_correlations' in analysis_results,
                'statistical_tests' in analysis_results,
                has_changepoints,
                has_stats,
                has_climate_corr
            ]
            completeness_score = sum(score_components) / len(score_components)
        
        results['tests'].append(f"SCORE: {completeness_score:.3f}")
        
        # Score 2: Detection accuracy (0-1)
        detection_score = 0.0
        if has_changepoints and analysis_results:
            # Check if detected change-point is near the true shift (1995, index 25)
            change_points = analysis_results.get('change_points', [])
            if change_points:
                # Look for change-point near 1995
                detected_years = []
                for cp in change_points:
                    if isinstance(cp, dict) and 'year' in cp:
                        detected_years.append(cp['year'])
                    elif isinstance(cp, (int, float)):
                        detected_years.append(cp)
                
                if detected_years:
                    closest_detection = min(detected_years, key=lambda x: abs(x - 1995))
                    if abs(closest_detection - 1995) <= 5:  # Within 5 years
                        detection_score = max(0, 1.0 - abs(closest_detection - 1995) / 10.0)
        
        results['tests'].append(f"SCORE: {detection_score:.3f}")
    
    return results

if __name__ == "__main__":
    results = run_test()
    
    for test in results['tests']:
        print(test)
    
    print(f"\nSummary: {results['passed']} passed, {results['failed']} failed")
