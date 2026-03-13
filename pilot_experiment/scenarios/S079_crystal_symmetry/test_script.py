import argparse
import json
import csv
import numpy as np
import pandas as pd
import tempfile
import subprocess
import os
import sys

def create_data():
    """Generate synthetic crystal structure data"""
    np.random.seed(42)
    
    crystals = []
    
    # Cubic crystals
    for _ in range(15):
        a = np.random.uniform(3.0, 8.0)
        crystals.append({
            'a': a, 'b': a, 'c': a,
            'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0,
            'expected': 'cubic'
        })
    
    # Tetragonal crystals
    for _ in range(12):
        a = np.random.uniform(3.0, 6.0)
        c = np.random.uniform(4.0, 10.0)
        crystals.append({
            'a': a, 'b': a, 'c': c,
            'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0,
            'expected': 'tetragonal'
        })
    
    # Orthorhombic crystals
    for _ in range(10):
        crystals.append({
            'a': np.random.uniform(3.0, 7.0),
            'b': np.random.uniform(4.0, 8.0),
            'c': np.random.uniform(5.0, 9.0),
            'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0,
            'expected': 'orthorhombic'
        })
    
    # Hexagonal crystals
    for _ in range(8):
        a = np.random.uniform(3.0, 6.0)
        c = np.random.uniform(4.0, 12.0)
        crystals.append({
            'a': a, 'b': a, 'c': c,
            'alpha': 90.0, 'beta': 90.0, 'gamma': 120.0,
            'expected': 'hexagonal'
        })
    
    # Trigonal crystals
    for _ in range(6):
        a = np.random.uniform(4.0, 7.0)
        angle = np.random.uniform(85.0, 95.0)
        if abs(angle - 90.0) < 1.0:
            angle = 85.0 if angle < 90 else 95.0
        crystals.append({
            'a': a, 'b': a, 'c': a,
            'alpha': angle, 'beta': angle, 'gamma': angle,
            'expected': 'trigonal'
        })
    
    # Monoclinic crystals
    for _ in range(8):
        beta = np.random.uniform(95.0, 120.0)
        crystals.append({
            'a': np.random.uniform(4.0, 8.0),
            'b': np.random.uniform(3.0, 7.0),
            'c': np.random.uniform(5.0, 9.0),
            'alpha': 90.0, 'beta': beta, 'gamma': 90.0,
            'expected': 'monoclinic'
        })
    
    # Triclinic crystals
    for _ in range(6):
        crystals.append({
            'a': np.random.uniform(4.0, 8.0),
            'b': np.random.uniform(3.0, 7.0),
            'c': np.random.uniform(5.0, 9.0),
            'alpha': np.random.uniform(80.0, 100.0),
            'beta': np.random.uniform(85.0, 105.0),
            'gamma': np.random.uniform(75.0, 110.0),
            'expected': 'triclinic'
        })
    
    return crystals

