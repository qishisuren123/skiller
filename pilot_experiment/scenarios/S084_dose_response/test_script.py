import os
import tempfile
import subprocess
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import shutil

def create_data():
    """Generate synthetic dose-response data"""
    np.random.seed(42)
    
    # Generate concentrations (log-spaced from 0.001 to 1000 µM)
    concentrations = np.logspace(-3, 3, 20)
    
    # True parameters for 4PL model
    true_ic50 = 10.0
    true_hill = -1.2
    true_top = 95.0
    true_bottom = 5.0
    
    # Generate responses with noise
    log_conc = np.log10(concentrations)
    true_response = true_bottom + (true_top - true_bottom) / (1 + (concentrations/true_ic50)**true_hill)
    
    # Add noise
    noise = np.random.normal(0, 3, len(true_response))
    responses = true_response + noise
    
    # Add some invalid data points for testing validation
    concentrations = np.append(concentrations, [-1, 0, np.inf])
    responses = np.append(responses, [50, -10, 150])
    
    # Create DataFrame
    df = pd.DataFrame({
        'concentration': concentrations,
        'response': responses
    })
    
    return df, true_ic50, true_hill, true_top, true_bottom

def test_dose_response_analysis():
    results = []
    scores = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test data
        df, true_ic50, true_hill, true_top, true_bottom = create_data()
        
        # Save input data
        input_file = os.path.join(temp_dir, "dose_data.csv")
        df.to_csv(input_file, index=False)
        
        # Create output directory
        output_dir = os.path.join(temp_dir, "results")
        os.makedirs(output_dir, exist_ok=True)
        
        # Test different argument name variations
        arg_variations = [
            ["--input", input_file, "--output", output_dir],
            ["-i", input_file, "-o", output_dir],
            ["--input_file", input_file, "--output_dir", output_dir],
        ]
        
        success = False
        for args in arg_variations:
            try:
                result = subprocess.run(
                    ["python", "generated.py"] + args,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        # Test 1: Script runs successfully
        if success:
            results.append("PASS: Script executed successfully")
        else:
            results.append("FAIL: Script failed to execute")
            return results, [0.0, 0.0]
        
        # Test 2: JSON results file exists
        json_file = os.path.join(output_dir, "fit_results.json")
        if os.path.exists(json_file):
            results.append("PASS: fit_results.json created")
            try:
                with open(json_file, 'r') as f:
                    fit_results = json.load(f)
            except:
                results.append("FAIL: fit_results.json is not valid JSON")
                return results, [0.0, 0.0]
        else:
            results.append("FAIL: fit_results.json not found")
            return results, [0.0, 0.0]
        
        # Test 3: Plot file exists
        plot_file = os.path.join(output_dir, "dose_response_curve.png")
        if os.path.exists(plot_file):
            results.append("PASS: dose_response_curve.png created")
        else:
            results.append("FAIL: dose_response_curve.png not found")
        
        # Test 4: JSON contains required parameters
        required_params = ['IC50', 'hill_slope', 'r_squared', 'data_points_used']
        missing_params = [p for p in required_params if p not in fit_results]
        if not missing_params:
            results.append("PASS: All required parameters in JSON")
        else:
            results.append(f"FAIL: Missing parameters: {missing_params}")
        
        # Test 5: IC50 value is reasonable
        if 'IC50' in fit_results:
            ic50_value = fit_results['IC50']
            if isinstance(ic50_value, (int, float)) and 1 < ic50_value < 100:
                results.append("PASS: IC50 value is reasonable")
            else:
                results.append(f"FAIL: IC50 value unreasonable: {ic50_value}")
        else:
            results.append("FAIL: IC50 not found in results")
        
        # Test 6: Hill slope is negative (for inhibition curve)
        if 'hill_slope' in fit_results:
            hill_value = fit_results['hill_slope']
            if isinstance(hill_value, (int, float)) and hill_value < 0:
                results.append("PASS: Hill slope is negative")
            else:
                results.append(f"FAIL: Hill slope should be negative: {hill_value}")
        else:
            results.append("FAIL: Hill slope not found in results")
        
        # Test 7: R-squared indicates good fit
        if 'r_squared' in fit_results:
            r2_value = fit_results['r_squared']
            if isinstance(r2_value, (int, float)) and r2_value > 0.8:
                results.append("PASS: R-squared indicates good fit")
            else:
                results.append(f"FAIL: R-squared too low: {r2_value}")
        else:
            results.append("FAIL: R-squared not found in results")
        
        # Test 8: Data filtering occurred
        if 'data_points_used' in fit_results:
            points_used = fit_results['data_points_used']
            if isinstance(points_used, int) and points_used == 20:  # Should filter out 3 invalid points
                results.append("PASS: Correct number of data points used")
            else:
                results.append(f"FAIL: Expected 20 data points, got: {points_used}")
        else:
            results.append("FAIL: Data points used not reported")
        
        # Test 9: Top plateau parameter exists and is reasonable
        if 'top' in fit_results or 'top_plateau' in fit_results:
            top_key = 'top' if 'top' in fit_results else 'top_plateau'
            top_value = fit_results[top_key]
            if isinstance(top_value, (int, float)) and 80 < top_value < 100:
                results.append("PASS: Top plateau value is reasonable")
            else:
                results.append(f"FAIL: Top plateau unreasonable: {top_value}")
        else:
            results.append("FAIL: Top plateau parameter not found")
        
        # Test 10: Bottom plateau parameter exists and is reasonable
        if 'bottom' in fit_results or 'bottom_plateau' in fit_results:
            bottom_key = 'bottom' if 'bottom' in fit_results else 'bottom_plateau'
            bottom_value = fit_results[bottom_key]
            if isinstance(bottom_value, (int, float)) and 0 < bottom_value < 20:
                results.append("PASS: Bottom plateau value is reasonable")
            else:
                results.append(f"FAIL: Bottom plateau unreasonable: {bottom_value}")
        else:
            results.append("FAIL: Bottom plateau parameter not found")
        
        # Test 11: Plot file is valid image
        try:
            img = plt.imread(plot_file)
            if img.shape[0] > 100 and img.shape[1] > 100:  # Reasonable image size
                results.append("PASS: Plot file is valid image")
            else:
                results.append("FAIL: Plot file too small")
        except:
            results.append("FAIL: Plot file is not a valid image")
        
        # Test 12: Confidence intervals provided
        ci_params = ['IC50_ci', 'hill_slope_ci', 'IC50_confidence_interval', 'hill_confidence_interval']
        has_ci = any(param in fit_results for param in ci_params)
        if has_ci:
            results.append("PASS: Confidence intervals provided")
        else:
            results.append("FAIL: No confidence intervals found")
        
        # Test 13: Script handles log transformation correctly
        if 'IC50' in fit_results:
            # IC50 should be close to true value (within 2-fold)
            ic50_ratio = fit_results['IC50'] / true_ic50
            if 0.5 < ic50_ratio < 2.0:
                results.append("PASS: IC50 estimation accuracy good")
            else:
                results.append(f"FAIL: IC50 estimation poor, ratio: {ic50_ratio}")
        
        # Test 14: JSON structure is well-formed
        try:
            json_str = json.dumps(fit_results, indent=2)
            if len(json_str) > 100:  # Reasonable amount of data
                results.append("PASS: JSON output is well-structured")
            else:
                results.append("FAIL: JSON output too minimal")
        except:
            results.append("FAIL: JSON serialization failed")
        
        # Test 15: Error handling for edge cases
        # Create a file with all invalid data
        bad_df = pd.DataFrame({
            'concentration': [-1, 0, np.inf],
            'response': [-50, 150, np.nan]
        })
        bad_input = os.path.join(temp_dir, "bad_data.csv")
        bad_df.to_csv(bad_input, index=False)
        
        try:
            bad_result = subprocess.run(
                ["python", "generated.py", "--input", bad_input, "--output", output_dir],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            # Should either handle gracefully or exit with error message
            if "invalid" in bad_result.stderr.lower() or "error" in bad_result.stderr.lower() or bad_result.returncode != 0:
                results.append("PASS: Handles invalid data appropriately")
            else:
                results.append("FAIL: Does not handle invalid data properly")
        except:
            results.append("PASS: Handles invalid data appropriately (timeout/error)")
        
        # Calculate scores
        # Score 1: Parameter estimation accuracy
        param_accuracy = 0.0
        if 'IC50' in fit_results and 'hill_slope' in fit_results:
            ic50_error = abs(np.log10(fit_results['IC50']) - np.log10(true_ic50)) / 2  # Normalize by 2 log units
            hill_error = abs(fit_results['hill_slope'] - true_hill) / 2  # Normalize by 2 units
            param_accuracy = max(0, 1 - (ic50_error + hill_error) / 2)
        
        # Score 2: Overall completeness
        pass_count = sum(1 for r in results if r.startswith("PASS"))
        completeness_score = pass_count / len(results)
        
        scores = [param_accuracy, completeness_score]
    
    return results + [f"SCORE: Parameter accuracy: {scores[0]:.3f}", 
                     f"SCORE: Overall completeness: {scores[1]:.3f}"], scores

if __name__ == "__main__":
    results, scores = test_dose_response_analysis()
    for result in results:
        print(result)
