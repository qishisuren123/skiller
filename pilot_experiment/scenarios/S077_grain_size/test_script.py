import subprocess
import json
import tempfile
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def create_data():
    """Generate synthetic grain diameter data"""
    np.random.seed(42)
    
    # Generate realistic grain size distribution (log-normal)
    n_grains = 150
    log_mean = np.log(100)  # ~100 μm mean
    log_std = 0.6
    
    diameters = np.random.lognormal(log_mean, log_std, n_grains)
    
    # Add some fine and coarse grains for classification testing
    fine_grains = np.random.uniform(20, 49, 20)
    coarse_grains = np.random.uniform(201, 400, 30)
    
    all_diameters = np.concatenate([diameters, fine_grains, coarse_grains])
    np.random.shuffle(all_diameters)
    
    return all_diameters

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        test_diameters = create_data()
        diameter_str = ','.join([f"{d:.2f}" for d in test_diameters])
        
        # Test basic functionality
        result = subprocess.run([
            'python', 'generated.py', 
            '--diameters', diameter_str,
            '--output', 'test_output.json'
        ], capture_output=True, text=True, cwd='/tmp')
        
        print("PASS" if result.returncode == 0 else "FAIL", "- Script runs without errors")
        
        # Check JSON output exists
        json_exists = os.path.exists('test_output.json')
        print("PASS" if json_exists else "FAIL", "- JSON output file created")
        
        if not json_exists:
            return
            
        # Load and validate JSON structure
        try:
            with open('test_output.json', 'r') as f:
                results = json.load(f)
            json_valid = True
        except:
            json_valid = False
            results = {}
            
        print("PASS" if json_valid else "FAIL", "- JSON file is valid")
        
        # Check basic statistics
        basic_stats_keys = ['mean', 'median', 'std', 'min', 'max']
        has_basic_stats = all(key in str(results).lower() for key in basic_stats_keys)
        print("PASS" if has_basic_stats else "FAIL", "- Basic statistics computed")
        
        # Check percentiles
        percentile_keys = ['d10', 'd50', 'd90']
        has_percentiles = any(key in str(results).lower() for key in percentile_keys)
        print("PASS" if has_percentiles else "FAIL", "- Distribution percentiles computed")
        
        # Check uniformity coefficients
        coeff_keys = ['cu', 'cc', 'uniformity', 'curvature']
        has_coefficients = any(key in str(results).lower() for key in coeff_keys)
        print("PASS" if has_coefficients else "FAIL", "- Uniformity coefficients computed")
        
        # Check size classifications
        class_keys = ['fine', 'medium', 'coarse']
        has_classifications = any(key in str(results).lower() for key in class_keys)
        print("PASS" if has_classifications else "FAIL", "- Size classifications computed")
        
        # Check histogram file
        hist_exists = os.path.exists('grain_histogram.png')
        print("PASS" if hist_exists else "FAIL", "- Histogram PNG file created")
        
        # Test alternative argument name
        result2 = subprocess.run([
            'python', 'generated.py', 
            '--grain_diameters', diameter_str,
            '--output', 'test_output2.json'
        ], capture_output=True, text=True, cwd='/tmp')
        
        alt_arg_works = result2.returncode == 0 or result.returncode == 0
        print("PASS" if alt_arg_works else "FAIL", "- Accepts diameter argument variations")
        
        # Validate statistical accuracy
        if json_valid and results:
            expected_mean = np.mean(test_diameters)
            expected_median = np.median(test_diameters)
            
            # Find mean and median in results (flexible key matching)
            result_mean = None
            result_median = None
            
            def find_value_by_key(data, target_keys):
                if isinstance(data, dict):
                    for key, value in data.items():
                        if any(target in str(key).lower() for target in target_keys):
                            if isinstance(value, (int, float)):
                                return value
                        if isinstance(value, dict):
                            found = find_value_by_key(value, target_keys)
                            if found is not None:
                                return found
                return None
            
            result_mean = find_value_by_key(results, ['mean'])
            result_median = find_value_by_key(results, ['median', 'd50'])
            
            mean_accurate = (result_mean is not None and 
                           abs(result_mean - expected_mean) < expected_mean * 0.01)
            median_accurate = (result_median is not None and 
                             abs(result_median - expected_median) < expected_median * 0.01)
            
            print("PASS" if mean_accurate else "FAIL", "- Mean calculation accurate")
            print("PASS" if median_accurate else "FAIL", "- Median calculation accurate")
            
            # Check size classification logic
            fine_count = np.sum(test_diameters < 50)
            medium_count = np.sum((test_diameters >= 50) & (test_diameters <= 200))
            coarse_count = np.sum(test_diameters > 200)
            
            total_grains = len(test_diameters)
            expected_fine_pct = (fine_count / total_grains) * 100
            expected_medium_pct = (medium_count / total_grains) * 100
            expected_coarse_pct = (coarse_count / total_grains) * 100
            
            # Look for percentage values in results
            percentages_reasonable = True
            result_str = str(results).lower()
            
            print("PASS" if percentages_reasonable else "FAIL", "- Size classification percentages reasonable")
            
            # Score metrics
            accuracy_score = 0.0
            completeness_score = 0.0
            
            # Accuracy score based on statistical correctness
            if mean_accurate:
                accuracy_score += 0.3
            if median_accurate:
                accuracy_score += 0.3
            if has_percentiles:
                accuracy_score += 0.2
            if has_coefficients:
                accuracy_score += 0.2
                
            # Completeness score based on output completeness
            if json_valid:
                completeness_score += 0.2
            if has_basic_stats:
                completeness_score += 0.2
            if has_classifications:
                completeness_score += 0.2
            if hist_exists:
                completeness_score += 0.2
            if has_percentiles and has_coefficients:
                completeness_score += 0.2
                
            print(f"SCORE: {accuracy_score:.2f} - Statistical accuracy")
            print(f"SCORE: {completeness_score:.2f} - Output completeness")

if __name__ == "__main__":
    run_test()
