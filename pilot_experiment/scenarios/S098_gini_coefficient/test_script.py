import subprocess
import json
import numpy as np
import matplotlib.pyplot as plt
import os
import tempfile
import shutil
from pathlib import Path

def create_data():
    """Create test scenarios for income inequality analysis"""
    return {
        'uniform': {
            'args': ['--population', '1000', '--distribution', 'uniform', '--min', '20000', '--max', '80000'],
            'expected_gini_range': (0.25, 0.4)
        },
        'normal': {
            'args': ['--population', '500', '--distribution', 'normal', '--mean', '50000', '--std', '15000'],
            'expected_gini_range': (0.2, 0.35)
        },
        'exponential': {
            'args': ['--population', '800', '--distribution', 'exponential', '--scale', '40000'],
            'expected_gini_range': (0.45, 0.65)
        },
        'equal': {
            'args': ['--population', '100', '--distribution', 'uniform', '--min', '50000', '--max', '50000'],
            'expected_gini_range': (0.0, 0.05)
        }
    }

def test_script():
    test_data = create_data()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Copy the generated script
        script_path = Path("generated.py")
        if not script_path.exists():
            shutil.copy2("../generated.py", "generated.py")
        
        results = []
        total_score = 0
        gini_accuracy_scores = []
        
        for scenario_name, scenario in test_data.items():
            print(f"\nTesting scenario: {scenario_name}")
            
            json_file = f"output_{scenario_name}.json"
            plot_file = f"plot_{scenario_name}.png"
            
            # Test command execution
            cmd = ['python', 'generated.py'] + scenario['args'] + ['--output-json', json_file, '--output-plot', plot_file]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                execution_success = result.returncode == 0
                print(f"PASS: Command execution successful" if execution_success else f"FAIL: Command failed - {result.stderr}")
                results.append(execution_success)
            except Exception as e:
                print(f"FAIL: Command execution failed - {e}")
                results.append(False)
                continue
            
            # Test JSON output file exists
            json_exists = Path(json_file).exists()
            print(f"PASS: JSON file created" if json_exists else f"FAIL: JSON file not created")
            results.append(json_exists)
            
            # Test plot file exists
            plot_exists = Path(plot_file).exists()
            print(f"PASS: Plot file created" if plot_exists else f"FAIL: Plot file not created")
            results.append(plot_exists)
            
            if json_exists:
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    # Test required JSON fields
                    required_fields = ['gini_coefficient', 'mean_income', 'median_income', 'income_std', 'percentile_90_10_ratio', 'quintile_shares']
                    all_fields_present = all(field in data for field in required_fields)
                    print(f"PASS: All required JSON fields present" if all_fields_present else f"FAIL: Missing JSON fields")
                    results.append(all_fields_present)
                    
                    # Test Gini coefficient range
                    if 'gini_coefficient' in data:
                        gini = data['gini_coefficient']
                        gini_valid_range = 0 <= gini <= 1
                        print(f"PASS: Gini coefficient in valid range [0,1]: {gini:.3f}" if gini_valid_range else f"FAIL: Gini coefficient out of range: {gini}")
                        results.append(gini_valid_range)
                        
                        # Test expected Gini range for scenario
                        expected_min, expected_max = scenario['expected_gini_range']
                        gini_in_expected_range = expected_min <= gini <= expected_max
                        print(f"PASS: Gini coefficient in expected range [{expected_min}, {expected_max}]: {gini:.3f}" if gini_in_expected_range else f"FAIL: Gini coefficient outside expected range")
                        results.append(gini_in_expected_range)
                        
                        # Calculate accuracy score for Gini coefficient
                        expected_center = (expected_min + expected_max) / 2
                        expected_range = expected_max - expected_min
                        accuracy = max(0, 1 - abs(gini - expected_center) / (expected_range / 2))
                        gini_accuracy_scores.append(accuracy)
                    else:
                        results.append(False)
                        results.append(False)
                        gini_accuracy_scores.append(0)
                    
                    # Test quintile shares
                    if 'quintile_shares' in data:
                        quintiles = data['quintile_shares']
                        quintiles_valid = (len(quintiles) == 5 and 
                                         all(0 <= share <= 1 for share in quintiles) and
                                         abs(sum(quintiles) - 1.0) < 0.01)
                        print(f"PASS: Quintile shares valid" if quintiles_valid else f"FAIL: Invalid quintile shares")
                        results.append(quintiles_valid)
                        
                        # Test quintile ordering (higher quintiles should generally have higher shares for unequal distributions)
                        if scenario_name != 'equal':
                            quintile_ordering = quintiles[-1] >= quintiles[0]  # Top quintile >= bottom quintile
                            print(f"PASS: Quintile ordering reasonable" if quintile_ordering else f"FAIL: Unexpected quintile ordering")
                            results.append(quintile_ordering)
                        else:
                            # For equal distribution, all quintiles should be approximately equal
                            quintile_equality = all(abs(share - 0.2) < 0.05 for share in quintiles)
                            print(f"PASS: Equal distribution quintiles" if quintile_equality else f"FAIL: Unequal quintiles for equal income")
                            results.append(quintile_equality)
                    else:
                        results.append(False)
                        results.append(False)
                    
                    # Test statistical measures reasonableness
                    if all(field in data for field in ['mean_income', 'median_income', 'income_std']):
                        stats_positive = all(data[field] > 0 for field in ['mean_income', 'median_income', 'income_std'])
                        print(f"PASS: Statistical measures positive" if stats_positive else f"FAIL: Non-positive statistical measures")
                        results.append(stats_positive)
                        
                        # Test percentile ratio
                        if 'percentile_90_10_ratio' in data:
                            ratio_reasonable = data['percentile_90_10_ratio'] >= 1.0
                            print(f"PASS: 90/10 percentile ratio >= 1" if ratio_reasonable else f"FAIL: Invalid percentile ratio")
                            results.append(ratio_reasonable)
                        else:
                            results.append(False)
                    else:
                        results.append(False)
                        results.append(False)
                        
                except Exception as e:
                    print(f"FAIL: JSON parsing error - {e}")
                    results.extend([False] * 6)
                    gini_accuracy_scores.append(0)
            else:
                results.extend([False] * 6)
                gini_accuracy_scores.append(0)
        
        # Test plot content (basic check on one file)
        if Path("plot_normal.png").exists():
            plot_size_reasonable = Path("plot_normal.png").stat().st_size > 1000
            print(f"PASS: Plot file has reasonable size" if plot_size_reasonable else f"FAIL: Plot file too small")
            results.append(plot_size_reasonable)
        else:
            results.append(False)
        
        # Calculate final scores
        pass_rate = sum(results) / len(results)
        gini_accuracy = np.mean(gini_accuracy_scores) if gini_accuracy_scores else 0
        
        print(f"\nSCORE: {pass_rate:.3f}")
        print(f"SCORE: {gini_accuracy:.3f}")
        
        return pass_rate, gini_accuracy

if __name__ == "__main__":
    test_script()
