import subprocess
import json
import os
import tempfile
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def create_data():
    """Generate synthetic tensile test parameters"""
    test_cases = [
        {
            'n_points': 1000,
            'max_stress': 500,
            'max_strain': 0.25,
            'expected_modulus_range': (180000, 220000),  # GPa converted to MPa
            'expected_yield_range': (200, 400),
            'expected_uts_range': (450, 500)
        },
        {
            'n_points': 500,
            'max_stress': 300,
            'max_strain': 0.15,
            'expected_modulus_range': (150000, 250000),
            'expected_yield_range': (150, 250),
            'expected_uts_range': (280, 300)
        }
    ]
    return test_cases

def run_test():
    test_cases = create_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        total_score = 0
        max_score = 0
        results = []
        
        for i, case in enumerate(test_cases):
            print(f"\n=== Test Case {i+1} ===")
            
            # Test different argument name variations
            arg_variations = [
                ['--n_points', '--max_stress', '--max_strain', '--plot', '--output'],
                ['--n-points', '--max-stress', '--max-strain', '--plot-file', '--output-file'],
                ['--points', '--stress', '--strain', '--plot', '--json'],
                ['--num_points', '--max_stress', '--max_strain', '--plot_file', '--json_file']
            ]
            
            success = False
            for args in arg_variations:
                try:
                    plot_file = f'tensile_plot_{i}.png'
                    json_file = f'results_{i}.json'
                    
                    cmd = [
                        'python', 'generated.py',
                        args[0], str(case['n_points']),
                        args[1], str(case['max_stress']),
                        args[2], str(case['max_strain']),
                        args[3], plot_file,
                        args[4], json_file
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        success = True
                        break
                        
                except Exception as e:
                    continue
            
            if not success:
                print("FAIL: Script execution failed with all argument variations")
                results.extend([False] * 7)
                continue
            
            # Test 1: Script runs without error
            script_success = result.returncode == 0
            print(f"PASS: Script execution successful" if script_success else f"FAIL: Script failed with error: {result.stderr}")
            results.append(script_success)
            
            # Test 2: JSON output file exists
            json_exists = os.path.exists(json_file)
            print(f"PASS: JSON file created" if json_exists else "FAIL: JSON file not created")
            results.append(json_exists)
            
            # Test 3: Plot file exists
            plot_exists = os.path.exists(plot_file)
            print(f"PASS: Plot file created" if plot_exists else "FAIL: Plot file not created")
            results.append(plot_exists)
            
            if json_exists:
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    # Test 4: JSON contains required fields
                    required_fields = ['elastic_modulus', 'yield_strength', 'ultimate_tensile_strength']
                    has_fields = all(field in data for field in required_fields)
                    print(f"PASS: All required fields present" if has_fields else "FAIL: Missing required fields")
                    results.append(has_fields)
                    
                    if has_fields:
                        # Test 5: Elastic modulus in reasonable range
                        modulus = data['elastic_modulus']
                        modulus_ok = case['expected_modulus_range'][0] <= modulus <= case['expected_modulus_range'][1]
                        print(f"PASS: Elastic modulus reasonable ({modulus:.0f} MPa)" if modulus_ok else f"FAIL: Elastic modulus unreasonable ({modulus:.0f} MPa)")
                        results.append(modulus_ok)
                        
                        # Test 6: Yield strength in reasonable range
                        yield_str = data['yield_strength']
                        yield_ok = case['expected_yield_range'][0] <= yield_str <= case['expected_yield_range'][1]
                        print(f"PASS: Yield strength reasonable ({yield_str:.1f} MPa)" if yield_ok else f"FAIL: Yield strength unreasonable ({yield_str:.1f} MPa)")
                        results.append(yield_ok)
                        
                        # Test 7: UTS in reasonable range
                        uts = data['ultimate_tensile_strength']
                        uts_ok = case['expected_uts_range'][0] <= uts <= case['expected_uts_range'][1]
                        print(f"PASS: UTS reasonable ({uts:.1f} MPa)" if uts_ok else f"FAIL: UTS unreasonable ({uts:.1f} MPa)")
                        results.append(uts_ok)
                        
                        # Test 8: UTS >= Yield strength
                        uts_yield_ok = uts >= yield_str
                        print(f"PASS: UTS >= Yield strength" if uts_yield_ok else "FAIL: UTS < Yield strength")
                        results.append(uts_yield_ok)
                        
                        # Test 9: Elastic modulus is positive
                        modulus_positive = modulus > 0
                        print(f"PASS: Elastic modulus positive" if modulus_positive else "FAIL: Elastic modulus not positive")
                        results.append(modulus_positive)
                        
                    else:
                        results.extend([False, False, False, False, False])
                        
                except Exception as e:
                    print(f"FAIL: Error reading JSON: {e}")
                    results.extend([False, False, False, False, False, False])
            else:
                results.extend([False, False, False, False, False, False])
        
        # Additional tests
        print(f"\n=== Additional Tests ===")
        
        # Test 10: Help message
        try:
            help_result = subprocess.run(['python', 'generated.py', '--help'], 
                                       capture_output=True, text=True, timeout=10)
            help_ok = help_result.returncode == 0 and 'stress' in help_result.stdout.lower()
            print(f"PASS: Help message works" if help_ok else "FAIL: Help message issue")
            results.append(help_ok)
        except:
            print("FAIL: Help message failed")
            results.append(False)
        
        # Test 11: Error handling for invalid arguments
        try:
            error_result = subprocess.run(['python', 'generated.py', '--invalid_arg'], 
                                        capture_output=True, text=True, timeout=10)
            error_ok = error_result.returncode != 0
            print(f"PASS: Invalid argument handling" if error_ok else "FAIL: Should reject invalid arguments")
            results.append(error_ok)
        except:
            print("FAIL: Error handling test failed")
            results.append(False)
        
        # Test 12: Default values work
        try:
            default_result = subprocess.run(['python', 'generated.py', 
                                           '--plot', 'default_plot.png',
                                           '--output', 'default_results.json'], 
                                          capture_output=True, text=True, timeout=30)
            default_ok = default_result.returncode == 0
            print(f"PASS: Default values work" if default_ok else "FAIL: Default values issue")
            results.append(default_ok)
        except:
            print("FAIL: Default values test failed")
            results.append(False)
        
        # Test 13: Small dataset handling
        try:
            small_result = subprocess.run(['python', 'generated.py',
                                         '--n_points', '50',
                                         '--max_stress', '100',
                                         '--max_strain', '0.1',
                                         '--plot', 'small_plot.png',
                                         '--output', 'small_results.json'], 
                                        capture_output=True, text=True, timeout=30)
            small_ok = small_result.returncode == 0
            print(f"PASS: Small dataset handling" if small_ok else "FAIL: Small dataset issue")
            results.append(small_ok)
        except:
            print("FAIL: Small dataset test failed")
            results.append(False)
        
        # Test 14: Large dataset handling
        try:
            large_result = subprocess.run(['python', 'generated.py',
                                         '--n_points', '5000',
                                         '--max_stress', '1000',
                                         '--max_strain', '0.5',
                                         '--plot', 'large_plot.png',
                                         '--output', 'large_results.json'], 
                                        capture_output=True, text=True, timeout=60)
            large_ok = large_result.returncode == 0
            print(f"PASS: Large dataset handling" if large_ok else "FAIL: Large dataset issue")
            results.append(large_ok)
        except:
            print("FAIL: Large dataset test failed")
            results.append(False)
        
        # Calculate scores
        pass_rate = sum(results) / len(results)
        
        # Property accuracy score
        accuracy_score = 0
        accuracy_count = 0
        
        for i, case in enumerate(test_cases):
            json_file = f'results_{i}.json'
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    if all(field in data for field in ['elastic_modulus', 'yield_strength', 'ultimate_tensile_strength']):
                        # Score based on how close values are to expected ranges
                        modulus = data['elastic_modulus']
                        yield_str = data['yield_strength']
                        uts = data['ultimate_tensile_strength']
                        
                        modulus_score = 1.0 if case['expected_modulus_range'][0] <= modulus <= case['expected_modulus_range'][1] else 0.5
                        yield_score = 1.0 if case['expected_yield_range'][0] <= yield_str <= case['expected_yield_range'][1] else 0.5
                        uts_score = 1.0 if case['expected_uts_range'][0] <= uts <= case['expected_uts_range'][1] else 0.5
                        
                        accuracy_score += (modulus_score + yield_score + uts_score) / 3
                        accuracy_count += 1
                        
                except:
                    pass
        
        if accuracy_count > 0:
            accuracy_score /= accuracy_count
        
        print(f"\n=== SUMMARY ===")
        print(f"SCORE: {pass_rate:.3f}")
        print(f"SCORE: {accuracy_score:.3f}")

if __name__ == "__main__":
    run_test()
