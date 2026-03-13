import subprocess
import tempfile
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

def create_data():
    """Generate synthetic spirometry parameters for testing"""
    # Different test cases with varying respiratory function
    test_cases = [
        {"n_points": 1000, "fev1_target": 3.2, "fvc_target": 4.1},  # Normal
        {"n_points": 800, "fev1_target": 2.1, "fvc_target": 3.8},   # Mild obstruction
        {"n_points": 1200, "fev1_target": 4.0, "fvc_target": 4.8},  # Above normal
        {"n_points": 500, "fev1_target": 1.8, "fvc_target": 2.9},   # Moderate obstruction
    ]
    return test_cases

def run_test():
    test_cases = create_data()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Copy the generated script
        if os.path.exists('../generated.py'):
            subprocess.run(['cp', '../generated.py', './'], check=True)
        elif os.path.exists('generated.py'):
            pass  # Already in current directory
        else:
            print("FAIL: generated.py not found")
            return
            
        total_score = 0
        max_score = 0
        accuracy_scores = []
        completeness_scores = []
        
        for i, case in enumerate(test_cases):
            print(f"\n--- Test Case {i+1} ---")
            
            plot_file = f"spirometry_plot_{i}.png"
            json_file = f"results_{i}.json"
            
            # Test different argument naming patterns
            arg_patterns = [
                ['--n_points', str(case['n_points']), '--plot', plot_file, '--output', json_file],
                ['--points', str(case['n_points']), '--plot_file', plot_file, '--json_output', json_file],
                ['-n', str(case['n_points']), '-p', plot_file, '-o', json_file],
            ]
            
            success = False
            for pattern in arg_patterns:
                try:
                    result = subprocess.run(['python', 'generated.py'] + pattern, 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        success = True
                        break
                except:
                    continue
            
            if not success:
                print("FAIL: Script execution failed with all argument patterns")
                continue
                
            print("PASS: Script executed successfully")
            
            # Test 1: JSON file created
            if os.path.exists(json_file):
                print("PASS: JSON output file created")
                total_score += 1
            else:
                print("FAIL: JSON output file not created")
            max_score += 1
            
            # Test 2: Plot file created
            if os.path.exists(plot_file):
                print("PASS: Plot file created")
                total_score += 1
            else:
                print("FAIL: Plot file not created")
            max_score += 1
            
            # Load and validate JSON results
            try:
                with open(json_file, 'r') as f:
                    results = json.load(f)
                print("PASS: JSON file is valid")
                total_score += 1
            except:
                print("FAIL: JSON file is invalid or unreadable")
                max_score += 1
                continue
            max_score += 1
            
            # Test 3: FEV1 present in results
            if 'FEV1' in results or 'fev1' in results:
                print("PASS: FEV1 value present in results")
                total_score += 1
                fev1_key = 'FEV1' if 'FEV1' in results else 'fev1'
                fev1_value = results[fev1_key]
            else:
                print("FAIL: FEV1 value missing from results")
                fev1_value = None
            max_score += 1
            
            # Test 4: FVC present in results
            if 'FVC' in results or 'fvc' in results:
                print("PASS: FVC value present in results")
                total_score += 1
                fvc_key = 'FVC' if 'FVC' in results else 'fvc'
                fvc_value = results[fvc_key]
            else:
                print("FAIL: FVC value missing from results")
                fvc_value = None
            max_score += 1
            
            # Test 5: FEV1/FVC ratio present
            ratio_keys = ['FEV1_FVC_ratio', 'fev1_fvc_ratio', 'ratio', 'FEV1/FVC']
            ratio_value = None
            for key in ratio_keys:
                if key in results:
                    ratio_value = results[key]
                    break
            
            if ratio_value is not None:
                print("PASS: FEV1/FVC ratio present in results")
                total_score += 1
            else:
                print("FAIL: FEV1/FVC ratio missing from results")
            max_score += 1
            
            # Test 6: Values are reasonable (basic sanity check)
            if fev1_value is not None and isinstance(fev1_value, (int, float)) and 0.5 < fev1_value < 8.0:
                print("PASS: FEV1 value is reasonable")
                total_score += 1
            else:
                print("FAIL: FEV1 value is unreasonable")
            max_score += 1
            
            # Test 7: FVC values are reasonable
            if fvc_value is not None and isinstance(fvc_value, (int, float)) and 1.0 < fvc_value < 10.0:
                print("PASS: FVC value is reasonable")
                total_score += 1
            else:
                print("FAIL: FVC value is unreasonable")
            max_score += 1
            
            # Test 8: Ratio is reasonable
            if ratio_value is not None and isinstance(ratio_value, (int, float)) and 0.3 < ratio_value < 1.2:
                print("PASS: FEV1/FVC ratio is reasonable")
                total_score += 1
            else:
                print("FAIL: FEV1/FVC ratio is unreasonable")
            max_score += 1
            
            # Test 9: FEV1 < FVC (physiologically correct)
            if fev1_value is not None and fvc_value is not None and fev1_value <= fvc_value:
                print("PASS: FEV1 ≤ FVC (physiologically correct)")
                total_score += 1
            else:
                print("FAIL: FEV1 > FVC (physiologically impossible)")
            max_score += 1
            
            # Test 10: Plot file is valid PNG
            try:
                plt.imread(plot_file)
                print("PASS: Plot file is valid image")
                total_score += 1
            except:
                print("FAIL: Plot file is not a valid image")
            max_score += 1
            
            # Test 11: Ratio calculation consistency
            if (fev1_value is not None and fvc_value is not None and 
                ratio_value is not None and fvc_value > 0):
                calculated_ratio = fev1_value / fvc_value
                if abs(calculated_ratio - ratio_value) < 0.05:
                    print("PASS: FEV1/FVC ratio calculation is consistent")
                    total_score += 1
                else:
                    print("FAIL: FEV1/FVC ratio calculation is inconsistent")
            else:
                print("FAIL: Cannot verify ratio calculation")
            max_score += 1
            
            # Calculate accuracy score based on reasonable physiological values
            accuracy = 0
            if fev1_value is not None and 1.0 < fev1_value < 6.0:
                accuracy += 0.33
            if fvc_value is not None and 2.0 < fvc_value < 8.0:
                accuracy += 0.33
            if ratio_value is not None and 0.5 < ratio_value < 1.0:
                accuracy += 0.34
            accuracy_scores.append(accuracy)
            
            # Calculate completeness score
            completeness = 0
            if fev1_value is not None:
                completeness += 0.33
            if fvc_value is not None:
                completeness += 0.33
            if ratio_value is not None:
                completeness += 0.34
            completeness_scores.append(completeness)
        
        # Final summary
        print(f"\n--- SUMMARY ---")
        print(f"Total PASS: {total_score}/{max_score}")
        
        if accuracy_scores:
            avg_accuracy = np.mean(accuracy_scores)
            print(f"SCORE: {avg_accuracy:.3f} (physiological accuracy)")
        else:
            print("SCORE: 0.000 (physiological accuracy)")
            
        if completeness_scores:
            avg_completeness = np.mean(completeness_scores)
            print(f"SCORE: {avg_completeness:.3f} (output completeness)")
        else:
            print("SCORE: 0.000 (output completeness)")

if __name__ == "__main__":
    run_test()
