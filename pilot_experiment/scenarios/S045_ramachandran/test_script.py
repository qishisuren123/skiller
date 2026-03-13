import subprocess
import tempfile
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.spatial.distance import cdist
import argparse

def create_data():
    """Generate synthetic protein dihedral angle data"""
    np.random.seed(42)
    
    # Expected number of residues for testing
    n_residues = 300
    
    # Generate realistic phi/psi distributions
    # Alpha helix region (60% of residues)
    n_alpha = int(0.6 * n_residues)
    phi_alpha = np.random.normal(-60, 15, n_alpha)
    psi_alpha = np.random.normal(-45, 15, n_alpha)
    
    # Beta sheet region (25% of residues)
    n_beta = int(0.25 * n_residues)
    phi_beta = np.random.normal(-120, 20, n_beta)
    psi_beta = np.random.normal(120, 20, n_beta)
    
    # Random/loop regions (10% of residues)
    n_loop = int(0.1 * n_residues)
    phi_loop = np.random.uniform(-180, 180, n_loop)
    psi_loop = np.random.uniform(-180, 180, n_loop)
    
    # Outliers (5% of residues)
    n_outliers = n_residues - n_alpha - n_beta - n_loop
    phi_outliers = np.random.uniform(-180, 180, n_outliers)
    psi_outliers = np.random.uniform(-180, 180, n_outliers)
    
    # Combine all data
    phi_angles = np.concatenate([phi_alpha, phi_beta, phi_loop, phi_outliers])
    psi_angles = np.concatenate([psi_alpha, psi_beta, psi_loop, psi_outliers])
    
    # Ensure angles are in [-180, 180] range
    phi_angles = ((phi_angles + 180) % 360) - 180
    psi_angles = ((psi_angles + 180) % 360) - 180
    
    return phi_angles, psi_angles, n_residues

