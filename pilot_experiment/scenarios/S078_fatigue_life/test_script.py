import subprocess
import tempfile
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import sys

def create_data():
    """Generate synthetic fatigue test data"""
    np.random.seed(42)
    
    # Generate realistic S-N data for steel
    # True parameters: A ≈ 1000, b ≈ 0.1
    true_A = 1000
    true_b = 0.1
    
    # Generate stress levels from 200 to 800 MPa
    n_points = 15
    stress_levels = np.linspace(200, 800, n_points)
    
    # Calculate theoretical cycles with some scatter
    cycles_theoretical = (true_A / stress_levels) ** (1/true_b)
    
    # Add log-normal scatter (typical for fatigue data)
    scatter_factor = np.random.lognormal(0, 0.3, n_points)
    cycles_actual = cycles_theoretical * scatter_factor
    
    # Ensure reasonable ranges
    cycles_actual = np.clip(cycles_actual, 1e3, 1e8)
    
    return stress_levels, cycles_actual

def run_test():
    results = {"PASS": 0, "FAIL": 0, "scores": {}}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        stress_data, cycles_data = create_data()
        
        # Convert to comma-separated strings
        stress_str = ','.join(map(str, stress_data))
        cycles_str = ','.join(map(str, cycles_data.astype(int)))
        
        # Test stress levels for prediction
        test_stress_str = "300,400,500"
        
        # Possible argument variations
        arg_variations = [
            ['--stress', stress_str, '--cycles', cycles_str, '--predict-stress', test_stress_str, '--output', 'results.json', '--plot', 'sn_curve.png'],
            ['--stress-data', stress_str, '--cycle-data', cycles_str, '--prediction-stress', test_stress_str, '--output-file', 'results.json', '--plot-file', 'sn_curve.png'],
            ['-s', stress_str, '-c', cycles_str, '-p', test_stress_str, '-o', 'results.json', '--plot', 'sn_curve.png']
        ]
        
        success = False
        for args in arg_variations:
            try:
                result = subprocess.run([sys.executable, 'generated.py'] + args, 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed with all argument variations")
            results["FAIL"] += 12
            results["scores"]["curve_fit_quality"] = 0.0
            results["scores"]["prediction_accuracy"] = 0.0
            return results
        
        # Test 1: Script runs successfully
        if success:
            print("PASS: Script executed successfully")
            results["PASS"] += 1
        else:
            print("FAIL: Script execution failed")
            results["FAIL"] += 1
        
        # Test 2: JSON output file exists
        if os.path.exists('results.json'):
            print("PASS: JSON output file created")
            results["PASS"] += 1
        else:
            print("FAIL: JSON output file not found")
            results["FAIL"] += 1
            results["scores"]["curve_fit_quality"] = 0.0
            results["scores"]["prediction_accuracy"] = 0.0
            return results
        
        # Load and validate JSON output
        try:
            with open('results.json', 'r') as f:
                output_data = json.load(f)
        except:
            print("FAIL: Could not parse JSON output")
            results["FAIL"] += 10
            results["scores"]["curve_fit_quality"] = 0.0
            results["scores"]["prediction_accuracy"] = 0.0
            return results
        
        # Test 3: JSON contains required fitted parameters
        required_keys = ['A', 'b', 'r_squared']
        has_params = all(key in output_data for key in required_keys)
        if has_params:
            print("PASS: JSON contains fitted parameters A, b, and r_squared")
            results["PASS"] += 1
        else:
            print("FAIL: JSON missing required fitted parameters")
            results["FAIL"] += 1
        
        # Test 4: Fitted parameters are reasonable
        if has_params:
            A_val = output_data['A']
            b_val = output_data['b']
            r_squared = output_data['r_squared']
            
            if 500 <= A_val <= 2000 and 0.05 <= b_val <= 0.3:
                print("PASS: Fitted parameters A and b are in reasonable ranges")
                results["PASS"] += 1
            else:
                print(f"FAIL: Fitted parameters out of range (A={A_val}, b={b_val})")
                results["FAIL"] += 1
        else:
            results["FAIL"] += 1
        
        # Test 5: R-squared indicates good fit
        if has_params and r_squared > 0.7:
            print("PASS: R-squared indicates good curve fit")
            results["PASS"] += 1
        else:
            print(f"FAIL: Poor curve fit (R²={r_squared if has_params else 'N/A'})")
            results["FAIL"] += 1
        
        # Test 6: Predictions are included
        if 'predictions' in output_data:
            print("PASS: Predictions included in output")
            results["PASS"] += 1
            predictions = output_data['predictions']
        else:
            print("FAIL: No predictions in output")
            results["FAIL"] += 1
            predictions = {}
        
        # Test 7: Correct number of predictions
        if len(predictions) == 3:
            print("PASS: Correct number of predictions")
            results["PASS"] += 1
        else:
            print(f"FAIL: Expected 3 predictions, got {len(predictions)}")
            results["FAIL"] += 1
        
        # Test 8: Endurance limit calculation
        if 'endurance_limit' in output_data:
            print("PASS: Endurance limit calculated")
            results["PASS"] += 1
            endurance_limit = output_data['endurance_limit']
        else:
            print("FAIL: Endurance limit not calculated")
            results["FAIL"] += 1
            endurance_limit = None
        
        # Test 9: Endurance limit is reasonable
        if endurance_limit and 100 <= endurance_limit <= 400:
            print("PASS: Endurance limit is reasonable")
            results["PASS"] += 1
        else:
            print(f"FAIL: Endurance limit unreasonable ({endurance_limit})")
            results["FAIL"] += 1
        
        # Test 10: Plot file exists
        plot_exists = os.path.exists('sn_curve.png')
        if plot_exists:
            print("PASS: Plot file created")
            results["PASS"] += 1
        else:
            print("FAIL: Plot file not created")
            results["FAIL"] += 1
        
        # Test 11: Safety factors included
        if 'safety_factor' in output_data or any('safety' in str(v) for v in output_data.values()):
            print("PASS: Safety factors considered")
            results["PASS"] += 1
        else:
            print("FAIL: Safety factors not included")
            results["FAIL"] += 1
        
        # Test 12: Confidence intervals mentioned
        if 'confidence_interval' in output_data or 'confidence' in str(output_data):
            print("PASS: Confidence intervals included")
            results["PASS"] += 1
        else:
            print("FAIL: Confidence intervals not included")
            results["FAIL"] += 1
        
        # Calculate scores
        # Score 1: Curve fit quality based on R-squared
        if has_params:
            fit_score = min(1.0, max(0.0, r_squared))
        else:
            fit_score = 0.0
        results["scores"]["curve_fit_quality"] = fit_score
        
        # Score 2: Prediction accuracy (compare with theoretical)
        if predictions and has_params:
            try:
                test_stresses = [300, 400, 500]
                theoretical_cycles = [(output_data['A'] / s) ** (1/output_data['b']) for s in test_stresses]
                
                pred_cycles = []
                for stress in test_stresses:
                    if str(stress) in predictions:
                        pred_cycles.append(predictions[str(stress)])
                    elif stress in predictions:
                        pred_cycles.append(predictions[stress])
                
                if len(pred_cycles) == 3:
                    # Calculate relative errors
                    rel_errors = [abs(p - t) / t for p, t in zip(pred_cycles, theoretical_cycles)]
                    avg_error = np.mean(rel_errors)
                    accuracy_score = max(0.0, 1.0 - avg_error)
                else:
                    accuracy_score = 0.0
            except:
                accuracy_score = 0.0
        else:
            accuracy_score = 0.0
        
        results["scores"]["prediction_accuracy"] = accuracy_score
        
        print(f"SCORE: curve_fit_quality = {fit_score:.3f}")
        print(f"SCORE: prediction_accuracy = {accuracy_score:.3f}")
    
    return results

if __name__ == "__main__":
    results = run_test()
    print(f"\nSummary: {results['PASS']} passed, {results['FAIL']} failed")
