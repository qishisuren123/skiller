import subprocess
import tempfile
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys

def create_data():
    """Generate synthetic test parameters"""
    return {
        'baseline_flux': 1e-6,
        'noise_level': 0.1,
        'duration_hours': 24,
        'resolution_minutes': 1
    }

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Test parameters
        data = create_data()
        json_file = "test_flares.json"
        plot_file = "test_plot.png"
        
        # Try different argument name variations
        cmd_variations = [
            ["python", "generated.py", "--output-json", json_file, "--output-plot", plot_file, 
             "--baseline-flux", str(data['baseline_flux']), "--noise-level", str(data['noise_level'])],
            ["python", "generated.py", "--output_json", json_file, "--output_plot", plot_file,
             "--baseline_flux", str(data['baseline_flux']), "--noise_level", str(data['noise_level'])],
            ["python", "generated.py", "-j", json_file, "-p", plot_file,
             "--baseline-flux", str(data['baseline_flux']), "--noise-level", str(data['noise_level'])]
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
            
        # Test 1: Check if JSON output file exists
        if os.path.exists(json_file):
            print("PASS: JSON output file created")
        else:
            print("FAIL: JSON output file not created")
            return
            
        # Test 2: Check if plot file exists
        if os.path.exists(plot_file):
            print("PASS: Plot file created")
        else:
            print("FAIL: Plot file not created")
            
        # Load and validate JSON data
        try:
            with open(json_file, 'r') as f:
                flare_data = json.load(f)
            print("PASS: JSON file is valid")
        except:
            print("FAIL: JSON file is invalid or corrupted")
            return
            
        # Test 3: Check if flare_data is a list
        if isinstance(flare_data, list):
            print("PASS: JSON contains list of flares")
        else:
            print("FAIL: JSON should contain a list of flares")
            return
            
        # Test 4: Check if flares were detected (should be 3-8)
        if 3 <= len(flare_data) <= 8:
            print("PASS: Reasonable number of flares detected")
        else:
            print("FAIL: Unexpected number of flares detected")
            
        # Test 5-10: Validate flare properties
        required_fields = ['start_time', 'peak_time', 'end_time', 'peak_flux', 'duration', 'classification']
        valid_flares = 0
        
        for i, flare in enumerate(flare_data):
            if all(field in flare for field in required_fields):
                valid_flares += 1
                
        if valid_flares == len(flare_data):
            print("PASS: All flares have required fields")
        else:
            print("FAIL: Some flares missing required fields")
            
        # Test 6: Check classification values
        valid_classes = ['C', 'M', 'X']
        classifications = [flare.get('classification', '') for flare in flare_data]
        if all(c in valid_classes for c in classifications):
            print("PASS: All classifications are valid (C, M, X)")
        else:
            print("FAIL: Invalid classification values found")
            
        # Test 7: Check duration values are positive
        durations = [flare.get('duration', 0) for flare in flare_data]
        if all(d > 0 for d in durations):
            print("PASS: All durations are positive")
        else:
            print("FAIL: Some durations are not positive")
            
        # Test 8: Check peak flux values are reasonable
        peak_fluxes = [flare.get('peak_flux', 0) for flare in flare_data]
        baseline = data['baseline_flux']
        if all(pf > baseline for pf in peak_fluxes):
            print("PASS: All peak fluxes exceed baseline")
        else:
            print("FAIL: Some peak fluxes do not exceed baseline")
            
        # Test 9: Check time ordering (start <= peak <= end)
        time_order_valid = True
        for flare in flare_data:
            start = flare.get('start_time', 0)
            peak = flare.get('peak_time', 0)
            end = flare.get('end_time', 0)
            if not (start <= peak <= end):
                time_order_valid = False
                break
                
        if time_order_valid:
            print("PASS: Time ordering is correct for all flares")
        else:
            print("FAIL: Time ordering is incorrect for some flares")
            
        # Test 10: Check minimum duration requirement (should be >= 5 minutes)
        min_duration_met = all(d >= 5 for d in durations)
        if min_duration_met:
            print("PASS: All flares meet minimum duration requirement")
        else:
            print("FAIL: Some flares below minimum duration requirement")
            
        # Test 11: Check classification consistency with peak flux
        classification_consistent = True
        for flare in flare_data:
            peak_flux = flare.get('peak_flux', 0)
            classification = flare.get('classification', '')
            ratio = peak_flux / baseline
            
            if classification == 'C' and not (1 <= ratio <= 10):
                classification_consistent = False
            elif classification == 'M' and not (10 < ratio <= 100):
                classification_consistent = False
            elif classification == 'X' and not (ratio > 100):
                classification_consistent = False
                
        if classification_consistent:
            print("PASS: Classifications consistent with peak flux ratios")
        else:
            print("FAIL: Some classifications inconsistent with peak flux ratios")
            
        # Test 12: Check plot file is valid image
        try:
            img = plt.imread(plot_file)
            print("PASS: Plot file is valid image")
        except:
            print("FAIL: Plot file is not a valid image")
            
        # SCORE 1: Detection accuracy (based on expected number of flares)
        expected_flares = 5.5  # middle of 3-8 range
        detection_score = max(0, 1 - abs(len(flare_data) - expected_flares) / expected_flares)
        print(f"SCORE: Detection accuracy: {detection_score:.3f}")
        
        # SCORE 2: Data completeness (fraction of flares with all required fields)
        completeness_score = valid_flares / max(1, len(flare_data))
        print(f"SCORE: Data completeness: {completeness_score:.3f}")

if __name__ == "__main__":
    run_test()
