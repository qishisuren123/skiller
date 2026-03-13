import os
import sys
import json
import tempfile
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

def create_data():
    """Generate synthetic asteroid observation data"""
    np.random.seed(42)
    
    # True orbital parameters for synthetic asteroid
    true_a = 2.5  # semi-major axis in AU
    true_b = 2.0  # semi-minor axis in AU
    center_x, center_y = 0.2, 0.1  # slight offset from Sun
    
    # Generate points along ellipse with noise
    n_obs = 25
    theta = np.linspace(0, 2*np.pi, n_obs)
    
    # Parametric ellipse equations
    x_true = center_x + true_a * np.cos(theta)
    y_true = center_y + true_b * np.sin(theta)
    
    # Add realistic measurement noise
    noise_level = 0.05
    x_obs = x_true + np.random.normal(0, noise_level, n_obs)
    y_obs = y_true + np.random.normal(0, noise_level, n_obs)
    
    # Create timestamps (days)
    timestamps = np.linspace(0, 365, n_obs)
    
    observations = {
        "timestamps": timestamps.tolist(),
        "x_coordinates": x_obs.tolist(),
        "y_coordinates": y_obs.tolist(),
        "units": "AU"
    }
    
    return observations, true_a, true_b

def ellipse_residuals(params, x, y):
    """Residual function for ellipse fitting"""
    h, k, a, b = params
    return ((x - h)/a)**2 + ((y - k)/b)**2 - 1

def fit_ellipse(x, y):
    """Fit ellipse to x,y data points"""
    # Initial guess
    x0 = [np.mean(x), np.mean(y), np.std(x)*2, np.std(y)*2]
    
    # Bounds to ensure positive semi-axes
    bounds = ([-np.inf, -np.inf, 0.1, 0.1], 
              [np.inf, np.inf, np.inf, np.inf])
    
    result = least_squares(ellipse_residuals, x0, args=(x, y), bounds=bounds)
    return result.x

def test_asteroid_orbit_calculator():
    results = {"PASS": 0, "FAIL": 0, "SCORE": {}}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test data
        obs_data, true_a, true_b = create_data()
        
        input_file = os.path.join(tmpdir, "observations.json")
        output_file = os.path.join(tmpdir, "orbital_elements.json")
        plot_file = os.path.join(tmpdir, "orbit_plot.png")
        
        with open(input_file, 'w') as f:
            json.dump(obs_data, f)
        
        # Test different argument name variations
        arg_variants = [
            ["--input", input_file, "--output", output_file, "--plot", plot_file],
            ["--observations", input_file, "--results", output_file, "--visualization", plot_file]
        ]
        
        success = False
        for args in arg_variants:
            try:
                result = subprocess.run([sys.executable, "generated.py"] + args, 
                                      capture_output=True, text=True, cwd=tmpdir, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        # Test 1: Script execution
        if success:
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Script execution failed")
            return results
        
        # Test 2: Output file creation
        if os.path.exists(output_file):
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Output JSON file not created")
        
        # Test 3: Plot file creation
        if os.path.exists(plot_file):
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Plot file not created")
        
        # Load and validate results
        try:
            with open(output_file, 'r') as f:
                orbital_data = json.load(f)
        except:
            results["FAIL"] += 10
            print(f"FAIL: Could not load output JSON")
            return results
        
        # Test 4: Required fields present
        required_fields = ["semi_major_axis", "semi_minor_axis", "eccentricity", "orbital_period"]
        if all(field in orbital_data for field in required_fields):
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Missing required orbital elements")
        
        # Test 5: Semi-major axis positive
        if orbital_data.get("semi_major_axis", 0) > 0:
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Semi-major axis not positive")
        
        # Test 6: Semi-minor axis positive
        if orbital_data.get("semi_minor_axis", 0) > 0:
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Semi-minor axis not positive")
        
        # Test 7: Eccentricity in valid range
        ecc = orbital_data.get("eccentricity", -1)
        if 0 <= ecc < 1:
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Eccentricity not in valid range [0,1)")
        
        # Test 8: Orbital period positive
        if orbital_data.get("orbital_period", 0) > 0:
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Orbital period not positive")
        
        # Test 9: Semi-major axis reasonable accuracy
        a_computed = orbital_data.get("semi_major_axis", 0)
        if abs(a_computed - true_a) < 0.5:
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Semi-major axis accuracy poor: {a_computed} vs {true_a}")
        
        # Test 10: Semi-minor axis reasonable accuracy  
        b_computed = orbital_data.get("semi_minor_axis", 0)
        if abs(b_computed - true_b) < 0.5:
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Semi-minor axis accuracy poor: {b_computed} vs {true_b}")
        
        # Test 11: Kepler's third law consistency
        T_computed = orbital_data.get("orbital_period", 0)
        T_expected = np.sqrt(a_computed**3)
        if abs(T_computed - T_expected) < 0.1:
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Kepler's third law not satisfied")
        
        # Test 12: R-squared present and reasonable
        r_squared = orbital_data.get("r_squared", -1)
        if r_squared > 0.8:
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: R-squared too low or missing: {r_squared}")
        
        # Test 13: Plot file has reasonable size
        if os.path.getsize(plot_file) > 1000:
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Plot file too small")
        
        # Test 14: Eccentricity calculation consistency
        e_expected = np.sqrt(1 - (b_computed/a_computed)**2) if a_computed > 0 else 0
        if abs(ecc - e_expected) < 0.01:
            results["PASS"] += 1
        else:
            results["FAIL"] += 1
            print(f"FAIL: Eccentricity calculation inconsistent")
        
        # SCORE 1: Orbital parameter accuracy
        a_error = abs(a_computed - true_a) / true_a if a_computed > 0 else 1
        b_error = abs(b_computed - true_b) / true_b if b_computed > 0 else 1
        accuracy_score = max(0, 1 - (a_error + b_error) / 2)
        results["SCORE"]["orbital_accuracy"] = accuracy_score
        
        # SCORE 2: Overall fit quality
        fit_score = max(0, r_squared) if r_squared >= 0 else 0
        results["SCORE"]["fit_quality"] = fit_score
    
    return results

if __name__ == "__main__":
    results = test_asteroid_orbit_calculator()
    print(f"PASS: {results['PASS']}")
    print(f"FAIL: {results['FAIL']}")
    for score_name, score_value in results["SCORE"].items():
        print(f"SCORE: {score_name}: {score_value:.3f}")
