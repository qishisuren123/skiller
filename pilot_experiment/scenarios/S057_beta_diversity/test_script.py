import subprocess
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
import os
import sys
from pathlib import Path

def create_data():
    """Generate synthetic ecological community data"""
    np.random.seed(42)
    
    # Create 5 sites with varying species compositions
    # Site 1: Forest community
    site1 = [15, 8, 12, 0, 3, 7, 0, 5, 2, 0]  # 10 species
    
    # Site 2: Similar forest community  
    site2 = [12, 6, 10, 1, 4, 8, 0, 3, 1, 0]
    
    # Site 3: Grassland community (different species dominant)
    site3 = [2, 0, 1, 18, 0, 2, 15, 0, 8, 12]
    
    # Site 4: Mixed community
    site4 = [5, 3, 4, 8, 2, 6, 7, 2, 4, 3]
    
    # Site 5: Sparse community
    site5 = [1, 0, 0, 2, 0, 1, 0, 0, 1, 0]
    
    return [site1, site2, site3, site4, site5]

def bray_curtis_dissimilarity(site1, site2):
    """Calculate Bray-Curtis dissimilarity between two sites"""
    site1, site2 = np.array(site1), np.array(site2)
    numerator = np.sum(np.abs(site1 - site2))
    denominator = np.sum(site1 + site2)
    if denominator == 0:
        return 0.0
    return numerator / denominator

def jaccard_dissimilarity(site1, site2):
    """Calculate Jaccard dissimilarity between two sites"""
    site1_bin = np.array(site1) > 0
    site2_bin = np.array(site2) > 0
    intersection = np.sum(site1_bin & site2_bin)
    union = np.sum(site1_bin | site2_bin)
    if union == 0:
        return 0.0
    return 1.0 - (intersection / union)

