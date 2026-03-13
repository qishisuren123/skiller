import subprocess
import tempfile
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import sys

def create_data():
    """Generate synthetic Lotka-Volterra time series data"""
    # True parameters
    alpha, beta, gamma, delta = 1.0, 0.5, 0.75, 0.25
    
    def lotka_volterra(state, t):
        x, y = state
        return [alpha*x - beta*x*y, delta*x*y - gamma*y]
    
    # Time points
    t = np.linspace(0, 20, 100)
    
    # Initial conditions
    initial_state = [10, 5]
    
    # Solve ODE
    solution = odeint(lotka_volterra, initial_state, t)
    
    # Add realistic noise
    noise_level = 0.1
    prey_pop = solution[:, 0] + np.random.normal(0, noise_level * solution[:, 0])
    pred_pop = solution[:, 1] + np.random.normal(0, noise_level * solution[:, 1])
    
    # Ensure positive populations
    prey_pop = np.maximum(prey_pop, 0.1)
    pred_pop = np.maximum(pred_pop, 0.1)
    
    # Create DataFrame
    data = pd.DataFrame({
        'time': t,
        'prey_population': prey_pop,
        'predator_population': pred_pop
    })
    
    return data, (alpha, beta, gamma, delta)

def test_lotka_volterra_fitting():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        data, true_params = create_data()
        input_file = 'population_data.csv'
        data.to_csv(input_file, index=False)
        
        output_plot = 'dynamics.png'
        output_results = 'results.json'
        predict_days = 50
        
        # Test different argument name variations
        cmd_variations = [
            ['--input', input_file, '--output_plot', output_plot, '--output_results', output_results, '--predict_days', str(predict_days)],
            ['--input', input_file, '--output-plot', output_plot, '--output-results', output_results, '--predict-days', str(predict_days)],
            ['-i', input_file, '--output_plot', output_plot, '--output_results', output_results]
        ]
        
        success = False
        for cmd_args in cmd_variations:
            try:
                result = subprocess.run([sys.executable, 'generated.py'] + cmd_args, 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        print(f"PASS: Script execution successful: {success}")
        
        if not success:
            print("FAIL: All command variations failed")
            return
        
        # Test file outputs
        plot_exists = os.path.exists(output_plot)
        results_exists = os.path.exists(output_results)
        print(f"PASS: Output plot created: {plot_exists}")
        print(f"PASS: Results JSON created: {results_exists}")
        
        if not results_exists:
            print("FAIL: Cannot proceed without results file")
            return
        
        # Load and validate results
        try:
            with open(output_results, 'r') as f:
                results = json.load(f)
            results_loaded = True
        except:
            results_loaded = False
            results = {}
        
        print(f"PASS: Results JSON is valid: {results_loaded}")
        
        # Test parameter estimation
        params_exist = all(param in results for param in ['alpha', 'beta', 'gamma', 'delta'])
        print(f"PASS: All Lotka-Volterra parameters estimated: {params_exist}")
        
        if params_exist:
            # Check parameter reasonableness (within order of magnitude)
            alpha_reasonable = 0.1 <= results['alpha'] <= 10.0
            beta_reasonable = 0.01 <= results['beta'] <= 5.0
            gamma_reasonable = 0.01 <= results['gamma'] <= 5.0
            delta_reasonable = 0.01 <= results['delta'] <= 2.0
            
            print(f"PASS: Alpha parameter reasonable: {alpha_reasonable}")
            print(f"PASS: Beta parameter reasonable: {beta_reasonable}")
            print(f"PASS: Gamma parameter reasonable: {gamma_reasonable}")
            print(f"PASS: Delta parameter reasonable: {delta_reasonable}")
        else:
            print("FAIL: Missing parameters")
            print("FAIL: Alpha parameter reasonable: False")
            print("FAIL: Beta parameter reasonable: False")
            print("FAIL: Gamma parameter reasonable: False")
            print("FAIL: Delta parameter reasonable: False")
        
        # Test goodness-of-fit metrics
        r2_prey_exists = 'r2_prey' in results
        r2_pred_exists = 'r2_predator' in results
        rmse_exists = 'rmse' in results
        
        print(f"PASS: R² for prey population calculated: {r2_prey_exists}")
        print(f"PASS: R² for predator population calculated: {r2_pred_exists}")
        print(f"PASS: RMSE calculated: {rmse_exists}")
        
        # Test prediction data
        predictions_exist = 'predictions' in results
        print(f"PASS: Prediction data generated: {predictions_exist}")
        
        if predictions_exist:
            pred_data = results['predictions']
            has_time = any('time' in str(key).lower() for key in pred_data.keys()) if isinstance(pred_data, dict) else False
            has_populations = any('prey' in str(key).lower() for key in pred_data.keys()) if isinstance(pred_data, dict) else False
            
            print(f"PASS: Predictions include time data: {has_time}")
            print(f"PASS: Predictions include population data: {has_populations}")
        else:
            print("FAIL: Predictions include time data: False")
            print("FAIL: Predictions include population data: False")
        
        # Calculate scores
        param_accuracy = 0.0
        if params_exist:
            true_alpha, true_beta, true_gamma, true_delta = true_params
            param_errors = [
                abs(results['alpha'] - true_alpha) / true_alpha,
                abs(results['beta'] - true_beta) / true_beta,
                abs(results['gamma'] - true_gamma) / true_gamma,
                abs(results['delta'] - true_delta) / true_delta
            ]
            param_accuracy = max(0, 1 - np.mean(param_errors))
        
        fit_quality = 0.0
        if r2_prey_exists and r2_pred_exists:
            r2_prey = results.get('r2_prey', 0)
            r2_pred = results.get('r2_predator', 0)
            fit_quality = (r2_prey + r2_pred) / 2
            fit_quality = max(0, min(1, fit_quality))  # Clamp to [0,1]
        
        print(f"SCORE: Parameter estimation accuracy: {param_accuracy:.3f}")
        print(f"SCORE: Model fit quality: {fit_quality:.3f}")

if __name__ == "__main__":
    test_lotka_volterra_fitting()
