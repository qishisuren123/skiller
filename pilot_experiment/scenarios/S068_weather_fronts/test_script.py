import subprocess
import tempfile
import os
import json
import numpy as np
import h5py
import matplotlib.pyplot as plt
from scipy import ndimage
import shutil

def create_data(temp_dir):
    """Create synthetic atmospheric temperature data with weather fronts"""
    # Create a 50x50 grid representing a 500km x 500km area
    nx, ny = 50, 50
    grid_spacing = 10.0  # km
    
    # Create coordinate arrays
    lat = np.linspace(40.0, 45.0, ny)
    lon = np.linspace(-100.0, -95.0, nx)
    
    # Create base temperature field with realistic values
    x, y = np.meshgrid(np.arange(nx), np.arange(ny))
    
    # Base temperature decreasing northward
    temp_base = 20.0 - 0.3 * y
    
    # Add a cold front (sharp temperature gradient)
    front_line = 15 + 8 * np.sin(0.3 * x)
    cold_front_mask = y > front_line
    temp_base[cold_front_mask] -= 8.0
    
    # Add a warm front (gentler gradient)
    warm_front_center = 35
    for i in range(ny):
        for j in range(nx):
            dist_to_warm_front = abs(i - warm_front_center + 2 * np.sin(0.2 * j))
            if dist_to_warm_front < 5:
                temp_base[i, j] += 4.0 * np.exp(-dist_to_warm_front**2 / 8.0)
    
    # Add some noise
    temp_base += np.random.normal(0, 0.5, (ny, nx))
    
    # Save to HDF5
    input_file = os.path.join(temp_dir, 'temperature_data.h5')
    with h5py.File(input_file, 'w') as f:
        f.create_dataset('temperature', data=temp_base)
        f.create_dataset('lat', data=lat)
        f.create_dataset('lon', data=lon)
        f.create_dataset('grid_spacing', data=grid_spacing)
    
    return input_file