def sorensen_dissimilarity(site1, site2):
    """Calculate Sorensen dissimilarity between two sites"""
    site1_bin = np.array(site1) > 0
    site2_bin = np.array(site2) > 0
    intersection = np.sum(site1_bin & site2_bin)
    total_species = np.sum(site1_bin) + np.sum(site2_bin)
    if total_species == 0:
        return 0.0
    return 1.0 - (2 * intersection / total_species)

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create test data
        sites_data = create_data()
        
        # Prepare command line arguments
        sites_str = ' '.join([','.join(map(str, site)) for site in sites_data])
        
        # Test different possible argument names
        cmd_variants = [
            ['python', 'generated.py', '--sites', sites_str, '--output', 'results.json', '--plot', 'heatmap.png'],
            ['python', 'generated.py', '--sites', sites_str, '--output', 'results.json', '--plot', 'heatmap.png'],
            ['python', 'generated.py', '--site-data', sites_str, '--output', 'results.json', '--plot', 'heatmap.png'],
            ['python', 'generated.py', '--sites', sites_str, '-o', 'results.json', '-p', 'heatmap.png']
        ]
        
        success = False
        for cmd in cmd_variants:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed")
            return
        
        print("PASS: Script executed successfully")
        
        # Test 1: Check if JSON output file exists
        if os.path.exists('results.json'):
            print("PASS: JSON output file created")
        else:
            print("FAIL: JSON output file not created")
            return
        
        # Test 2: Check if plot file exists
        if os.path.exists('heatmap.png'):
            print("PASS: Heatmap PNG file created")
        else:
            print("FAIL: Heatmap PNG file not created")
        
        # Load and validate JSON results
        try:
            with open('results.json', 'r') as f:
                results = json.load(f)
            print("PASS: JSON file is valid and readable")
        except:
            print("FAIL: JSON file is invalid or unreadable")
            return
        
        # Test 3: Check for required matrices
        required_keys = ['bray_curtis', 'jaccard', 'sorensen']
        has_all_matrices = all(key in results for key in required_keys)
        if has_all_matrices:
            print("PASS: All required dissimilarity matrices present")
        else:
            print("FAIL: Missing required dissimilarity matrices")
        
        # Test 4: Check matrix dimensions
        n_sites = len(sites_data)
        correct_dimensions = True
        for key in required_keys:
            if key in results:
                matrix = np.array(results[key])
                if matrix.shape != (n_sites, n_sites):
                    correct_dimensions = False
                    break
        
        if correct_dimensions:
            print("PASS: Dissimilarity matrices have correct dimensions")
        else:
            print("FAIL: Dissimilarity matrices have incorrect dimensions")
        
        # Test 5: Check diagonal values (should be 0 for dissimilarity)
        diagonal_correct = True
        for key in required_keys:
            if key in results:
                matrix = np.array(results[key])
                if not np.allclose(np.diag(matrix), 0, atol=1e-6):
                    diagonal_correct = False
                    break
        
        if diagonal_correct:
            print("PASS: Diagonal values are zero (sites identical to themselves)")
        else:
            print("FAIL: Diagonal values are not zero")
        
        # Test 6: Check symmetry of matrices
        symmetric = True
        for key in required_keys:
            if key in results:
                matrix = np.array(results[key])
                if not np.allclose(matrix, matrix.T, atol=1e-6):
                    symmetric = False
                    break
        
        if symmetric:
            print("PASS: Dissimilarity matrices are symmetric")
        else:
            print("FAIL: Dissimilarity matrices are not symmetric")
        
        # Test 7: Check value ranges (0 to 1 for dissimilarity)
        values_in_range = True
        for key in required_keys:
            if key in results:
                matrix = np.array(results[key])
                if np.any(matrix < 0) or np.any(matrix > 1):
                    values_in_range = False
                    break
        
        if values_in_range:
            print("PASS: All dissimilarity values are in range [0,1]")
        else:
            print("FAIL: Some dissimilarity values are outside range [0,1]")
        
        # Test 8: Check for summary statistics
        has_summary = 'summary_statistics' in results
        if has_summary:
            print("PASS: Summary statistics included")
        else:
            print("FAIL: Summary statistics missing")
        
        # Test 9: Validate Bray-Curtis calculation for known case
        if 'bray_curtis' in results:
            bc_matrix = np.array(results['bray_curtis'])
            expected_bc_01 = bray_curtis_dissimilarity(sites_data[0], sites_data[1])
            actual_bc_01 = bc_matrix[0, 1]
            if abs(expected_bc_01 - actual_bc_01) < 0.01:
                print("PASS: Bray-Curtis calculation appears correct")
            else:
                print("FAIL: Bray-Curtis calculation appears incorrect")
        else:
            print("FAIL: Bray-Curtis matrix missing")
        
        # Test 10: Validate Jaccard calculation
        if 'jaccard' in results:
            jaccard_matrix = np.array(results['jaccard'])
            expected_jaccard_01 = jaccard_dissimilarity(sites_data[0], sites_data[1])
            actual_jaccard_01 = jaccard_matrix[0, 1]
            if abs(expected_jaccard_01 - actual_jaccard_01) < 0.01:
                print("PASS: Jaccard calculation appears correct")
            else:
                print("FAIL: Jaccard calculation appears incorrect")
        else:
            print("FAIL: Jaccard matrix missing")
        
        # Test 11: Check that different metrics give different results
        if all(key in results for key in required_keys):
            bc_matrix = np.array(results['bray_curtis'])
            jaccard_matrix = np.array(results['jaccard'])
            sorensen_matrix = np.array(results['sorensen'])
            
            # They should not be identical (except possibly diagonal)
            matrices_different = not (np.allclose(bc_matrix, jaccard_matrix) and 
                                    np.allclose(bc_matrix, sorensen_matrix))
            if matrices_different:
                print("PASS: Different metrics produce different results")
            else:
                print("FAIL: All metrics produce identical results")
        else:
            print("FAIL: Cannot compare metrics - matrices missing")
        
        # Test 12: Check PNG file is valid
        try:
            from PIL import Image
            img = Image.open('heatmap.png')
            img.verify()
            print("PASS: PNG file is valid image")
        except:
            print("FAIL: PNG file is invalid or corrupted")
        
        # SCORE 1: Accuracy of Bray-Curtis calculations
        if 'bray_curtis' in results:
            bc_matrix = np.array(results['bray_curtis'])
            total_error = 0
            count = 0
            for i in range(len(sites_data)):
                for j in range(i+1, len(sites_data)):
                    expected = bray_curtis_dissimilarity(sites_data[i], sites_data[j])
                    actual = bc_matrix[i, j]
                    total_error += abs(expected - actual)
                    count += 1
            avg_error = total_error / count if count > 0 else 1.0
            accuracy_score = max(0, 1.0 - avg_error * 10)  # Scale error
            print(f"SCORE: Bray-Curtis accuracy: {accuracy_score:.3f}")
        else:
            print("SCORE: Bray-Curtis accuracy: 0.000")
        
        # SCORE 2: Completeness of output
        completeness_items = [
            os.path.exists('results.json'),
            os.path.exists('heatmap.png'),
            'bray_curtis' in results if 'results' in locals() else False,
            'jaccard' in results if 'results' in locals() else False,
            'sorensen' in results if 'results' in locals() else False,
            'summary_statistics' in results if 'results' in locals() else False
        ]
        completeness_score = sum(completeness_items) / len(completeness_items)
        print(f"SCORE: Output completeness: {completeness_score:.3f}")

if __name__ == "__main__":
    run_test()