def test_crystal_classification():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        crystals = create_data()
        
        # Create CSV file
        csv_file = 'crystals.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['a', 'b', 'c', 'alpha', 'beta', 'gamma'])
            writer.writeheader()
            for crystal in crystals:
                writer.writerow({k: v for k, v in crystal.items() if k != 'expected'})
        
        output_file = 'results.json'
        
        # Test CSV input
        try:
            result = subprocess.run([
                sys.executable, 'generated.py',
                '--input-csv', csv_file,
                '--output', output_file,
                '--tolerance', '0.1'
            ], capture_output=True, text=True, timeout=30)
            
            print("PASS: Script executed without errors")
            csv_success = True
        except:
            print("FAIL: Script execution failed")
            csv_success = False
            return
        
        # Load and validate results
        try:
            with open(output_file, 'r') as f:
                results = json.load(f)
            print("PASS: Output JSON file created and readable")
        except:
            print("FAIL: Could not read output JSON file")
            return
        
        # Test structure of results
        required_keys = ['classifications', 'statistics']
        if all(key in results for key in required_keys):
            print("PASS: Results contain required top-level keys")
        else:
            print("FAIL: Results missing required keys")
        
        # Test classifications
        classifications = results.get('classifications', [])
        if len(classifications) == len(crystals):
            print("PASS: Correct number of classifications")
        else:
            print("FAIL: Incorrect number of classifications")
        
        # Test individual crystal system classifications
        correct_classifications = 0
        total_classifications = len(crystals)
        
        for i, (crystal, classification) in enumerate(zip(crystals, classifications)):
            expected = crystal['expected']
            predicted = classification.get('crystal_system', '').lower()
            
            if predicted == expected:
                correct_classifications += 1
        
        accuracy = correct_classifications / total_classifications if total_classifications > 0 else 0
        
        if accuracy >= 0.8:
            print("PASS: Crystal system classification accuracy >= 80%")
        else:
            print("FAIL: Crystal system classification accuracy < 80%")
        
        print(f"SCORE: {accuracy:.3f}")
        
        # Test statistics section
        stats = results.get('statistics', {})
        if 'crystal_system_distribution' in stats:
            print("PASS: Statistics include crystal system distribution")
        else:
            print("FAIL: Statistics missing crystal system distribution")
        
        if 'average_volumes' in stats or 'parameter_ranges' in stats:
            print("PASS: Statistics include volume or parameter information")
        else:
            print("FAIL: Statistics missing volume/parameter information")
        
        # Test individual parameter input
        test_crystal = crystals[0]
        single_output = 'single_result.json'
        
        try:
            subprocess.run([
                sys.executable, 'generated.py',
                '--a', str(test_crystal['a']),
                '--b', str(test_crystal['b']),
                '--c', str(test_crystal['c']),
                '--alpha', str(test_crystal['alpha']),
                '--beta', str(test_crystal['beta']),
                '--gamma', str(test_crystal['gamma']),
                '--output', single_output
            ], capture_output=True, text=True, timeout=30)
            
            with open(single_output, 'r') as f:
                single_results = json.load(f)
            
            if len(single_results.get('classifications', [])) == 1:
                print("PASS: Single crystal parameter input works")
            else:
                print("FAIL: Single crystal parameter input failed")
        except:
            print("FAIL: Single crystal parameter input failed")
        
        # Test tolerance parameter effect
        tolerance_test_crystal = {
            'a': 5.000, 'b': 5.001, 'c': 5.002,
            'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0
        }
        
        # Write tolerance test crystal
        tolerance_csv = 'tolerance_test.csv'
        with open(tolerance_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['a', 'b', 'c', 'alpha', 'beta', 'gamma'])
            writer.writeheader()
            writer.writerow(tolerance_test_crystal)
        
        tolerance_output = 'tolerance_result.json'
        
        try:
            subprocess.run([
                sys.executable, 'generated.py',
                '--input-csv', tolerance_csv,
                '--output', tolerance_output,
                '--tolerance', '0.01'
            ], capture_output=True, text=True, timeout=30)
            
            with open(tolerance_output, 'r') as f:
                tolerance_results = json.load(f)
            
            predicted_system = tolerance_results['classifications'][0]['crystal_system'].lower()
            if predicted_system == 'cubic':
                print("PASS: Tolerance parameter working correctly")
            else:
                print("FAIL: Tolerance parameter not working correctly")
        except:
            print("FAIL: Tolerance test failed")
        
        # Test validation of unreasonable parameters
        invalid_crystal = {
            'a': -1.0, 'b': 5.0, 'c': 5.0,
            'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0
        }
        
        invalid_csv = 'invalid_test.csv'
        with open(invalid_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['a', 'b', 'c', 'alpha', 'beta', 'gamma'])
            writer.writeheader()
            writer.writerow(invalid_crystal)
        
        invalid_output = 'invalid_result.json'
        
        try:
            result = subprocess.run([
                sys.executable, 'generated.py',
                '--input-csv', invalid_csv,
                '--output', invalid_output
            ], capture_output=True, text=True, timeout=30)
            
            # Should either fail or include warnings
            if result.returncode != 0 or 'warn' in result.stderr.lower() or 'error' in result.stderr.lower():
                print("PASS: Invalid parameters properly handled")
            else:
                print("FAIL: Invalid parameters not properly validated")
        except:
            print("PASS: Invalid parameters caused appropriate failure")
        
        # Test comprehensive crystal system coverage
        predicted_systems = set()
        for classification in classifications:
            predicted_systems.add(classification.get('crystal_system', '').lower())
        
        expected_systems = {'cubic', 'tetragonal', 'orthorhombic', 'hexagonal', 'trigonal', 'monoclinic', 'triclinic'}
        coverage = len(predicted_systems.intersection(expected_systems)) / len(expected_systems)
        
        if coverage >= 0.6:
            print("PASS: Good coverage of crystal systems")
        else:
            print("FAIL: Poor coverage of crystal systems")
        
        print(f"SCORE: {coverage:.3f}")
        
        # Test parameter preservation in output
        first_classification = classifications[0] if classifications else {}
        if all(param in first_classification for param in ['a', 'b', 'c', 'alpha', 'beta', 'gamma']):
            print("PASS: Input parameters preserved in output")
        else:
            print("FAIL: Input parameters not preserved in output")

if __name__ == "__main__":
    test_crystal_classification()