def run_test():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test data
        input_file = create_data(temp_dir)
        output_json = os.path.join(temp_dir, 'fronts.json')
        output_plot = os.path.join(temp_dir, 'front_plot.png')
        
        # Test different argument name variations
        possible_args = [
            ['--input-data', '--output-fronts', '--output-plot'],
            ['--input_data', '--output_fronts', '--output_plot'],
            ['--input', '--fronts', '--plot'],
            ['--data', '--output-json', '--output-png']
        ]
        
        success = False
        for args in possible_args:
            try:
                cmd = [
                    'python', 'generated.py',
                    args[0], input_file,
                    args[1], output_json,
                    args[2], output_plot,
                    '--gradient-threshold', '1.5',
                    '--min-front-length', '4',
                    '--smoothing-sigma', '1.2'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            # Try with minimal args
            try:
                cmd = ['python', 'generated.py', input_file, output_json, output_plot]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                success = result.returncode == 0
            except:
                pass
        
        # Load original data for validation
        with h5py.File(input_file, 'r') as f:
            temp_data = f['temperature'][:]
            grid_spacing = f['grid_spacing'][()]
        
        # Test results
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Script runs successfully
        total_tests += 1
        if success:
            tests_passed += 1
            print("PASS: Script executed successfully")
        else:
            print("FAIL: Script failed to execute")
        
        # Test 2: JSON output file exists
        total_tests += 1
        if os.path.exists(output_json):
            tests_passed += 1
            print("PASS: JSON output file created")
        else:
            print("FAIL: JSON output file not created")
            return tests_passed, total_tests, 0.0, 0.0
        
        # Test 3: Plot output file exists
        total_tests += 1
        if os.path.exists(output_plot):
            tests_passed += 1
            print("PASS: Plot output file created")
        else:
            print("FAIL: Plot output file not created")
        
        # Load and validate JSON output
        try:
            with open(output_json, 'r') as f:
                front_data = json.load(f)
        except:
            print("FAIL: Could not load JSON output")
            return tests_passed, total_tests, 0.0, 0.0
        
        # Test 4: JSON has required structure
        total_tests += 1
        if isinstance(front_data, dict) and 'fronts' in front_data:
            tests_passed += 1
            print("PASS: JSON has correct structure")
        else:
            print("FAIL: JSON structure incorrect")
        
        fronts = front_data.get('fronts', [])
        
        # Test 5: At least one front detected
        total_tests += 1
        if len(fronts) > 0:
            tests_passed += 1
            print("PASS: At least one front detected")
        else:
            print("FAIL: No fronts detected")
        
        # Test 6: Front data contains required fields
        total_tests += 1
        valid_fronts = 0
        for front in fronts:
            if all(key in front for key in ['coordinates', 'gradient_strength', 'length']):
                valid_fronts += 1
        
        if valid_fronts == len(fronts) and len(fronts) > 0:
            tests_passed += 1
            print("PASS: All fronts have required fields")
        else:
            print("FAIL: Fronts missing required fields")
        
        # Test 7: Coordinates are reasonable
        total_tests += 1
        coord_valid = True
        for front in fronts:
            coords = front.get('coordinates', [])
            if not coords or not all(len(coord) == 2 for coord in coords):
                coord_valid = False
                break
            # Check if coordinates are within grid bounds
            for coord in coords:
                if not (0 <= coord[0] < temp_data.shape[1] and 0 <= coord[1] < temp_data.shape[0]):
                    coord_valid = False
                    break
        
        if coord_valid:
            tests_passed += 1
            print("PASS: Front coordinates are valid")
        else:
            print("FAIL: Invalid front coordinates")
        
        # Test 8: Gradient strengths are positive
        total_tests += 1
        gradient_valid = all(front.get('gradient_strength', 0) > 0 for front in fronts)
        if gradient_valid and len(fronts) > 0:
            tests_passed += 1
            print("PASS: Gradient strengths are positive")
        else:
            print("FAIL: Invalid gradient strengths")
        
        # Test 9: Front lengths meet minimum requirement
        total_tests += 1
        length_valid = all(front.get('length', 0) >= 4 for front in fronts)
        if length_valid and len(fronts) > 0:
            tests_passed += 1
            print("PASS: Front lengths meet minimum requirement")
        else:
            print("FAIL: Some fronts too short")
        
        # Test 10: Reasonable number of fronts (not too many)
        total_tests += 1
        if 1 <= len(fronts) <= 20:
            tests_passed += 1
            print("PASS: Reasonable number of fronts detected")
        else:
            print("FAIL: Unreasonable number of fronts")
        
        # Test 11: Plot file is valid PNG
        total_tests += 1
        try:
            from PIL import Image
            img = Image.open(output_plot)
            if img.format == 'PNG':
                tests_passed += 1
                print("PASS: Valid PNG plot created")
            else:
                print("FAIL: Plot is not PNG format")
        except:
            print("FAIL: Could not open plot file")
        
        # Test 12: Gradient strengths are reasonable
        total_tests += 1
        reasonable_gradients = all(0.5 <= front.get('gradient_strength', 0) <= 20.0 for front in fronts)
        if reasonable_gradients and len(fronts) > 0:
            tests_passed += 1
            print("PASS: Gradient strengths are reasonable")
        else:
            print("FAIL: Gradient strengths out of reasonable range")
        
        # Calculate scores
        # Score 1: Detection accuracy (based on expected front locations)
        detection_score = 0.0
        if len(fronts) > 0:
            # Check if fronts are detected in expected regions
            expected_regions = [(15, 25), (30, 40)]  # y-ranges where fronts should be
            detected_regions = []
            
            for front in fronts:
                coords = front.get('coordinates', [])
                if coords:
                    avg_y = np.mean([coord[1] for coord in coords])
                    detected_regions.append(avg_y)
            
            matches = 0
            for expected_y_min, expected_y_max in expected_regions:
                for detected_y in detected_regions:
                    if expected_y_min <= detected_y <= expected_y_max:
                        matches += 1
                        break
            
            detection_score = min(matches / len(expected_regions), 1.0)
        
        # Score 2: Processing quality (gradient computation accuracy)
        processing_score = 0.0
        if len(fronts) > 0:
            # Calculate actual gradients at detected front locations
            gy, gx = np.gradient(temp_data)
            gradient_magnitude = np.sqrt(gx**2 + gy**2) * (1.0 / grid_spacing)
            
            total_gradient_error = 0.0
            total_points = 0
            
            for front in fronts:
                coords = front.get('coordinates', [])
                reported_strength = front.get('gradient_strength', 0)
                
                if coords:
                    actual_gradients = []
                    for coord in coords:
                        x, y = int(coord[0]), int(coord[1])
                        if 0 <= x < gradient_magnitude.shape[1] and 0 <= y < gradient_magnitude.shape[0]:
                            actual_gradients.append(gradient_magnitude[y, x])
                    
                    if actual_gradients:
                        avg_actual = np.mean(actual_gradients)
                        error = abs(reported_strength - avg_actual) / max(avg_actual, 0.1)
                        total_gradient_error += error
                        total_points += 1
            
            if total_points > 0:
                avg_error = total_gradient_error / total_points
                processing_score = max(0.0, 1.0 - avg_error)
        
        print(f"SCORE: {detection_score:.3f}")
        print(f"SCORE: {processing_score:.3f}")
        
        return tests_passed, total_tests, detection_score, processing_score

if __name__ == "__main__":
    run_test()
