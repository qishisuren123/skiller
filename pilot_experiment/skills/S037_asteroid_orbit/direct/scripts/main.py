#!/usr/bin/env python3
"""
Asteroid Orbital Elements Calculator
Computes orbital parameters from position observations using elliptical orbit fitting.
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
import sys

def load_observations(filename):
    """Load asteroid observations from JSON file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Validate required fields
        required_fields = ['timestamps', 'x_coordinates', 'y_coordinates']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        timestamps = np.array(data['timestamps'])
        x_coords = np.array(data['x_coordinates'])
        y_coords = np.array(data['y_coordinates'])
        
        # Validate data consistency
        if not (len(timestamps) == len(x_coords) == len(y_coords)):
            raise ValueError("Inconsistent data lengths")
        
        if len(timestamps) < 5:
            raise ValueError("Need at least 5 observations for ellipse fitting")
        
        return timestamps, x_coords, y_coords
    
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"Error loading observations: {e}")
        sys.exit(1)

def ellipse_residuals(params, x, y):
    """Calculate residuals for ellipse fitting."""
    h, k, a, b, theta = params
    
    # Handle negative semi-axes
    a, b = abs(a), abs(b)
    if a == 0 or b == 0:
        return np.full_like(x, 1e6)
    
    # Rotate coordinates
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    x_rot = (x - h) * cos_t + (y - k) * sin_t
    y_rot = -(x - h) * sin_t + (y - k) * cos_t
    
    # Ellipse equation residuals
    return (x_rot/a)**2 + (y_rot/b)**2 - 1

def fit_ellipse(x, y):
    """Fit ellipse to observation points using least squares."""
    # Initial guess based on data bounds
    x_center, y_center = np.mean(x), np.mean(y)
    x_range, y_range = np.ptp(x), np.ptp(y)
    initial_a, initial_b = x_range/2, y_range/2
    initial_theta = 0.0
    
    initial_guess = [x_center, y_center, initial_a, initial_b, initial_theta]
    
    # Try multiple initial guesses for robustness
    best_result = None
    best_cost = np.inf
    
    for i in range(5):
        # Add some randomization to initial guess
        guess = initial_guess.copy()
        if i > 0:
            guess[0] += np.random.normal(0, x_range/10)  # h
            guess[1] += np.random.normal(0, y_range/10)  # k
            guess[2] += np.random.normal(0, x_range/20)  # a
            guess[3] += np.random.normal(0, y_range/20)  # b
            guess[4] = np.random.uniform(0, 2*np.pi)     # theta
        
        try:
            result = least_squares(ellipse_residuals, guess, args=(x, y))
            if result.success and result.cost < best_cost:
                best_result = result
                best_cost = result.cost
        except:
            continue
    
    if best_result is None:
        raise RuntimeError("Ellipse fitting failed to converge")
    
    return best_result

