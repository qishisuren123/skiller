import subprocess
import tempfile
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

def create_data():
    """Create test parameters for various scenarios"""
    test_cases = [
        # Standard case
        {"num_points": 1000, "noise_level": 0.001, "transit_depth": 0.01},
        # High noise case
        {"num_points": 500, "noise_level": 0.005, "transit_depth": 0.015},
        # Shallow transit
        {"num_points": 1500, "noise_level": 0.0005, "transit_depth": 0.005},
        # Deep transit
        {"num_points": 800, "noise_level": 0.002, "transit_depth": 0.025},
    ]
    return test_cases

def run_test():
    test_cases = create_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        total_score = 0
        detection_accuracy = 0
        fit_quality = 0
        
        for i, case in enumerate(test_cases):
            print(f"Running test case {i+1}")
            
            output_file = f"results_{i}.json"
            plot_file = f"plot_{i}.png"
            
            # Test with plot
            cmd = [
                "python", "generated.py",
                "--num_points", str(case["num_points"]),
                "--noise_level", str(case["noise_level"]),
                "--transit_depth", str(case["transit_depth"]),
                "--output_file", output_file,
                "--plot_file", plot_file
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                # Test 1: Script runs without error
                if result.returncode == 0:
                    print("PASS: Script executed successfully")
                    total_score += 1
                else:
                    print(f"FAIL: Script failed with return code {result.returncode}")
                    print(f"Error: {result.stderr}")
                    continue
                
                # Test 2: Output JSON file exists
                if os.path.exists(output_file):
                    print("PASS: Output JSON file created")
                    total_score += 1
                else:
                    print("FAIL: Output JSON file not created")
                    continue
                
                # Test 3: Plot file exists when requested
                if os.path.exists(plot_file):
                    print("PASS: Plot file created when requested")
                    total_score += 1
                else:
                    print("FAIL: Plot file not created")
                
                # Load and validate JSON results
                try:
                    with open(output_file, 'r') as f:
                        results = json.load(f)
                    
                    # Test 4: JSON contains required fields
                    required_fields = ['detected_transit_time', 'fitted_depth', 'fitted_duration', 
                                     'detection_significance', 'chi_squared', 'reduced_chi_squared']
                    has_all_fields = all(field in results for field in required_fields)
                    
                    if has_all_fields:
                        print("PASS: JSON contains all required fields")
                        total_score += 1
                    else:
                        print("FAIL: JSON missing required fields")
                        missing = [f for f in required_fields if f not in results]
                        print(f"Missing: {missing}")
                    
                    # Test 5: Transit time detection accuracy (should be near day 5.0)
                    if 'detected_transit_time' in results:
                        detected_time = results['detected_transit_time']
                        if isinstance(detected_time, (int, float)) and 4.8 <= detected_time <= 5.2:
                            print("PASS: Transit time detected accurately")
                            total_score += 1
                            detection_accuracy += 1
                        else:
                            print(f"FAIL: Transit time inaccurate: {detected_time}")
                    
                    # Test 6: Fitted depth reasonable
                    if 'fitted_depth' in results:
                        fitted_depth = results['fitted_depth']
                        expected_depth = case['transit_depth']
                        if isinstance(fitted_depth, (int, float)) and abs(fitted_depth - expected_depth) < expected_depth * 0.5:
                            print("PASS: Fitted depth reasonable")
                            total_score += 1
                            fit_quality += abs(fitted_depth - expected_depth) / expected_depth
                        else:
                            print(f"FAIL: Fitted depth unreasonable: {fitted_depth} vs expected {expected_depth}")
                    
                    # Test 7: Fitted duration reasonable (should be around 3 hours = 0.125 days)
                    if 'fitted_duration' in results:
                        fitted_duration = results['fitted_duration']
                        if isinstance(fitted_duration, (int, float)) and 0.05 <= fitted_duration <= 0.25:
                            print("PASS: Fitted duration reasonable")
                            total_score += 1
                        else:
                            print(f"FAIL: Fitted duration unreasonable: {fitted_duration}")
                    
                    # Test 8: Detection significance is positive
                    if 'detection_significance' in results:
                        significance = results['detection_significance']
                        if isinstance(significance, (int, float)) and significance > 0:
                            print("PASS: Detection significance positive")
                            total_score += 1
                        else:
                            print(f"FAIL: Detection significance invalid: {significance}")
                    
                    # Test 9: Chi-squared values are reasonable
                    if 'chi_squared' in results and 'reduced_chi_squared' in results:
                        chi2 = results['chi_squared']
                        red_chi2 = results['reduced_chi_squared']
                        if isinstance(chi2, (int, float)) and isinstance(red_chi2, (int, float)) and chi2 > 0 and red_chi2 > 0:
                            print("PASS: Chi-squared values reasonable")
                            total_score += 1
                        else:
                            print(f"FAIL: Chi-squared values invalid: {chi2}, {red_chi2}")
                    
                except json.JSONDecodeError:
                    print("FAIL: Invalid JSON format")
                except Exception as e:
                    print(f"FAIL: Error reading results: {e}")
            
            except subprocess.TimeoutExpired:
                print("FAIL: Script timed out")
            except Exception as e:
                print(f"FAIL: Unexpected error: {e}")
        
        # Test without plot file
        print("Testing without plot file")
        cmd_no_plot = [
            "python", "generated.py",
            "--num_points", "500",
            "--noise_level", "0.002",
            "--transit_depth", "0.012",
            "--output_file", "results_no_plot.json"
        ]
        
        try:
            result = subprocess.run(cmd_no_plot, capture_output=True, text=True, timeout=30)
            
            # Test 10: Script works without plot argument
            if result.returncode == 0:
                print("PASS: Script works without plot file")
                total_score += 1
            else:
                print("FAIL: Script fails without plot file")
            
            # Test 11: No plot file created when not requested
            if not os.path.exists("plot_no_plot.png"):
                print("PASS: No plot file created when not requested")
                total_score += 1
            else:
                print("FAIL: Plot file created when not requested")
        
        except Exception as e:
            print(f"FAIL: Error in no-plot test: {e}")
        
        # Test error handling
        print("Testing error handling")
        
        # Test 12: Invalid arguments
        cmd_invalid = [
            "python", "generated.py",
            "--num_points", "-100",
            "--output_file", "test.json"
        ]
        
        try:
            result = subprocess.run(cmd_invalid, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print("PASS: Script handles invalid arguments appropriately")
                total_score += 1
            else:
                print("FAIL: Script should reject invalid arguments")
        except Exception as e:
            print("PASS: Script handles invalid arguments appropriately")
            total_score += 1
        
        # Test 13: Missing required argument
        cmd_missing = ["python", "generated.py", "--num_points", "100"]
        
        try:
            result = subprocess.run(cmd_missing, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print("PASS: Script requires output file argument")
                total_score += 1
            else:
                print("FAIL: Script should require output file argument")
        except Exception as e:
            print("PASS: Script requires output file argument")
            total_score += 1
        
        # Test 14: High noise case still produces results
        cmd_noisy = [
            "python", "generated.py",
            "--num_points", "1000",
            "--noise_level", "0.01",
            "--transit_depth", "0.005",
            "--output_file", "noisy_results.json"
        ]
        
        try:
            result = subprocess.run(cmd_noisy, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists("noisy_results.json"):
                print("PASS: Script handles high noise case")
                total_score += 1
            else:
                print("FAIL: Script fails with high noise")
        except Exception as e:
            print(f"FAIL: Error in high noise test: {e}")
        
        # Test 15: Default arguments work
        cmd_defaults = ["python", "generated.py", "--output_file", "default_results.json"]
        
        try:
            result = subprocess.run(cmd_defaults, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists("default_results.json"):
                print("PASS: Script works with default arguments")
                total_score += 1
            else:
                print("FAIL: Script fails with default arguments")
        except Exception as e:
            print(f"FAIL: Error in default arguments test: {e}")
        
        # Calculate scores
        max_score = 15
        detection_accuracy_score = detection_accuracy / len(test_cases) if len(test_cases) > 0 else 0
        fit_quality_score = max(0, 1 - (fit_quality / len(test_cases))) if len(test_cases) > 0 else 0
        
        print(f"\nTotal Score: {total_score}/{max_score}")
        print(f"SCORE: {total_score/max_score:.3f}")
        print(f"SCORE: {(detection_accuracy_score + fit_quality_score)/2:.3f}")

if __name__ == "__main__":
    run_test()
