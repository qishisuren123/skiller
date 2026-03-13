import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
from scipy.interpolate import RBFInterpolator
from scipy.stats import gaussian_kde
import h5py
import os
import subprocess
import tempfile
import json
from pathlib import Path

def create_data():
    """Generate synthetic hardness indentation data"""
    np.random.seed(42)
    
    # Create irregular sampling pattern with varying density
    n_points = 150
    
    # Dense cluster in center
    center_points = 60
    x_center = np.random.normal(50, 15, center_points)
    y_center = np.random.normal(50, 15, center_points)
    
    # Sparse points around edges
    edge_points = n_points - center_points
    x_edge = np.random.uniform(0, 100, edge_points)
    y_edge = np.random.uniform(0, 100, edge_points)
    
    x_coords = np.concatenate([x_center, x_edge])
    y_coords = np.concatenate([y_center, y_edge])
    
    # Generate realistic hardness field with spatial correlation
    # Base hardness field
    X, Y = np.meshgrid(np.linspace(0, 100, 50), np.linspace(0, 100, 50))
    base_field = 5 + 3 * np.sin(X/20) * np.cos(Y/15) + 2 * np.exp(-((X-70)**2 + (Y-30)**2)/400)
    
    # Interpolate to measurement points
    from scipy.interpolate import RegularGridInterpolator
    interp_func = RegularGridInterpolator((np.linspace(0, 100, 50), np.linspace(0, 100, 50)), 
                                        base_field.T, bounds_error=False, fill_value=5)
    
    hardness_values = interp_func(np.column_stack([x_coords, y_coords]))
    
    # Add noise and ensure positive values
    hardness_values += np.random.normal(0, 0.3, len(hardness_values))
    hardness_values = np.maximum(hardness_values, 1.0)
    
    # Add some invalid data points
    invalid_indices = np.random.choice(len(hardness_values), 5, replace=False)
    hardness_values[invalid_indices] = np.nan
    
    # Create DataFrame
    data = pd.DataFrame({
        'X_um': x_coords,
        'Y_um': y_coords, 
        'Hardness_GPa': hardness_values
    })
    
    return data

