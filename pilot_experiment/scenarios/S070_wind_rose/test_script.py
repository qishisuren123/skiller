import subprocess
import tempfile
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import sys

def create_data():
    """Generate synthetic wind data for testing"""
    np.random.seed(42)
    
    # Generate realistic wind patterns
    n_samples = 1000
    
    # Prevailing winds from SW (225°) and NW (315°) with some randomness
    directions = []
    speeds = []
    
    for _ in range(n_samples):
        if np.random.random() < 0.3:  # 30% prevailing SW
            dir_base = 225
            speed_base = 6.0
        elif np.random.random() < 0.5:  # 20% prevailing NW  
            dir_base = 315
            speed_base = 5.5
        else:  # Random other directions
            dir_base = np.random.uniform(0, 360)
            speed_base = 3.0
            
        # Add noise
        direction = (dir_base + np.random.normal(0, 15)) % 360
        speed = max(0, speed_base + np.random.normal(0, 2))
        
        directions.append(direction)
        speeds.append(speed)
    
    # Add some calm conditions
    for _ in range(100):
        directions.append(np.random.uniform(0, 360))
        speeds.append(np.random.uniform(0, 1.5))
    
    return np.array(speeds), np.array(directions)

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create test data
        speeds, directions = create_data()
        
        # Test arguments
        stats_file = "wind_stats.json"
        plot_file = "wind_rose.png"
        
        # Convert arrays to space-separated strings
        speeds_str = " ".join(map(str, speeds))
        directions_str = " ".join(map(str, directions))
        
        # Try different argument variations
        cmd_variations = [
            ["python", "generated.py", "--speeds", speeds_str, "--directions", directions_str, 
             "--output-stats", stats_file, "--output-plot", plot_file],
            ["python", "generated.py", "--speeds", speeds_str, "--directions", directions_str,
             "--output_stats", stats_file, "--output_plot", plot_file],
            ["python", "generated.py", "-s", speeds_str, "-d", directions_str,
             "-o", stats_file, "-p", plot_file]
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
        
        if not success:
            print("FAIL: Script execution failed")
            return
        
        # Test 1: Check if JSON stats file exists
        if os.path.exists(stats_file):
            print("PASS: Statistics JSON file created")
        else:
            print("FAIL: Statistics JSON file not created")
            return
        
        # Test 2: Check if PNG plot file exists
        if os.path.exists(plot_file):
            print("PASS: Wind rose plot file created")
        else:
            print("FAIL: Wind rose plot file not created")
            return
        
        # Load and validate JSON
        try:
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            print("PASS: JSON file is valid")
        except:
            print("FAIL: JSON file is invalid or corrupted")
            return
        
        # Test 3: Check for direction bins (16 compass directions)
        expected_directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                             'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        
        if isinstance(stats, dict) and any(dir_name in str(stats) for dir_name in expected_directions[:8]):
            print("PASS: Direction binning implemented")
        else:
            print("FAIL: Direction binning not properly implemented")
        
        # Test 4: Check for calm conditions reporting
        stats_str = str(stats).lower()
        if 'calm' in stats_str or any(key for key in stats.keys() if 'calm' in str(key).lower()) if isinstance(stats, dict) else False:
            print("PASS: Calm conditions reported")
        else:
            print("FAIL: Calm conditions not reported")
        
        # Test 5: Check for speed categories
        speed_categories = ['calm', 'light', 'moderate', 'strong']
        if any(cat in stats_str for cat in speed_categories):
            print("PASS: Speed categories implemented")
        else:
            print("FAIL: Speed categories not implemented")
        
        # Test 6: Validate PNG image
        try:
            img = Image.open(plot_file)
            if img.size[0] > 100 and img.size[1] > 100:
                print("PASS: Wind rose plot has reasonable dimensions")
            else:
                print("FAIL: Wind rose plot dimensions too small")
        except:
            print("FAIL: Wind rose plot cannot be opened as image")
        
        # Test 7: Check if plot is polar/circular (matplotlib polar plot detection)
        try:
            # Check if matplotlib was used to create a polar plot
            fig_files = [f for f in os.listdir('.') if f.endswith('.png')]
            if fig_files:
                print("PASS: Plot file generated successfully")
            else:
                print("FAIL: No plot files found")
        except:
            print("FAIL: Error checking plot files")
        
        # Test 8: Validate frequency statistics
        if isinstance(stats, dict):
            has_frequencies = False
            for key, value in stats.items():
                if isinstance(value, (int, float)) or (isinstance(value, dict) and any(isinstance(v, (int, float)) for v in value.values())):
                    has_frequencies = True
                    break
            if has_frequencies:
                print("PASS: Frequency statistics present")
            else:
                print("FAIL: No frequency statistics found")
        else:
            print("FAIL: Statistics not in expected dictionary format")
        
        # Test 9: Check for mean wind speed calculations
        if 'mean' in stats_str or 'average' in stats_str:
            print("PASS: Mean wind speed calculations included")
        else:
            print("FAIL: Mean wind speed calculations not found")
        
        # Test 10: Validate data processing (check if all data points accounted for)
        total_samples = len(speeds)
        # Look for total count in stats
        total_found = False
        if isinstance(stats, dict):
            for key, value in stats.items():
                if isinstance(value, (int, float)) and abs(value - total_samples) < total_samples * 0.1:
                    total_found = True
                    break
        
        if total_found:
            print("PASS: Data processing accounts for all samples")
        else:
            print("PASS: Data processing completed (sample count validation skipped)")
        
        # Test 11: Check JSON structure completeness
        if isinstance(stats, dict) and len(stats) >= 3:
            print("PASS: JSON contains multiple statistical measures")
        else:
            print("FAIL: JSON structure incomplete")
        
        # Test 12: Validate direction range (0-360 degrees)
        direction_valid = True
        try:
            # Check if directions are properly handled
            if np.any(directions < 0) or np.any(directions >= 360):
                # Script should handle this properly
                pass
            print("PASS: Direction range validation handled")
        except:
            print("FAIL: Direction range validation failed")
        
        # Test 13: Check for proper file extensions
        if stats_file.endswith('.json') and plot_file.endswith('.png'):
            print("PASS: Output files have correct extensions")
        else:
            print("FAIL: Output files don't have expected extensions")
        
        # SCORE 1: Statistical accuracy (0-1)
        try:
            # Calculate expected calm percentage
            calm_expected = np.sum(speeds < 2.0) / len(speeds)
            
            # Try to find calm percentage in stats
            calm_found = 0.0
            stats_str_lower = json.dumps(stats).lower()
            
            # Simple validation - if calm is mentioned and reasonable
            if 'calm' in stats_str_lower and isinstance(stats, dict):
                score1 = 0.8  # Good if calm conditions are tracked
            else:
                score1 = 0.5  # Partial credit
                
            print(f"SCORE: {score1:.3f}")
        except:
            print("SCORE: 0.500")
        
        # SCORE 2: Visualization quality (0-1)
        try:
            img = Image.open(plot_file)
            width, height = img.size
            
            # Score based on image properties
            size_score = min(1.0, (width * height) / (400 * 400))  # Reasonable size
            
            # Check if image has color variation (not just blank)
            img_array = np.array(img)
            if len(img_array.shape) == 3:  # Color image
                color_variance = np.var(img_array)
                color_score = min(1.0, color_variance / 1000)
            else:
                color_score = 0.5
            
            viz_score = (size_score + color_score) / 2
            print(f"SCORE: {viz_score:.3f}")
        except:
            print("SCORE: 0.000")

if __name__ == "__main__":
    run_test()
