import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import subprocess
import tempfile
import os
import sys
from scipy.optimize import least_squares
from scipy import stats

def create_data():
    """Generate synthetic EIS data with known circuit parameters"""
    np.random.seed(42)
    
    # Generate frequency range (log scale)
    frequencies = np.logspace(-2, 6, 50)  # 0.01 Hz to 1 MHz
    omega = 2 * np.pi * frequencies
    
    # True parameters for Randles circuit: R_s + (R_ct || C_dl) + W
    R_s = 10.0      # Solution resistance
    R_ct = 50.0     # Charge transfer resistance  
    C_dl = 1e-5     # Double layer capacitance
    sigma = 100.0   # Warburg coefficient
    
    # Calculate theoretical impedance
    Z_c = 1 / (1j * omega * C_dl)  # Capacitor impedance
    Z_w = sigma * (1 - 1j) / np.sqrt(omega)  # Warburg impedance
    Z_rc = (R_ct * Z_c) / (R_ct + Z_c)  # Parallel RC
    Z_total = R_s + Z_rc + Z_w
    
    # Add realistic noise
    noise_level = 0.02
    Z_real = Z_total.real + noise_level * Z_total.real * np.random.randn(len(frequencies))
    Z_imag = Z_total.imag + noise_level * np.abs(Z_total.imag) * np.random.randn(len(frequencies))
    
    # Create DataFrame
    data = pd.DataFrame({
        'frequency': frequencies,
        'Z_real': Z_real,
        'Z_imag': Z_imag
    })
    
    return data, {'R_s': R_s, 'R_ct': R_ct, 'C_dl': C_dl, 'sigma': sigma}