def run_test():
    results = {"PASS": 0, "FAIL": 0, "tests": []}
    
    def test_condition(name, condition, error_msg=""):
        if condition:
            results["PASS"] += 1
            results["tests"].append(f"PASS: {name}")
            return True
        else:
            results["FAIL"] += 1 
            results["tests"].append(f"FAIL: {name} - {error_msg}")
            return False
    
    # Create test data
    test_data = create_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Save input data
        input_file = tmpdir / "hardness_data.csv"
        test_data.to_csv(input_file, index=False)
        
        output_dir = tmpdir / "output"
        output_dir.mkdir()
        
        # Test different argument patterns
        cmd_patterns = [
            ["python", "generated.py", str(input_file), "--output", str(output_dir)],
            ["python", "generated.py", "--input", str(input_file), "--output-dir", str(output_dir)],
            ["python", "generated.py", "-i", str(input_file), "-o", str(output_dir)]
        ]
        
        success = False
        for cmd in cmd_patterns:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        test_condition("Script execution", success, "Script failed to run with any argument pattern")
        
        if not success:
            print("STDOUT:", result.stdout if 'result' in locals() else "No output")
            print("STDERR:", result.stderr if 'result' in locals() else "No output") 
            for test in results["tests"]:
                print(test)
            return
        
        # Test 1: Check HDF5 output files exist
        h5_files = list(output_dir.glob("*.h5")) + list(output_dir.glob("*.hdf5"))
        test_condition("HDF5 output files created", len(h5_files) > 0)
        
        # Test 2: Check PNG visualization files
        png_files = list(output_dir.glob("*.png"))
        test_condition("PNG visualization files created", len(png_files) > 0)
        
        if len(h5_files) > 0:
            h5_file = h5_files[0]
            
            try:
                with h5py.File(h5_file, 'r') as f:
                    # Test 3: Check for multiple interpolation methods
                    method_count = 0
                    methods = ['rbf', 'idw', 'kriging', 'gaussian', 'radial']
                    for method in methods:
                        if any(method.lower() in key.lower() for key in f.keys()):
                            method_count += 1
                    test_condition("Multiple interpolation methods", method_count >= 2, 
                                 f"Found {method_count} methods, need at least 2")
                    
                    # Test 4: Check for hardness maps
                    hardness_maps = []
                    for key in f.keys():
                        if 'hardness' in key.lower() or 'map' in key.lower():
                            if isinstance(f[key], h5py.Dataset) and len(f[key].shape) == 2:
                                hardness_maps.append(f[key][:])
                    
                    test_condition("2D hardness maps present", len(hardness_maps) > 0)
                    
                    # Test 5: Check for uncertainty maps  
                    uncertainty_maps = []
                    for key in f.keys():
                        if any(word in key.lower() for word in ['uncertainty', 'error', 'std', 'variance']):
                            if isinstance(f[key], h5py.Dataset) and len(f[key].shape) == 2:
                                uncertainty_maps.append(f[key][:])
                    
                    test_condition("Uncertainty maps present", len(uncertainty_maps) > 0)
                    
                    # Test 6: Check grid resolution adaptation
                    if hardness_maps:
                        map_shape = hardness_maps[0].shape
                        expected_min_size = 20
                        expected_max_size = 200
                        reasonable_size = (expected_min_size <= min(map_shape) and 
                                         max(map_shape) <= expected_max_size)
                        test_condition("Reasonable grid resolution", reasonable_size,
                                     f"Grid shape {map_shape} outside reasonable range")
                    
                    # Test 7: Check for valid hardness values
                    if hardness_maps:
                        valid_hardness = True
                        for hmap in hardness_maps:
                            if np.any(np.isnan(hmap)) or np.any(hmap <= 0) or np.any(hmap > 50):
                                valid_hardness = False
                                break
                        test_condition("Valid hardness value ranges", valid_hardness)
                    
                    # Test 8: Check for metadata
                    has_metadata = False
                    for key in f.keys():
                        if 'meta' in key.lower() or 'info' in key.lower():
                            has_metadata = True
                            break
                    # Also check for attributes
                    if not has_metadata:
                        has_metadata = len(f.attrs) > 0
                    test_condition("Metadata present", has_metadata)
                    
                    # Test 9: Check data filtering (should have fewer points than input)
                    valid_input_points = test_data.dropna().shape[0]
                    processed_points = None
                    
                    for key in f.keys():
                        if 'points' in key.lower() or 'data' in key.lower():
                            if isinstance(f[key], h5py.Dataset):
                                processed_points = f[key].shape[0]
                                break
                    
                    if processed_points is None and 'n_points' in f.attrs:
                        processed_points = f.attrs['n_points']
                    
                    if processed_points is not None:
                        test_condition("Data filtering applied", processed_points <= len(test_data))
                    else:
                        test_condition("Data filtering applied", True)  # Can't verify, assume pass
                    
            except Exception as e:
                test_condition("HDF5 file readable", False, str(e))
        
        # Test 10: Check PNG file quality
        if png_files:
            try:
                from PIL import Image
                img = Image.open(png_files[0])
                reasonable_size = img.size[0] >= 300 and img.size[1] >= 300
                test_condition("PNG visualization quality", reasonable_size)
            except:
                test_condition("PNG visualization quality", False, "Could not open PNG file")
        
        # Test 11: Check for statistical outputs
        stats_found = False
        json_files = list(output_dir.glob("*.json"))
        txt_files = list(output_dir.glob("*.txt"))
        
        if json_files or txt_files:
            stats_found = True
        elif h5_files:
            try:
                with h5py.File(h5_files[0], 'r') as f:
                    for key in f.keys():
                        if any(word in key.lower() for word in ['stats', 'summary', 'correlation', 'rmse']):
                            stats_found = True
                            break
            except:
                pass
        
        test_condition("Statistical analysis outputs", stats_found)
        
        # Test 12: Check for contour/overlay features in output
        advanced_viz = False
        if png_files and len(png_files) >= 2:
            advanced_viz = True
        elif png_files:
            # Check file size as proxy for complexity
            try:
                file_size = png_files[0].stat().st_size
                advanced_viz = file_size > 50000  # Assume complex plots are larger
            except:
                pass
        
        test_condition("Advanced visualization features", advanced_viz)
        
        # SCORE 1: Interpolation method diversity (0-1)
        method_diversity_score = min(method_count / 3.0, 1.0) if 'method_count' in locals() else 0
        
        # SCORE 2: Output completeness (0-1) 
        output_components = 0
        if len(h5_files) > 0: output_components += 1
        if len(png_files) > 0: output_components += 1
        if len(hardness_maps) > 0: output_components += 1
        if len(uncertainty_maps) > 0: output_components += 1
        if stats_found: output_components += 1
        
        completeness_score = min(output_components / 5.0, 1.0)
        
        print(f"SCORE: {method_diversity_score:.3f}")
        print(f"SCORE: {completeness_score:.3f}")
    
    # Print results
    for test in results["tests"]:
        print(test)

if __name__ == "__main__":
    run_test()
