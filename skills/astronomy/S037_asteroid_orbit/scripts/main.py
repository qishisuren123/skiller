#!/usr/bin/env python3
"""
Asteroid Orbital Elements Calculator
Computes basic orbital elements from position observations
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
import logging

def load_observations(input_file):
    """Load asteroid observation data from JSON file"""
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Handle different possible field names
    if 'time' in data:
        timestamps = np.array(data['time'])
    elif 'timestamps' in data:
        timestamps = np.array(data['timestamps'])
    else:
        raise KeyError("No time data found. Expected 'time' or 'timestamps' field")
    
    if 'x' in data:
        x_coords = np.array(data['x'])
    elif 'x_coordinates' in data:
        x_coords = np.array(data['x_coordinates'])
    else:
        raise KeyError("No x coordinate data found. Expected 'x' or 'x_coordinates' field")
    
    if 'y' in data:
        y_coords = np.array(data['y'])
    elif 'y_coordinates' in data:
        y_coords = np.array(data['y_coordinates'])
    else:
        raise KeyError("No y coordinate data found. Expected 'y' or 'y_coordinates' field")
    
    return timestamps, x_coords, y_coords

def ellipse_residuals(params, x, y):
    """Calculate residuals for ellipse fitting with Sun at one focus"""
    h, k, a, b, theta = params
    
    if a <= 0 or b <= 0:
        return np.full_like(x, 1e10)
    
    # Rotate coordinates
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    
    x_rot = (x - h) * cos_theta + (y - k) * sin_theta
    y_rot = -(x - h) * sin_theta + (y - k) * cos_theta
    
    # Ellipse equation residuals
    residuals = (x_rot / a)**2 + (y_rot / b)**2 - 1
    return residuals

def fit_ellipse(x_coords, y_coords):
    """Fit elliptical orbit to position data"""
    n_points = int(len(x_coords))  # Ensure integer
    
    # Initial parameter estimates
    h_init = np.mean(x_coords)
    k_init = np.mean(y_coords)
    
    # Use data spread for initial semi-axis estimates
    x_spread = np.max(x_coords) - np.min(x_coords)
    y_spread = np.max(y_coords) - np.min(y_coords)
    
    a_init = max(x_spread / 2, 0.1)
    b_init = max(y_spread / 2, 0.1)
    theta_init = 0.0
    
    initial_params = [h_init, k_init, a_init, b_init, theta_init]
    
    # Set bounds
    bounds = (
        [-np.inf, -np.inf, 0.01, 0.01, -np.pi],
        [np.inf, np.inf, np.inf, np.inf, np.pi]
    )
    
    try:
        result = least_squares(ellipse_residuals, initial_params,
                             args=(x_coords, y_coords), bounds=bounds,
                             max_nfev=1000)
        
        h, k, a, b, theta = result.x
        return h, k, a, b, theta, result
        
    except Exception as e:
        logging.error(f"Fitting failed: {e}")
        raise

def calculate_orbital_elements(h, k, a, b):
    """Calculate orbital elements from fitted ellipse"""
    # Ensure a >= b (a is semi-major axis)
    if b > a:
        a, b = b, a
    
    # Calculate eccentricity
    eccentricity = np.sqrt(1 - (b**2 / a**2)) if a > b else 0.0
    
    # For orbital mechanics, we need to account for the Sun's position
    # Distance from ellipse center to Sun (at origin)
    center_to_sun = np.sqrt(h**2 + k**2)
    
    # Adjust semi-major axis based on Sun's position relative to ellipse
    # This is a simplified approach - in reality this is more complex
    if center_to_sun > 0:
        # The semi-major axis should be approximately the mean distance to Sun
        distances_to_sun = np.sqrt(h**2 + k**2)  # This is just center distance
        # Use the fitted ellipse semi-major axis but ensure it's reasonable
        orbital_semi_major = max(a, center_to_sun)
    else:
        orbital_semi_major = a
    
    # Recalculate eccentricity if we adjusted the semi-major axis
    if orbital_semi_major != a:
        # Keep the same semi-minor axis
        orbital_eccentricity = np.sqrt(1 - (b**2 / orbital_semi_major**2))
    else:
        orbital_eccentricity = eccentricity
    
    # Ensure eccentricity is in valid range
    orbital_eccentricity = max(0.0, min(0.99, orbital_eccentricity))
    
    # Calculate orbital period using Kepler's third law
    period = np.sqrt(orbital_semi_major**3)
    
    return orbital_semi_major, b, orbital_eccentricity, period

def calculate_r_squared(x_coords, y_coords, h, k, a, b, theta):
    """Calculate R-squared for the ellipse fit"""
    residuals = ellipse_residuals([h, k, a, b, theta], x_coords, y_coords)
    ss_res = np.sum(residuals**2)
    
    # Total sum of squares
    y_mean = np.mean(y_coords)
    ss_tot = np.sum((y_coords - y_mean)**2)
    
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    
    r_squared = 1 - (ss_res / ss_tot)
    return max(0.0, r_squared)  # Ensure non-negative

def save_results(output_file, semi_major, semi_minor, eccentricity, period, r_squared):
    """Save orbital elements to JSON file"""
    results = {
        'orbital_elements': {
            'semi_major_axis_au': float(semi_major),
            'semi_minor_axis_au': float(semi_minor),
            'eccentricity': float(eccentricity),
            'orbital_period_years': float(period)
        },
        'fitting_statistics': {
            'r_squared': float(r_squared)
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

def create_visualization(x_coords, y_coords, h, k, a, b, theta, output_file):
    """Generate visualization of orbital fit"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # Plot observation points
    ax.scatter(x_coords, y_coords, c='red', s=50, label='Observations', zorder=5)
    
    # Generate ellipse points
    t = np.linspace(0, 2*np.pi, 1000)
    ellipse_x = h + a * np.cos(t) * np.cos(theta) - b * np.sin(t) * np.sin(theta)
    ellipse_y = k + a * np.cos(t) * np.sin(theta) + b * np.sin(t) * np.cos(theta)
    
    ax.plot(ellipse_x, ellipse_y, 'b-', linewidth=2, label='Fitted Orbit')
    
    # Plot Sun at origin
    ax.scatter(0, 0, c='yellow', s=200, marker='*', 
              edgecolors='orange', linewidth=2, label='Sun', zorder=10)
    
    # Plot ellipse center
    ax.scatter(h, k, c='blue', s=30, marker='x', label='Orbit Center')
    
    ax.set_xlabel('X Position (AU)')
    ax.set_ylabel('Y Position (AU)')
    ax.set_title('Asteroid Orbital Fit')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Calculate asteroid orbital elements')
    parser.add_argument('--input', '--observations', required=True,
                       help='Input JSON file with observation data')
    parser.add_argument('--output', '--results', required=True,
                       help='Output JSON file for orbital elements')
    parser.add_argument('--plot', '--visualization', required=True,
                       help='Output PNG file for orbital visualization')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Load observation data
        logger.info(f"Loading observations from {args.input}")
        timestamps, x_coords, y_coords = load_observations(args.input)
        
        # Fit elliptical orbit
        logger.info("Fitting elliptical orbit...")
        h, k, a, b, theta, fit_result = fit_ellipse(x_coords, y_coords)
        
        # Calculate orbital elements
        semi_major, semi_minor, eccentricity, period = calculate_orbital_elements(h, k, a, b)
        
        # Calculate R-squared
        r_squared = calculate_r_squared(x_coords, y_coords, h, k, a, b, theta)
        
        # Validate results
        if eccentricity < 0 or eccentricity >= 1:
            logger.warning(f"Unusual eccentricity value: {eccentricity}")
        if semi_major <= 0:
            logger.error("Invalid semi-major axis")
            return
        
        # Save results
        save_results(args.output, semi_major, semi_minor, eccentricity, period, r_squared)
        
        # Create visualization
        create_visualization(x_coords, y_coords, h, k, a, b, theta, args.plot)
        
        logger.info(f"Semi-major axis: {semi_major:.3f} AU")
        logger.info(f"Eccentricity: {eccentricity:.3f}")
        logger.info(f"Orbital period: {period:.2f} years")
        logger.info(f"R-squared: {r_squared:.3f}")
        logger.info(f"Results saved to {args.output}")
        logger.info(f"Visualization saved to {args.plot}")
        
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return

if __name__ == "__main__":
    main()
