import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json
import os
from pathlib import Path

def four_pl_model(log_conc, bottom, top, log_ic50, hill_slope):
    """4-parameter logistic model for dose-response curves"""
    return bottom + (top - bottom) / (1 + 10**((log_ic50 - log_conc) * hill_slope))

def validate_data(df):
    """Validate and clean dose-response data"""
    initial_count = len(df)
    
    # Remove rows with invalid concentrations or responses
    df_clean = df[
        (df['concentration'] > 0) & 
        (df['response'] >= 0) & 
        (df['response'] <= 100) &
        (pd.notna(df['concentration'])) &
        (pd.notna(df['response']))
    ].copy()
    
    filtered_count = initial_count - len(df_clean)
    print(f"Filtered {filtered_count} invalid data points. {len(df_clean)} points remaining.")
    
    return df_clean

def fit_dose_response_curve(concentrations, responses):
    """Fit 4PL model to dose-response data"""
    log_conc = np.log10(concentrations)
    
    # Initial parameter estimates
    min_resp = np.min(responses)
    max_resp = np.max(responses)
    median_conc = np.median(concentrations)
    
    # Initial parameters: [bottom, top, log_ic50, hill_slope]
    p0 = [min_resp, max_resp, np.log10(median_conc), 1.0]
    
    # Parameter bounds
    bounds = (
        [0, max(50, min_resp), log_conc.min()-2, -10],  # lower bounds
        [min(50, max_resp), 100, log_conc.max()+2, 10]  # upper bounds
    )
    
    try:
        popt, pcov = curve_fit(four_pl_model, log_conc, responses, 
                              p0=p0, bounds=bounds, maxfev=5000)
        
        # Calculate parameter standard errors
        param_errors = np.sqrt(np.diag(pcov))
        
        # Calculate R-squared
        y_pred = four_pl_model(log_conc, *popt)
        ss_res = np.sum((responses - y_pred) ** 2)
        ss_tot = np.sum((responses - np.mean(responses)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        return popt, param_errors, r_squared, True
        
    except Exception as e:
        print(f"Curve fitting failed: {e}")
        return None, None, None, False

def create_plot(concentrations, responses, fit_params, output_dir):
    """Generate dose-response curve plot"""
    plt.figure(figsize=(10, 6))
    
    # Plot original data
    plt.scatter(concentrations, responses, alpha=0.7, s=50, 
               color='blue', label='Data points')
    
    if fit_params is not None:
        # Generate smooth curve for plotting
        conc_range = np.logspace(np.log10(concentrations.min()), 
                                np.log10(concentrations.max()), 100)
        log_conc_range = np.log10(conc_range)
        fitted_curve = four_pl_model(log_conc_range, *fit_params)
        
        plt.plot(conc_range, fitted_curve, 'r-', linewidth=2, 
                label='4PL fit')
        
        # Add IC50 line
        ic50 = 10**fit_params[2]
        plt.axvline(x=ic50, color='green', linestyle='--', alpha=0.7,
                   label=f'IC50 = {ic50:.2e}')
    
    plt.xscale('log')
    plt.xlabel('Concentration')
    plt.ylabel('Response (%)')
    plt.title('Dose-Response Curve Analysis')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plot_path = os.path.join(output_dir, 'dose_response_curve.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return plot_path

def save_results(fit_params, param_errors, r_squared, n_points, output_dir):
    """Save fitting results to JSON file"""
    if fit_params is not None:
        results = {
            'ic50': float(10**fit_params[2]),
            'ic50_log': float(fit_params[2]),
            'hill_slope': float(fit_params[3]),
            'top_plateau': float(fit_params[1]),
            'bottom_plateau': float(fit_params[0]),
            'ic50_std_error': float(param_errors[2] * 10**fit_params[2] * np.log(10)),
            'hill_slope_std_error': float(param_errors[3]),
            'top_plateau_std_error': float(param_errors[1]),
            'bottom_plateau_std_error': float(param_errors[0]),
            'r_squared': float(r_squared),
            'n_data_points': int(n_points),
            'fit_successful': True
        }
    else:
        results = {
            'fit_successful': False,
            'n_data_points': int(n_points),
            'error': 'Curve fitting failed'
        }
    
    results_path = os.path.join(output_dir, 'fit_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results_path

def main():
    parser = argparse.ArgumentParser(description='Analyze dose-response curves and compute IC50/EC50 values')
    parser.add_argument('--input', required=True, help='Input CSV file with concentration and response columns')
    parser.add_argument('--output', required=True, help='Output directory for results')
    
    args = parser.parse_args()
    
    # Create output directory
    Path(args.output).mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        df = pd.read_csv(args.input)
        
        # Validate required columns
        if 'concentration' not in df.columns or 'response' not in df.columns:
            raise ValueError("CSV file must contain 'concentration' and 'response' columns")
        
        # Validate and clean data
        df_clean = validate_data(df)
        
        if len(df_clean) < 5:
            raise ValueError("Insufficient valid data points for curve fitting (minimum 5 required)")
        
        # Fit curve
        print("Fitting 4-parameter logistic model...")
        fit_params, param_errors, r_squared, success = fit_dose_response_curve(
            df_clean['concentration'].values, df_clean['response'].values
        )
        
        if success:
            ic50 = 10**fit_params[2]
            print(f"Curve fitting successful!")
            print(f"IC50/EC50: {ic50:.2e}")
            print(f"Hill slope: {fit_params[3]:.3f}")
            print(f"R-squared: {r_squared:.4f}")
        else:
            print("Curve fitting failed!")
        
        # Create plot
        plot_path = create_plot(df_clean['concentration'].values, 
                               df_clean['response'].values, 
                               fit_params, args.output)
        print(f"Plot saved to: {plot_path}")
        
        # Save results
        results_path = save_results(fit_params, param_errors, r_squared, 
                                   len(df_clean), args.output)
        print(f"Results saved to: {results_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