def calculate_orbital_elements(ellipse_params, x_obs, y_obs):
    """Calculate orbital elements from fitted ellipse parameters."""
    h, k, a_fit, b_fit, theta = ellipse_params
    
    # Ensure positive semi-axes and identify semi-major axis
    a_fit, b_fit = abs(a_fit), abs(b_fit)
    semi_major = max(a_fit, b_fit)
    semi_minor = min(a_fit, b_fit)
    
    # Calculate eccentricity
    if semi_major == 0:
        raise ValueError("Invalid semi-major axis")
    
    eccentricity = np.sqrt(1 - (semi_minor/semi_major)**2)
    
    # Validate physical constraints
    if not (0 <= eccentricity < 1):
        raise ValueError(f"Unphysical eccentricity: {eccentricity}")
    
    # Calculate orbital period using Kepler's third law (T² = a³ in AU/years)
    period_years = semi_major**1.5
    
    # Calculate R-squared for fit quality
    residuals = ellipse_residuals(ellipse_params, x_obs, y_obs)
    ss_res = np.sum(residuals**2)
    y_mean = np.mean(np.sqrt(x_obs**2 + y_obs**2))  # Mean distance from origin
    ss_tot = np.sum((np.sqrt(x_obs**2 + y_obs**2) - y_mean)**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return {
        'semi_major_axis_au': float(semi_major),
        'semi_minor_axis_au': float(semi_minor),
        'eccentricity': float(eccentricity),
        'orbital_period_years': float(period_years),
        'ellipse_center_x_au': float(h),
        'ellipse_center_y_au': float(k),
        'rotation_angle_rad': float(theta),
        'fit_r_squared': float(r_squared)
    }

def generate_ellipse_points(h, k, a, b, theta, n_points=100):
    """Generate points along the fitted ellipse for visualization."""
    t = np.linspace(0, 2*np.pi, n_points)
    x_ellipse = a * np.cos(t)
    y_ellipse = b * np.sin(t)
    
    # Apply rotation and translation
    cos_theta, sin_theta = np.cos(theta), np.sin(theta)
    x_rot = x_ellipse * cos_theta - y_ellipse * sin_theta + h
    y_rot = x_ellipse * sin_theta + y_ellipse * cos_theta + k
    
    return x_rot, y_rot

def create_visualization(x_obs, y_obs, timestamps, orbital_elements, output_file):
    """Create and save orbital visualization."""
    plt.figure(figsize=(10, 8))
    
    # Plot observations
    plt.scatter(x_obs, y_obs, c=timestamps, cmap='viridis', 
               s=50, alpha=0.7, label='Observations')
    plt.colorbar(label='Time')
    
    # Plot fitted ellipse
    h = orbital_elements['ellipse_center_x_au']
    k = orbital_elements['ellipse_center_y_au']
    a = orbital_elements['semi_major_axis_au']
    b = orbital_elements['semi_minor_axis_au']
    theta = orbital_elements['rotation_angle_rad']
    
    x_ellipse, y_ellipse = generate_ellipse_points(h, k, a, b, theta)
    plt.plot(x_ellipse, y_ellipse, 'r-', linewidth=2, label='Fitted Orbit')
    
    # Plot Sun at origin
    plt.plot(0, 0, 'yo', markersize=10, label='Sun')
    
    # Plot ellipse center
    plt.plot(h, k, 'rx', markersize=8, label='Orbit Center')
    
    plt.xlabel('X Position (AU)')
    plt.ylabel('Y Position (AU)')
    plt.title('Asteroid Orbital Fit')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    
    # Add text with orbital elements
    info_text = f"Semi-major axis: {a:.3f} AU\n"
    info_text += f"Eccentricity: {orbital_elements['eccentricity']:.3f}\n"
    info_text += f"Period: {orbital_elements['orbital_period_years']:.2f} years\n"
    info_text += f"R²: {orbital_elements['fit_r_squared']:.3f}"
    
    plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def save_results(orbital_elements, output_file):
    """Save orbital elements to JSON file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(orbital_elements, f, indent=2)
    except IOError as e:
        print(f"Error saving results: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Calculate asteroid orbital elements from observations')
    parser.add_argument('--input', '--observations', required=True,
                       help='Input JSON file with observation data')
    parser.add_argument('--output', '--results', required=True,
                       help='Output JSON file for orbital elements')
    parser.add_argument('--plot', '--visualization', required=True,
                       help='Output PNG file for orbital visualization')
    
    args = parser.parse_args()
    
    # Load observation data
    print("Loading observations...")
    timestamps, x_coords, y_coords = load_observations(args.input)
    print(f"Loaded {len(timestamps)} observations")
    
    # Fit elliptical orbit
    print("Fitting elliptical orbit...")
    try:
        fit_result = fit_ellipse(x_coords, y_coords)
        print("Orbit fitting successful")
    except Exception as e:
        print(f"Error fitting orbit: {e}")
        sys.exit(1)
    
    # Calculate orbital elements
    print("Calculating orbital elements...")
    try:
        orbital_elements = calculate_orbital_elements(fit_result.x, x_coords, y_coords)
        print("Orbital elements calculated successfully")
    except Exception as e:
        print(f"Error calculating orbital elements: {e}")
        sys.exit(1)
    
    # Generate visualization
    print("Creating visualization...")
    create_visualization(x_coords, y_coords, timestamps, orbital_elements, args.plot)
    
    # Save results
    print("Saving results...")
    save_results(orbital_elements, args.output)
    
    # Print summary
    print("\nOrbital Elements Summary:")
    print(f"Semi-major axis: {orbital_elements['semi_major_axis_au']:.3f} AU")
    print(f"Eccentricity: {orbital_elements['eccentricity']:.3f}")
    print(f"Orbital period: {orbital_elements['orbital_period_years']:.2f} years")
    print(f"Fit quality (R²): {orbital_elements['fit_r_squared']:.3f}")
    print(f"\nResults saved to: {args.output}")
    print(f"Visualization saved to: {args.plot}")

if __name__ == "__main__":
    main()
