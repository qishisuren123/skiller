import numpy as np
import json
import matplotlib.pyplot as plt
import subprocess
import tempfile
import os
import sys
from pathlib import Path

def create_data():
    """Generate synthetic CMB temperature map data"""
    # Create a synthetic HEALPix-like temperature map
    # Using Nside=8 gives 768 pixels (12*Nside^2)
    nside = 8
    npix = 12 * nside**2  # 768 pixels
    
    # Generate realistic CMB temperature fluctuations
    np.random.seed(42)
    
    # Create correlated temperature fluctuations
    # Simulate a simplified CMB power spectrum
    ell_max = int(np.sqrt(npix/12))  # ~8
    
    # Generate random a_lm coefficients with realistic CMB-like power
    temperature_map = np.zeros(npix)
    
    # Add large scale fluctuations (low ell)
    for i in range(npix):
        # Create spatially correlated temperature field
        theta = np.pi * i / npix  # simplified coordinate
        phi = 2 * np.pi * (i % int(np.sqrt(npix))) / np.sqrt(npix)
        
        # Add multiple scales of fluctuations
        temp = 0
        temp += 100 * np.cos(2*theta) * np.sin(phi)  # ell=2 mode
        temp += 50 * np.sin(3*theta) * np.cos(2*phi)  # ell=3 mode  
        temp += 30 * np.cos(4*theta) * np.sin(3*phi)  # ell=4 mode
        temp += 20 * np.random.normal(0, 1)  # noise
        
        temperature_map[i] = temp
    
    # Add overall random component
    temperature_map += np.random.normal(0, 10, npix)
    
    return temperature_map

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
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        cmb_data = create_data()
        input_file = "cmb_temperature_map.npy"
        np.save(input_file, cmb_data)
        
        output_json = "power_spectrum.json"
        output_plot = "power_spectrum.png"
        
        # Test 1: Check if script runs without errors
        try:
            # Try common argument patterns
            cmd_variants = [
                ["python", "generated.py", input_file, output_json, output_plot],
                ["python", "generated.py", "--input", input_file, "--output", output_json, "--plot", output_plot],
                ["python", "generated.py", "-i", input_file, "-o", output_json, "-p", output_plot],
                ["python", "generated.py", input_file, "--output-json", output_json, "--output-plot", output_plot]
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
            
            test_condition("Script execution", success, "Script failed to run with any argument pattern")
            
            if not success:
                print("STDOUT:", result.stdout if 'result' in locals() else "No output")
                print("STDERR:", result.stderr if 'result' in locals() else "No error")
                return results
                
        except Exception as e:
            test_condition("Script execution", False, f"Exception: {str(e)}")
            return results
        
        # Test 2: Check JSON output file exists
        json_exists = os.path.exists(output_json)
        test_condition("JSON output file created", json_exists)
        
        # Test 3: Check plot file exists  
        plot_exists = os.path.exists(output_plot)
        test_condition("Plot file created", plot_exists)
        
        if json_exists:
            try:
                with open(output_json, 'r') as f:
                    data = json.load(f)
                
                # Test 4: Check JSON structure
                has_ell = 'ell' in data or 'l' in data or 'multipole' in data
                test_condition("JSON contains multipole values", has_ell)
                
                # Test 5: Check power spectrum values
                has_cl = 'cl' in data or 'C_l' in data or 'power_spectrum' in data or 'power' in data
                test_condition("JSON contains power spectrum values", has_cl)
                
                # Get the data arrays
                ell_key = next((k for k in ['ell', 'l', 'multipole'] if k in data), None)
                cl_key = next((k for k in ['cl', 'C_l', 'power_spectrum', 'power'] if k in data), None)
                
                if ell_key and cl_key:
                    ell_values = np.array(data[ell_key])
                    cl_values = np.array(data[cl_key])
                    
                    # Test 6: Check multipole range starts at 2
                    starts_at_2 = len(ell_values) > 0 and min(ell_values) >= 2
                    test_condition("Multipole range starts at ell>=2", starts_at_2)
                    
                    # Test 7: Check reasonable multipole range
                    max_ell_reasonable = len(ell_values) > 0 and max(ell_values) <= 20
                    test_condition("Maximum multipole is reasonable", max_ell_reasonable)
                    
                    # Test 8: Check power spectrum values are positive
                    cl_positive = len(cl_values) > 0 and np.all(cl_values >= 0)
                    test_condition("Power spectrum values are non-negative", cl_positive)
                    
                    # Test 9: Check array lengths match
                    lengths_match = len(ell_values) == len(cl_values)
                    test_condition("Multipole and power spectrum arrays have same length", lengths_match)
                    
                    # Test 10: Check for statistics
                    has_stats = any(key in data for key in ['total_power', 'peak_multipole', 'rms', 'statistics'])
                    test_condition("JSON contains statistical analysis", has_stats)
                    
                    # Test 11: Check units (should be in μK²)
                    reasonable_units = len(cl_values) > 0 and np.mean(cl_values) > 1 and np.mean(cl_values) < 1e8
                    test_condition("Power spectrum values in reasonable range (μK²)", reasonable_units)
                    
                else:
                    for i in range(6, 12):
                        test_condition(f"Test {i} (data extraction failed)", False, "Could not extract ell/cl data")
                
            except Exception as e:
                test_condition("JSON file parsing", False, f"JSON parsing error: {str(e)}")
                for i in range(4, 12):
                    test_condition(f"Test {i} (JSON parsing failed)", False, "JSON parsing failed")
        else:
            for i in range(4, 12):
                test_condition(f"Test {i} (no JSON file)", False, "JSON file not created")
        
        # Test 12: Check plot file is valid
        if plot_exists:
            try:
                # Check file size is reasonable (not empty, not too large)
                plot_size = os.path.getsize(output_plot)
                reasonable_size = 1000 < plot_size < 10**7  # 1KB to 10MB
                test_condition("Plot file has reasonable size", reasonable_size)
            except:
                test_condition("Plot file has reasonable size", False, "Could not check plot file size")
        else:
            test_condition("Plot file has reasonable size", False, "Plot file not created")
        
        # Test 13: Check for proper argparse usage (help option)
        try:
            help_result = subprocess.run(["python", "generated.py", "--help"], 
                                       capture_output=True, text=True, timeout=10)
            has_help = help_result.returncode == 0 and "usage:" in help_result.stdout.lower()
            test_condition("Script provides help message", has_help)
        except:
            test_condition("Script provides help message", False, "Help option failed")
        
        # SCORE 1: Data processing accuracy (0-1)
        if json_exists:
            try:
                with open(output_json, 'r') as f:
                    data = json.load(f)
                
                # Check if processing seems reasonable
                score_components = []
                
                # Check if we have the right data structure
                ell_key = next((k for k in ['ell', 'l', 'multipole'] if k in data), None)
                cl_key = next((k for k in ['cl', 'C_l', 'power_spectrum', 'power'] if k in data), None)
                
                if ell_key and cl_key:
                    ell_values = np.array(data[ell_key])
                    cl_values = np.array(data[cl_key])
                    
                    # Score based on data quality
                    if len(ell_values) > 0 and len(cl_values) > 0:
                        score_components.append(0.3)  # Has data
                        
                        if min(ell_values) >= 2:
                            score_components.append(0.2)  # Correct ell range
                            
                        if np.all(cl_values >= 0):
                            score_components.append(0.2)  # Positive power
                            
                        if len(ell_values) == len(cl_values):
                            score_components.append(0.2)  # Matching lengths
                            
                        if 1 < np.mean(cl_values) < 1e8:
                            score_components.append(0.1)  # Reasonable values
                
                processing_score = sum(score_components)
                
            except:
                processing_score = 0.0
        else:
            processing_score = 0.0
            
        results["SCORE"] = results.get("SCORE", {})
        results["SCORE"]["Data processing accuracy"] = processing_score
        
        # SCORE 2: Output completeness (0-1)
        completeness_score = 0.0
        
        if json_exists:
            completeness_score += 0.4
            
        if plot_exists:
            completeness_score += 0.3
            
        if json_exists:
            try:
                with open(output_json, 'r') as f:
                    data = json.load(f)
                    
                # Check for statistical analysis
                if any(key in data for key in ['total_power', 'peak_multipole', 'rms', 'statistics']):
                    completeness_score += 0.3
                    
            except:
                pass
                
        results["SCORE"]["Output completeness"] = completeness_score
    
    return results

if __name__ == "__main__":
    results = run_test()
    
    print(f"PASS: {results['PASS']}")
    print(f"FAIL: {results['FAIL']}")
    
    for test in results["tests"]:
        print(test)
    
    for score_name, score_value in results.get("SCORE", {}).items():
        print(f"SCORE: {score_name}: {score_value:.3f}")
