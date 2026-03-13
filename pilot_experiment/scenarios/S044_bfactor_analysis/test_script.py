import subprocess
import json
import os
import tempfile
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def create_data():
    """Generate synthetic B-factor data for testing"""
    np.random.seed(42)
    
    # Test case 1: Small protein with clear flexible regions
    bfactors_1 = np.concatenate([
        np.random.normal(20, 3, 15),  # Stable N-terminus
        np.random.normal(55, 8, 8),   # Flexible loop
        np.random.normal(18, 2, 20),  # Stable core
        np.random.normal(48, 6, 5),   # Flexible region
        np.random.normal(22, 4, 12)   # Stable C-terminus
    ])
    
    # Test case 2: Uniform low B-factors (rigid protein)
    bfactors_2 = np.random.normal(15, 2, 30)
    
    # Test case 3: Single residue
    bfactors_3 = np.array([35.5])
    
    return {
        'case1': bfactors_1,
        'case2': bfactors_2, 
        'case3': bfactors_3
    }

def run_test():
    test_data = create_data()
    results = {'passed': 0, 'total': 0, 'scores': {}}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Test case 1: Normal analysis
        bfactors_str = ','.join([f"{x:.1f}" for x in test_data['case1']])
        
        # Try common argument variations
        cmd_variations = [
            ['python', 'generated.py', '--bfactors', bfactors_str, '--output', 'results1.json', '--plot', 'plot1.png'],
            ['python', 'generated.py', '--bfactors', bfactors_str, '-o', 'results1.json', '-p', 'plot1.png'],
            ['python', 'generated.py', '--bfactors', bfactors_str, '--output', 'results1.json', '--plot', 'plot1.png']
        ]
        
        success = False
        for cmd in cmd_variations:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        # Test 1: Script runs successfully
        results['total'] += 1
        if success:
            results['passed'] += 1
            print("PASS: Script executed successfully")
        else:
            print("FAIL: Script failed to execute")
            return results
        
        # Test 2: JSON output file created
        results['total'] += 1
        if os.path.exists('results1.json'):
            results['passed'] += 1
            print("PASS: JSON output file created")
        else:
            print("FAIL: JSON output file not created")
            return results
        
        # Load results for further testing
        with open('results1.json', 'r') as f:
            json_data = json.load(f)
        
        # Test 3: JSON contains required statistical fields
        results['total'] += 1
        required_stats = ['mean', 'median', 'std']
        if all(stat in json_data for stat in required_stats):
            results['passed'] += 1
            print("PASS: JSON contains required statistical fields")
        else:
            print("FAIL: JSON missing required statistical fields")
        
        # Test 4: Statistical values are reasonable
        results['total'] += 1
        expected_mean = np.mean(test_data['case1'])
        actual_mean = json_data.get('mean', 0)
        if abs(actual_mean - expected_mean) < 1.0:
            results['passed'] += 1
            print("PASS: Mean calculation is accurate")
        else:
            print(f"FAIL: Mean calculation incorrect (expected ~{expected_mean:.1f}, got {actual_mean})")
        
        # Test 5: Flexible regions identified
        results['total'] += 1
        if 'flexible_residues' in json_data and len(json_data['flexible_residues']) > 0:
            results['passed'] += 1
            print("PASS: Flexible regions identified")
        else:
            print("FAIL: No flexible regions identified")
        
        # Test 6: Plot file created
        results['total'] += 1
        if os.path.exists('plot1.png'):
            results['passed'] += 1
            print("PASS: Plot file created")
        else:
            print("FAIL: Plot file not created")
        
        # Test 7: Quartiles present
        results['total'] += 1
        if 'q25' in json_data and 'q75' in json_data:
            results['passed'] += 1
            print("PASS: Quartiles calculated")
        else:
            print("FAIL: Quartiles missing")
        
        # Test case 2: With normalization
        cmd = ['python', 'generated.py', '--bfactors', bfactors_str, '--output', 'results2.json', '--plot', 'plot2.png', '--normalize']
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            success = result.returncode == 0
        except:
            success = False
        
        # Test 8: Normalization option works
        results['total'] += 1
        if success and os.path.exists('results2.json'):
            results['passed'] += 1
            print("PASS: Normalization option works")
        else:
            print("FAIL: Normalization option failed")
        
        if success and os.path.exists('results2.json'):
            with open('results2.json', 'r') as f:
                norm_data = json.load(f)
            
            # Test 9: Normalized values present
            results['total'] += 1
            if 'normalized_bfactors' in norm_data:
                results['passed'] += 1
                print("PASS: Normalized B-factors present")
            else:
                print("FAIL: Normalized B-factors missing")
            
            # Test 10: Normalized values in correct range
            results['total'] += 1
            if 'normalized_bfactors' in norm_data:
                norm_vals = norm_data['normalized_bfactors']
                if min(norm_vals) >= 0 and max(norm_vals) <= 100:
                    results['passed'] += 1
                    print("PASS: Normalized values in 0-100 range")
                else:
                    print("FAIL: Normalized values out of range")
            else:
                results['total'] += 1
                print("FAIL: Cannot test normalized range - no data")
        else:
            results['total'] += 2  # Skip tests 9 and 10
            print("FAIL: Cannot test normalization features")
        
        # Test case 3: Rigid protein (low B-factors)
        bfactors_str2 = ','.join([f"{x:.1f}" for x in test_data['case2']])
        cmd = ['python', 'generated.py', '--bfactors', bfactors_str2, '--output', 'results3.json', '--plot', 'plot3.png']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            success = result.returncode == 0
        except:
            success = False
        
        # Test 11: Handles low B-factor data
        results['total'] += 1
        if success:
            results['passed'] += 1
            print("PASS: Handles low B-factor data")
        else:
            print("FAIL: Failed with low B-factor data")
        
        # Test case 4: Single residue
        bfactors_str3 = f"{test_data['case3'][0]:.1f}"
        cmd = ['python', 'generated.py', '--bfactors', bfactors_str3, '--output', 'results4.json', '--plot', 'plot4.png']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            success = result.returncode == 0
        except:
            success = False
        
        # Test 12: Handles single residue
        results['total'] += 1
        if success:
            results['passed'] += 1
            print("PASS: Handles single residue case")
        else:
            print("FAIL: Failed with single residue")
        
        # Test 13: Flexible segments identified
        results['total'] += 1
        if os.path.exists('results1.json'):
            with open('results1.json', 'r') as f:
                data = json.load(f)
            if 'flexible_segments' in data:
                results['passed'] += 1
                print("PASS: Flexible segments identified")
            else:
                print("FAIL: Flexible segments not identified")
        else:
            print("FAIL: Cannot test flexible segments")
        
        # Test 14: Standard deviation reasonable
        results['total'] += 1
        if os.path.exists('results1.json'):
            with open('results1.json', 'r') as f:
                data = json.load(f)
            expected_std = np.std(test_data['case1'])
            actual_std = data.get('std', 0)
            if abs(actual_std - expected_std) < 1.0:
                results['passed'] += 1
                print("PASS: Standard deviation calculation accurate")
            else:
                print(f"FAIL: Standard deviation incorrect (expected ~{expected_std:.1f}, got {actual_std})")
        else:
            print("FAIL: Cannot test standard deviation")
        
        # Test 15: Median calculation
        results['total'] += 1
        if os.path.exists('results1.json'):
            with open('results1.json', 'r') as f:
                data = json.load(f)
            expected_median = np.median(test_data['case1'])
            actual_median = data.get('median', 0)
            if abs(actual_median - expected_median) < 1.0:
                results['passed'] += 1
                print("PASS: Median calculation accurate")
            else:
                print(f"FAIL: Median incorrect (expected ~{expected_median:.1f}, got {actual_median})")
        else:
            print("FAIL: Cannot test median")
        
        # Calculate scores
        # Score 1: Overall functionality (fraction of tests passed)
        functionality_score = results['passed'] / results['total']
        results['scores']['functionality'] = functionality_score
        print(f"SCORE: {functionality_score:.3f}")
        
        # Score 2: Statistical accuracy (based on key calculations)
        accuracy_tests = 0
        accuracy_passed = 0
        
        if os.path.exists('results1.json'):
            with open('results1.json', 'r') as f:
                data = json.load(f)
            
            # Check mean accuracy
            accuracy_tests += 1
            expected_mean = np.mean(test_data['case1'])
            actual_mean = data.get('mean', 0)
            if abs(actual_mean - expected_mean) < 0.5:
                accuracy_passed += 1
            
            # Check std accuracy  
            accuracy_tests += 1
            expected_std = np.std(test_data['case1'])
            actual_std = data.get('std', 0)
            if abs(actual_std - expected_std) < 0.5:
                accuracy_passed += 1
            
            # Check flexible region detection
            accuracy_tests += 1
            q75 = np.percentile(test_data['case1'], 75)
            expected_flexible = np.sum(test_data['case1'] > q75)
            actual_flexible = len(data.get('flexible_residues', []))
            if abs(actual_flexible - expected_flexible) <= 1:
                accuracy_passed += 1
        
        accuracy_score = accuracy_passed / accuracy_tests if accuracy_tests > 0 else 0
        results['scores']['statistical_accuracy'] = accuracy_score
        print(f"SCORE: {accuracy_score:.3f}")
    
    return results

if __name__ == "__main__":
    results = run_test()
    print(f"\nPassed {results['passed']}/{results['total']} tests")
    for score_name, score_value in results['scores'].items():
        print(f"{score_name}: {score_value:.3f}")