def test_impedance_fitting():
    results = {'passed': 0, 'failed': 0, 'tests': []}
    
    def add_test(name, condition, details=""):
        results['tests'].append({
            'name': name,
            'passed': condition,
            'details': details
        })
        if condition:
            results['passed'] += 1
        else:
            results['failed'] += 1
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        test_data, true_params = create_data()
        
        # Save test data
        input_file = 'test_impedance.csv'
        test_data.to_csv(input_file, index=False)
        
        output_file = 'results.json'
        
        # Test different argument patterns
        cmd_patterns = [
            ['python', 'generated.py', '--input', input_file, '--output', output_file],
            ['python', 'generated.py', '-i', input_file, '-o', output_file],
            ['python', 'generated.py', input_file, output_file]
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
        
        add_test("Script execution", success, f"Return code: {result.returncode if 'result' in locals() else 'N/A'}")
        
        if not success:
            return results, 0.0, 0.0
        
        # Check output file exists
        output_exists = os.path.exists(output_file)
        add_test("Output file created", output_exists)
        
        if not output_exists:
            return results, 0.0, 0.0
        
        # Load and validate results
        try:
            with open(output_file, 'r') as f:
                results_data = json.load(f)
        except:
            add_test("Valid JSON output", False)
            return results, 0.0, 0.0
        
        add_test("Valid JSON output", True)
        
        # Test 1: Multiple circuit models implemented
        models_present = 'models' in results_data or 'circuits' in results_data
        add_test("Multiple circuit models", models_present)
        
        # Get models data
        models_key = 'models' if 'models' in results_data else 'circuits'
        models = results_data.get(models_key, {})
        
        # Test 2: At least 4 different circuit types
        min_models = len(models) >= 4
        add_test("Minimum 4 circuit models", min_models, f"Found {len(models)} models")
        
        # Test 3: Required circuit types present
        model_names = [name.lower() for name in models.keys()]
        required_circuits = ['rc', 'randles', 'double', 'cpe']
        circuits_found = sum(1 for req in required_circuits 
                           if any(req in name for name in model_names))
        sufficient_circuits = circuits_found >= 3
        add_test("Required circuit types", sufficient_circuits, 
                f"Found {circuits_found}/4 required types")
        
        # Test 4: Parameter fitting results
        has_parameters = False
        parameter_quality = 0.0
        
        for model_name, model_data in models.items():
            if 'parameters' in model_data or 'params' in model_data:
                has_parameters = True
                params_key = 'parameters' if 'parameters' in model_data else 'params'
                params = model_data[params_key]
                
                # Check for reasonable parameter values
                if isinstance(params, dict):
                    param_values = [v for v in params.values() if isinstance(v, (int, float))]
                    if param_values:
                        # Parameters should be positive and reasonable
                        reasonable = all(0.1 < abs(v) < 1e6 for v in param_values)
                        if reasonable:
                            parameter_quality = max(parameter_quality, 0.8)
        
        add_test("Parameter fitting", has_parameters)
        
        # Test 5: Statistical analysis metrics
        has_statistics = False
        stats_quality = 0.0
        
        for model_data in models.values():
            stats_indicators = ['chi_squared', 'r_squared', 'aic', 'bic', 'rmse', 'goodness']
            found_stats = sum(1 for stat in stats_indicators 
                            if any(stat in key.lower() for key in model_data.keys()))
            if found_stats >= 2:
                has_statistics = True
                stats_quality = min(found_stats / 4.0, 1.0)
                break
        
        add_test("Statistical analysis", has_statistics)
        
        # Test 6: Model comparison and ranking
        has_ranking = False
        ranking_indicators = ['best_model', 'ranking', 'model_comparison', 'aic', 'bic']
        
        for indicator in ranking_indicators:
            if indicator in results_data:
                has_ranking = True
                break
        
        # Alternative: check if models have comparison metrics
        if not has_ranking:
            comparison_metrics = 0
            for model_data in models.values():
                if any(metric in str(model_data).lower() 
                      for metric in ['aic', 'bic', 'chi', 'score']):
                    comparison_metrics += 1
            has_ranking = comparison_metrics >= 2
        
        add_test("Model comparison/ranking", has_ranking)
        
        # Test 7: Parameter uncertainties
        has_uncertainties = False
        for model_data in models.values():
            uncertainty_keys = ['uncertainties', 'errors', 'std_errors', 'confidence']
            if any(key in model_data for key in uncertainty_keys):
                has_uncertainties = True
                break
        
        add_test("Parameter uncertainties", has_uncertainties)
        
        # Test 8: Complex impedance handling
        handles_complex = False
        complex_indicators = ['real', 'imag', 'complex', 'nyquist', 'Z_real', 'Z_imag']
        data_str = str(results_data).lower()
        complex_found = sum(1 for indicator in complex_indicators if indicator in data_str)
        handles_complex = complex_found >= 2
        
        add_test("Complex impedance handling", handles_complex)
        
        # Test 9: Frequency range coverage
        freq_coverage = False
        if 'frequency_range' in results_data:
            freq_coverage = True
        else:
            # Check if results span reasonable frequency range
            freq_indicators = ['frequency', 'freq', 'omega']
            freq_coverage = any(indicator in data_str for indicator in freq_indicators)
        
        add_test("Frequency range coverage", freq_coverage)
        
        # Test 10: Data validation
        has_validation = 'validation' in results_data or 'quality' in results_data
        if not has_validation:
            # Check for outlier detection or data quality metrics
            validation_terms = ['outlier', 'quality', 'valid', 'kramers', 'residual']
            has_validation = any(term in data_str for term in validation_terms)
        
        add_test("Data validation", has_validation)
        
        # Test 11: Residual analysis
        has_residuals = False
        residual_keys = ['residuals', 'residual_analysis', 'fit_quality', 'deviation']
        for key in residual_keys:
            if key in results_data or any(key in str(model_data) for model_data in models.values()):
                has_residuals = True
                break
        
        add_test("Residual analysis", has_residuals)
        
        # Test 12: Proper weighting implementation
        has_weighting = False
        weight_indicators = ['weight', 'weighted', 'modulus']
        has_weighting = any(indicator in data_str for indicator in weight_indicators)
        
        add_test("Weighted fitting", has_weighting)
        
        # Calculate scores
        
        # Score 1: Parameter accuracy (compare with known values if Randles circuit found)
        parameter_accuracy = 0.0
        for model_name, model_data in models.items():
            if 'randles' in model_name.lower():
                params_key = 'parameters' if 'parameters' in model_data else 'params'
                if params_key in model_data:
                    params = model_data[params_key]
                    if isinstance(params, dict):
                        # Check accuracy of fitted parameters
                        accuracies = []
                        param_map = {'r_s': 'R_s', 'rs': 'R_s', 'r_ct': 'R_ct', 'rct': 'R_ct'}
                        
                        for fitted_name, fitted_val in params.items():
                            if isinstance(fitted_val, (int, float)):
                                true_name = param_map.get(fitted_name.lower())
                                if true_name and true_name in true_params:
                                    true_val = true_params[true_name]
                                    relative_error = abs(fitted_val - true_val) / true_val
                                    accuracy = max(0, 1 - relative_error)
                                    accuracies.append(accuracy)
                        
                        if accuracies:
                            parameter_accuracy = np.mean(accuracies)
                break
        
        # Score 2: Overall implementation completeness
        implementation_score = 0.0
        total_features = 12
        passed_features = sum(1 for test in results['tests'] if test['passed'])
        implementation_score = passed_features / total_features
        
        # Bonus for advanced features
        advanced_features = ['correlation', 'confidence_interval', 'bootstrap', 'monte_carlo']
        bonus = sum(0.05 for feature in advanced_features if feature in data_str)
        implementation_score = min(1.0, implementation_score + bonus)
    
    return results, parameter_accuracy, implementation_score

if __name__ == "__main__":
    results, param_score, impl_score = test_impedance_fitting()
    
    print("=== Electrochemical Impedance Spectroscopy Fitting Test Results ===")
    print(f"PASSED: {results['passed']}")
    print(f"FAILED: {results['failed']}")
    print(f"SCORE: {param_score:.3f} (parameter_accuracy)")
    print(f"SCORE: {impl_score:.3f} (implementation_completeness)")
    
    print("\nDetailed Results:")
    for test in results['tests']:
        status = "PASS" if test['passed'] else "FAIL"
        details = f" - {test['details']}" if test['details'] else ""
        print(f"{status}: {test['name']}{details}")
