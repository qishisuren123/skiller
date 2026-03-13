# Example 1: Basic ellipse fitting and orbital elements calculation
import numpy as np
from scipy.optimize import least_squares

# Sample observation data (asteroid positions in AU)
x_obs = np.array([2.1, 2.3, 2.2, 1.8, 1.5, 1.3, 1.5, 1.8])
y_obs = np.array([0.5, 1.2, 1.8, 2.1, 1.9, 1.2, 0.3, -0.2])

def ellipse_residuals(params, x, y):
    h, k, a, b, theta = params
    a, b = abs(a), abs(b)
    if a == 0 or b == 0:
        return np.full_like(x, 1e6)
    
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    x_rot = (x - h) * cos_t + (y - k) * sin_t
    y_rot = -(x - h) * sin_t + (y - k) * cos_t
    return (x_rot/a)**2 + (y_rot/b)**2 - 1

# Initial guess for ellipse parameters
initial_guess = [np.mean(x_obs), np.mean(y_obs), 
                np.ptp(x_obs)/2, np.ptp(y_obs)/2, 0.0]

# Fit ellipse
result = least_squares(ellipse_residuals, initial_guess, args=(x_obs, y_obs))
h, k, a_fit, b_fit, theta = result.x

# Calculate orbital elements
semi_major = max(abs(a_fit), abs(b_fit))
semi_minor = min(abs(a_fit), abs(b_fit))
eccentricity = np.sqrt(1 - (semi_minor/semi_major)**2)
period_years = semi_major**1.5

print(f"Semi-major axis: {semi_major:.3f} AU")
print(f"Eccentricity: {eccentricity:.3f}")
print(f"Orbital period: {period_years:.2f} years")

# Example 2: Complete workflow with visualization
import matplotlib.pyplot as plt
import json

# Load observations from JSON
def load_and_process_asteroid_data(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    
    timestamps = np.array(data['timestamps'])
    x_coords = np.array(data['x_coordinates'])
    y_coords = np.array(data['y_coordinates'])
    
    # Fit orbit
    initial_guess = [np.mean(x_coords), np.mean(y_coords),
                    np.ptp(x_coords)/2, np.ptp(y_coords)/2, 0.0]
    
    result = least_squares(ellipse_residuals, initial_guess, 
                          args=(x_coords, y_coords))
    
    if not result.success:
        raise RuntimeError("Orbit fitting failed")
    
    h, k, a_fit, b_fit, theta = result.x
    semi_major = max(abs(a_fit), abs(b_fit))
    semi_minor = min(abs(a_fit), abs(b_fit))
    
    # Generate ellipse for plotting
    t = np.linspace(0, 2*np.pi, 100)
    x_ellipse = abs(a_fit) * np.cos(t)
    y_ellipse = abs(b_fit) * np.sin(t)
    
    # Apply rotation and translation
    cos_theta, sin_theta = np.cos(theta), np.sin(theta)
    x_rot = x_ellipse * cos_theta - y_ellipse * sin_theta + h
    y_rot = x_ellipse * sin_theta + y_ellipse * cos_theta + k
    
    # Create visualization
    plt.figure(figsize=(10, 8))
    plt.scatter(x_coords, y_coords, c=timestamps, cmap='viridis', 
               s=50, alpha=0.7, label='Observations')
    plt.plot(x_rot, y_rot, 'r-', linewidth=2, label='Fitted Orbit')
    plt.plot(0, 0, 'yo', markersize=10, label='Sun')
    plt.xlabel('X Position (AU)')
    plt.ylabel('Y Position (AU)')
    plt.title('Asteroid Orbital Analysis')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    plt.savefig('asteroid_orbit.png', dpi=300, bbox_inches='tight')
    
    # Return orbital elements
    return {
        'semi_major_axis_au': float(semi_major),
        'semi_minor_axis_au': float(semi_minor),
        'eccentricity': float(np.sqrt(1 - (semi_minor/semi_major)**2)),
        'orbital_period_years': float(semi_major**1.5)
    }

# Usage example:
# orbital_elements = load_and_process_asteroid_data('observations.json')
# print(f"Orbital period: {orbital_elements['orbital_period_years']:.2f} years")
