import numpy as np
import argparse
import json
from scipy.optimize import minimize
import matplotlib.pyplot as plt

def generate_photometric_data(num_points, noise_level):
    """Generate synthetic photometric time series over 10 days"""
    time = np.linspace(0, 10, num_points)  # 10 days
    baseline_flux = np.ones(num_points)
    noise = np.random.normal(0, noise_level, num_points)
    flux = baseline_flux + noise
    return time, flux

def inject_transit(time, flux, transit_depth, transit_time=5.0, duration_hours=3.0):
    """Inject box-car transit signal"""
    duration_days = duration_hours / 24.0
    transit_mask = np.abs(time - transit_time) <= duration_days / 2
    flux_with_transit = flux.copy()
    flux_with_transit[transit_mask] -= transit_depth
    return flux_with_transit

def box_car_filter(time, flux, duration_hours=3.0):
    """Apply sliding box-car filter for transit detection"""
    duration_days = duration_hours / 24.0
    dt = np.median(np.diff(time))
    filter_width = int(duration_days / dt)
    
    if filter_width < 3:
        filter_width = 3
    
    # Create detection statistic
    detection_stat = np.zeros_like(time)
    
    for i in range(len(time)):
        start_idx = max(0, i - filter_width // 2)
        end_idx = min(len(time), i + filter_width // 2 + 1)
        
        in_transit = flux[start_idx:end_idx]
        out_transit_before = flux[max(0, start_idx - filter_width):start_idx]
        out_transit_after = flux[end_idx:min(len(flux), end_idx + filter_width)]
        out_transit = np.concatenate([out_transit_before, out_transit_after])
        
        if len(out_transit) > 0:
            detection_stat[i] = np.mean(out_transit) - np.mean(in_transit)
    
    return detection_stat

def transit_model(time, params):
    """Box-car transit model"""
    t0, depth, duration_hours = params
    duration_days = duration_hours / 24.0
    
    model = np.ones_like(time)
    transit_mask = np.abs(time - t0) <= duration_days / 2
    model[transit_mask] = 1.0 - depth
    return model

def chi_squared(params, time, flux, flux_err):
    """Chi-squared objective function"""
    model = transit_model(time, params)
    chi2 = np.sum(((flux - model) / flux_err) ** 2)
    return chi2

def fit_transit(time, flux, flux_err, initial_guess):
    """Fit transit parameters using least-squares"""
    bounds = [
        (time.min(), time.max()),  # t0
        (0.0, 0.1),               # depth
        (1.0/24, 6.0/24)          # duration in days (1-6 hours)
    ]
    
    result = minimize(chi_squared, initial_guess, 
                     args=(time, flux, flux_err),
                     bounds=bounds, method='L-BFGS-B')
    
    return result

def calculate_detection_significance(detection_stat, noise_level):
    """Calculate detection significance"""
    # Use robust statistics for significance
    median_stat = np.median(detection_stat)
    mad_stat = np.median(np.abs(detection_stat - median_stat))
    robust_std = 1.4826 * mad_stat  # Convert MAD to std estimate
    
    if robust_std == 0:
        robust_std = noise_level
    
    max_detection = np.max(detection_stat)
    significance = (max_detection - median_stat) / robust_std
    
    return significance, np.argmax(detection_stat)

def create_diagnostic_plot(time, original_flux, flux_with_transit, 
                          fitted_model, output_path):
    """Create diagnostic plot"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                   gridspec_kw={'height_ratios': [3, 1]})
    
    # Main light curve
    ax1.plot(time, original_flux, 'k.', alpha=0.3, markersize=2, 
             label='Original data')
    ax1.plot(time, flux_with_transit, 'b.', markersize=3, 
             label='Data with transit')
    ax1.plot(time, fitted_model, 'r-', linewidth=2, 
             label='Best-fit model')
    
    ax1.set_ylabel('Relative Flux')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Exoplanet Transit Detection and Fit')
    
    # Residuals
    residuals = flux_with_transit - fitted_model
    ax2.plot(time, residuals, 'g.', markersize=2)
    ax2.axhline(0, color='k', linestyle='--', alpha=0.5)
    ax2.set_xlabel('Time (days)')
    ax2.set_ylabel('Residuals')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Exoplanet Transit Detection and Fitting')
    parser.add_argument('--num_points', type=int, default=1000,
                       help='Number of data points in time series')
    parser.add_argument('--noise_level', type=float, default=0.001,
                       help='Standard deviation of photometric noise')
    parser.add_argument('--transit_depth', type=float, default=0.01,
                       help='Expected transit depth as fraction')
    parser.add_argument('--output_file', type=str, required=True,
                       help='Path to save results as JSON')
    parser.add_argument('--plot_file', type=str,
                       help='Path to save diagnostic plot')
    
    args = parser.parse_args()
    
    # Generate synthetic data
    time, original_flux = generate_photometric_data(args.num_points, args.noise_level)
    flux_with_transit = inject_transit(time, original_flux, args.transit_depth)
    
    # Detect transit
    detection_stat = box_car_filter(time, flux_with_transit)
    significance, best_idx = calculate_detection_significance(detection_stat, args.noise_level)
    
    results = {
        'detection_significance': float(significance),
        'significant_detection': significance > 3.0
    }
    
    if significance > 3.0:
        # Fit transit parameters
        initial_t0 = time[best_idx]
        initial_guess = [initial_t0, args.transit_depth, 3.0/24]  # 3 hours in days
        
        flux_err = np.full_like(flux_with_transit, args.noise_level)
        fit_result = fit_transit(time, flux_with_transit, flux_err, initial_guess)
        
        if fit_result.success:
            fitted_t0, fitted_depth, fitted_duration = fit_result.x
            fitted_model = transit_model(time, fit_result.x)
            
            # Calculate fit quality
            chi2 = fit_result.fun
            dof = len(time) - 3  # 3 parameters
            reduced_chi2 = chi2 / dof
            
            results.update({
                'fitted_transit_time': float(fitted_t0),
                'fitted_depth': float(fitted_depth),
                'fitted_duration_hours': float(fitted_duration * 24),
                'chi_squared': float(chi2),
                'reduced_chi_squared': float(reduced_chi2),
                'fit_success': True
            })
            
            # Create diagnostic plot if requested
            if args.plot_file:
                create_diagnostic_plot(time, original_flux, flux_with_transit,
                                     fitted_model, args.plot_file)
        else:
            results.update({
                'fit_success': False,
                'fit_error': 'Optimization failed to converge'
            })
    else:
        results.update({
            'fit_success': False,
            'fit_error': 'No significant transit detected'
        })
    
    # Save results
    with open(args.output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis complete. Results saved to {args.output_file}")
    if significance > 3.0:
        print(f"Transit detected with {significance:.1f}σ significance")
    else:
        print(f"No significant transit detected ({significance:.1f}σ)")

if __name__ == "__main__":
    main()