def test_ramachandran_analysis():
    phi_angles, psi_angles, expected_residues = create_data()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        plot_file = os.path.join(temp_dir, "ramachandran.png")
        data_file = os.path.join(temp_dir, "analysis.json")
        
        # Test with default parameters
        cmd = [
            "python", "generated.py",
            "--num_residues", str(expected_residues),
            "--output_plot", plot_file,
            "--output_data", data_file,
            "--outlier_threshold", "2.0"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"FAIL: Script execution failed: {result.stderr}")
                return
        except subprocess.TimeoutExpired:
            print("FAIL: Script execution timed out")
            return
        except Exception as e:
            print(f"FAIL: Script execution error: {e}")
            return
        
        # Test 1: Check if plot file is created
        if os.path.exists(plot_file):
            print("PASS: Ramachandran plot file created")
        else:
            print("FAIL: Ramachandran plot file not created")
        
        # Test 2: Check if data file is created
        if os.path.exists(data_file):
            print("PASS: Analysis data file created")
        else:
            print("FAIL: Analysis data file not created")
            return
        
        # Load and validate JSON data
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"FAIL: Could not load JSON data: {e}")
            return
        
        # Test 3: Check required fields in JSON
        required_fields = ['phi_angles', 'psi_angles', 'outliers', 'statistics']
        missing_fields = [field for field in required_fields if field not in data]
        if not missing_fields:
            print("PASS: All required JSON fields present")
        else:
            print(f"FAIL: Missing JSON fields: {missing_fields}")
        
        # Test 4: Check data dimensions
        phi_data = data.get('phi_angles', [])
        psi_data = data.get('psi_angles', [])
        if len(phi_data) == expected_residues and len(psi_data) == expected_residues:
            print("PASS: Correct number of residues generated")
        else:
            print(f"FAIL: Expected {expected_residues} residues, got phi:{len(phi_data)}, psi:{len(psi_data)}")
        
        # Test 5: Check angle ranges
        phi_valid = all(-180 <= angle <= 180 for angle in phi_data)
        psi_valid = all(-180 <= angle <= 180 for angle in psi_data)
        if phi_valid and psi_valid:
            print("PASS: All angles within valid range [-180, 180]")
        else:
            print("FAIL: Some angles outside valid range")
        
        # Test 6: Check outlier detection
        outliers = data.get('outliers', [])
        if isinstance(outliers, list) and len(outliers) >= 0:
            print("PASS: Outlier detection completed")
        else:
            print("FAIL: Invalid outlier data")
        
        # Test 7: Check statistics structure
        stats_data = data.get('statistics', {})
        expected_stats = ['alpha_helix_percent', 'beta_sheet_percent', 'disallowed_percent']
        stats_present = all(stat in stats_data for stat in expected_stats)
        if stats_present:
            print("PASS: Required statistics calculated")
        else:
            print("FAIL: Missing required statistics")
        
        # Test 8: Validate percentage values
        percentages = [stats_data.get(stat, -1) for stat in expected_stats]
        valid_percentages = all(0 <= p <= 100 for p in percentages)
        if valid_percentages:
            print("PASS: Statistics percentages in valid range")
        else:
            print("FAIL: Invalid percentage values")
        
        # Test 9: Check plot file size (should contain actual plot data)
        if os.path.getsize(plot_file) > 1000:  # Reasonable minimum size for PNG
            print("PASS: Plot file has reasonable size")
        else:
            print("FAIL: Plot file too small, likely empty")
        
        # Test 10: Test alternative argument formats
        plot_file2 = os.path.join(temp_dir, "rama2.png")
        data_file2 = os.path.join(temp_dir, "data2.json")
        
        cmd2 = [
            "python", "generated.py",
            "--num-residues", "200",
            "--output-plot", plot_file2,
            "--output-data", data_file2,
            "--outlier-threshold", "3.0"
        ]
        
        try:
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
            if result2.returncode == 0 and os.path.exists(plot_file2):
                print("PASS: Alternative argument format accepted")
            else:
                print("FAIL: Alternative argument format not handled")
        except:
            print("FAIL: Alternative argument format caused error")
        
        # Test 11: Validate outlier threshold effect
        if os.path.exists(data_file2):
            try:
                with open(data_file2, 'r') as f:
                    data2 = json.load(f)
                outliers2 = data2.get('outliers', [])
                # Higher threshold should generally result in fewer outliers
                print("PASS: Outlier threshold parameter processed")
            except:
                print("FAIL: Could not validate outlier threshold effect")
        else:
            print("FAIL: Second analysis file not created")
        
        # Test 12: Check for reasonable structural distribution
        alpha_pct = stats_data.get('alpha_helix_percent', 0)
        beta_pct = stats_data.get('beta_sheet_percent', 0)
        if alpha_pct > 0 and beta_pct > 0:
            print("PASS: Detected both alpha helix and beta sheet regions")
        else:
            print("FAIL: Unrealistic structural region detection")
        
        # Test 13: Validate outlier indices
        if outliers and all(isinstance(idx, int) and 0 <= idx < expected_residues for idx in outliers):
            print("PASS: Outlier indices are valid")
        else:
            print("FAIL: Invalid outlier indices")
        
        # SCORE 1: Data quality score
        angle_std = np.std(phi_data + psi_data)
        data_quality = min(1.0, angle_std / 100.0)  # Normalize by expected std
        print(f"SCORE: Data quality: {data_quality:.3f}")
        
        # SCORE 2: Analysis completeness score
        completeness_factors = [
            len(phi_data) == expected_residues,
            len(outliers) > 0,
            alpha_pct > 0,
            beta_pct > 0,
            os.path.exists(plot_file),
            len(stats_data) >= 3
        ]
        completeness = sum(completeness_factors) / len(completeness_factors)
        print(f"SCORE: Analysis completeness: {completeness:.3f}")

if __name__ == "__main__":
    test_ramachandran_analysis()
