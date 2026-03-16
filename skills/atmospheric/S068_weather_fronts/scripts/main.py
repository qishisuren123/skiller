#!/usr/bin/env python3
"""
Weather Front Detection from Temperature Gradient Analysis
"""

import argparse
import json
import logging
import numpy as np
import h5py
import matplotlib.pyplot as plt
from scipy import ndimage
from scipy.ndimage import gaussian_filter, label, sobel
import matplotlib.colors as colors

def setup_logging():
    """Configure logging for the script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_temperature_data(input_file):
    """Load temperature data from HDF5 file"""
    logging.info(f"Loading temperature data from {input_file}")
    
    with h5py.File(input_file, 'r') as f:
        temperature = f['temperature'][:]
        lat = f['lat'][:]
        lon = f['lon'][:]
        grid_spacing = f['grid_spacing'][()]
    
    return temperature, lat, lon, grid_spacing

def smooth_temperature_field(temperature, sigma):
    """Apply Gaussian smoothing to temperature field"""
    logging.info(f"Applying Gaussian smoothing with sigma={sigma}")
    return gaussian_filter(temperature, sigma=sigma)

def calculate_temperature_gradients(temperature, grid_spacing):
    """Calculate temperature gradients using optimized scipy operations"""
    logging.info("Calculating temperature gradients")
    
    # Use scipy's sobel filters for faster gradient calculation
    grad_y = sobel(temperature, axis=0) / (8.0 * grid_spacing)
    grad_x = sobel(temperature, axis=1) / (8.0 * grid_spacing)
    
    # Calculate gradient magnitude
    gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
    
    return grad_x, grad_y, gradient_magnitude

def detect_gradient_ridges_optimized(grad_x, grad_y, gradient_magnitude, threshold):
    """Optimized ridge detection using scipy filters"""
    logging.info("Detecting gradient ridges using optimized method")
    
    # Pre-filter by gradient threshold to reduce computation
    high_grad_mask = gradient_magnitude > threshold
    if not np.any(high_grad_mask):
        return np.zeros_like(gradient_magnitude, dtype=bool)
    
    # Use scipy's sobel for second derivatives
    grad_xx = sobel(grad_x, axis=1) / 8.0
    grad_xy = sobel(grad_x, axis=0) / 8.0  
    grad_yy = sobel(grad_y, axis=0) / 8.0
    
    # Avoid division by zero with epsilon
    eps = 1e-10
    magnitude_safe = np.maximum(gradient_magnitude, eps)
    
    # Normalize gradient vectors only where needed
    grad_x_norm = np.divide(grad_x, magnitude_safe, out=np.zeros_like(grad_x), where=high_grad_mask)
    grad_y_norm = np.divide(grad_y, magnitude_safe, out=np.zeros_like(grad_y), where=high_grad_mask)
    
    # Perpendicular direction vectors
    perp_x = -grad_y_norm
    perp_y = grad_x_norm
    
    # Vectorized second derivative calculation
    second_deriv_perp = (perp_x**2 * grad_xx + 
                        2 * perp_x * perp_y * grad_xy + 
                        perp_y**2 * grad_yy)
    
    # Ridge condition
    ridge_mask = high_grad_mask & (second_deriv_perp < -0.05)
    
    return ridge_mask

def detect_fronts(grad_x, grad_y, gradient_magnitude, threshold, min_length):
    """Detect weather fronts as gradient ridges"""
    logging.info(f"Detecting fronts with threshold={threshold} °C/km")
    
    ridge_mask = detect_gradient_ridges_optimized(grad_x, grad_y, gradient_magnitude, threshold)
    
    structure = np.ones((3, 3))
    labeled_fronts, num_fronts = label(ridge_mask, structure=structure)
    
    if num_fronts == 0:
        return labeled_fronts, []
    
    # Vectorized filtering by minimum length
    unique_labels, counts = np.unique(labeled_fronts[labeled_fronts > 0], return_counts=True)
    valid_fronts = unique_labels[counts >= min_length].tolist()
    
    return labeled_fronts, valid_fronts

def extract_front_properties(labeled_fronts, valid_fronts, gradient_magnitude, lat, lon):
    """Extract properties of detected fronts"""
    logging.info("Extracting front properties")
    
    fronts_data = []
    
    for front_id in valid_fronts:
        front_pixels = np.where(labeled_fronts == front_id)
        y_indices, x_indices = front_pixels
        
        front_lats = lat[y_indices]
        front_lons = lon[x_indices]
        
        avg_gradient = np.mean(gradient_magnitude[front_pixels])
        
        front_data = {
            'id': int(front_id),
            'coordinates': {
                'lat': front_lats.tolist(),
                'lon': front_lons.tolist()
            },
            'average_gradient': float(avg_gradient),
            'length': len(y_indices)
        }
        fronts_data.append(front_data)
    
    return fronts_data

def save_front_data(fronts_data, output_file):
    """Save front data to JSON file"""
    logging.info(f"Saving front data to {output_file}")
    
    output_data = {
        'fronts': fronts_data,
        'total_fronts': len(fronts_data)
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

def create_visualization(temperature, labeled_fronts, valid_fronts, lat, lon, output_file):
    """Create visualization of temperature field with detected fronts"""
    logging.info(f"Creating visualization: {output_file}")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    
    temp_plot = ax.contourf(lon_grid, lat_grid, temperature, levels=20, cmap='RdYlBu_r')
    plt.colorbar(temp_plot, ax=ax, label='Temperature (°C)')
    
    for front_id in valid_fronts:
        front_pixels = np.where(labeled_fronts == front_id)
        y_indices, x_indices = front_pixels
        front_lons_plot = lon[x_indices]
        front_lats_plot = lat[y_indices]
        ax.scatter(front_lons_plot, front_lats_plot, c='black', s=1, alpha=0.8)
    
    ax.set_xlabel('Longitude (°)')
    ax.set_ylabel('Latitude (°)')
    ax.set_title('Temperature Field with Detected Weather Fronts')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Detect weather fronts from temperature gradient analysis')
    parser.add_argument('--input-data', required=True, help='Path to input HDF5 file')
    parser.add_argument('--output-fronts', required=True, help='Path to output JSON file')
    parser.add_argument('--output-plot', required=True, help='Path to output PNG file')
    parser.add_argument('--gradient-threshold', type=float, default=2.0, 
                       help='Minimum temperature gradient magnitude (°C/km)')
    parser.add_argument('--min-front-length', type=int, default=5,
                       help='Minimum length (grid points) for valid front')
    parser.add_argument('--smoothing-sigma', type=float, default=1.0,
                       help='Gaussian smoothing parameter')
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        temperature, lat, lon, grid_spacing = load_temperature_data(args.input_data)
        smoothed_temp = smooth_temperature_field(temperature, args.smoothing_sigma)
        grad_x, grad_y, gradient_magnitude = calculate_temperature_gradients(smoothed_temp, grid_spacing)
        labeled_fronts, valid_fronts = detect_fronts(grad_x, grad_y, gradient_magnitude, 
                                                   args.gradient_threshold, args.min_front_length)
        fronts_data = extract_front_properties(labeled_fronts, valid_fronts, gradient_magnitude, lat, lon)
        save_front_data(fronts_data, args.output_fronts)
        create_visualization(smoothed_temp, labeled_fronts, valid_fronts, lat, lon, args.output_plot)
        
        logging.info(f"Front detection complete. Found {len(fronts_data)} fronts.")
        
    except Exception as e:
        logging.error(f"Error during processing: {e}")
        raise

if __name__ == '__main__':
    main()
