#!/usr/bin/env python3
"""
Weather Front Detection from Temperature Gradient Analysis
Detects atmospheric fronts by analyzing temperature gradients in gridded data.
"""

import argparse
import json
import h5py
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, label
from scipy.ndimage.measurements import find_objects
import sys

def load_atmospheric_data(filepath):
    """Load temperature data and coordinates from HDF5 file."""
    try:
        with h5py.File(filepath, 'r') as f:
            temperature = f['temperature'][:]
            lat = f['lat'][:]
            lon = f['lon'][:]
            grid_spacing = f['grid_spacing'][()]
        return temperature, lat, lon, grid_spacing
    except (KeyError, OSError) as e:
        raise ValueError(f"Error loading HDF5 file: {e}")

def detect_weather_fronts(temperature, grid_spacing, gradient_threshold, 
                         min_front_length, smoothing_sigma):
    """Detect weather fronts from temperature gradient analysis."""
    
    # Apply Gaussian smoothing to reduce noise
    temp_smooth = gaussian_filter(temperature, sigma=smoothing_sigma)
    
    # Calculate temperature gradients using central differences
    grad_y, grad_x = np.gradient(temp_smooth)
    
    # Convert gradients from °C/grid_point to °C/km
    grad_x = grad_x / grid_spacing
    grad_y = grad_y / grid_spacing
    
    # Compute gradient magnitude
    grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
    
    # Apply threshold to identify potential fronts
    front_mask = grad_magnitude >= gradient_threshold
    
    # Segment connected regions (8-connectivity for diagonal connections)
    structure = np.ones((3, 3), dtype=int)  # 8-connected neighborhood
    labeled_fronts, num_fronts = label(front_mask, structure=structure)
    
    # Filter fronts by minimum length and extract properties
    front_segments = []
    
    for front_id in range(1, num_fronts + 1):
        front_pixels = labeled_fronts == front_id
        front_coords = np.where(front_pixels)
        
        # Calculate front length (number of pixels)
        front_length = len(front_coords[0])
        
        if front_length >= min_front_length:
            # Calculate average gradient strength for this front
            avg_gradient = np.mean(grad_magnitude[front_pixels])
            
            # Store front segment information
            segment_info = {
                'front_id': int(front_id),
                'length_pixels': int(front_length),
                'avg_gradient_strength': float(avg_gradient),
                'pixel_coordinates': {
                    'y_indices': front_coords[0].tolist(),
                    'x_indices': front_coords[1].tolist()
                }
            }
            front_segments.append(segment_info)
    
    return front_segments, grad_magnitude, labeled_fronts

def save_front_data(front_segments, output_path, metadata):
    """Save detected front information to JSON file."""
    output_data = {
        'metadata': metadata,
        'num_fronts_detected': len(front_segments),
        'front_segments': front_segments
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

def create_visualization(temperature, lat, lon, front_segments, labeled_fronts, 
                        grad_magnitude, output_path):
    """Create visualization showing temperature field with detected fronts."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot 1: Temperature field with front overlay
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    
    temp_plot = ax1.contourf(lon_grid, lat_grid, temperature, levels=20, cmap='RdYlBu_r')
    plt.colorbar(temp_plot, ax=ax1, label='Temperature (°C)')
    
    # Overlay detected fronts
    if len(front_segments) > 0:
        front_mask = labeled_fronts > 0
        ax1.contour(lon_grid, lat_grid, front_mask.astype(int), 
                   levels=[0.5], colors='black', linewidths=2)
    
    ax1.set_xlabel('Longitude (°)')
    ax1.set_ylabel('Latitude (°)')
    ax1.set_title('Temperature Field with Detected Fronts')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Temperature gradient magnitude
    grad_plot = ax2.contourf(lon_grid, lat_grid, grad_magnitude, levels=20, cmap='plasma')
    plt.colorbar(grad_plot, ax=ax2, label='Temperature Gradient (°C/km)')
    
    ax2.set_xlabel('Longitude (°)')
    ax2.set_ylabel('Latitude (°)')
    ax2.set_title('Temperature Gradient Magnitude')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(
        description='Detect weather fronts from temperature gradient analysis'
    )
    parser.add_argument('--input-data', required=True,
                       help='Path to input HDF5 file containing temperature grid data')
    parser.add_argument('--output-fronts', required=True,
                       help='Path to output JSON file containing detected front information')
    parser.add_argument('--output-plot', required=True,
                       help='Path to output PNG file showing temperature field with detected fronts')
    parser.add_argument('--gradient-threshold', type=float, default=2.0,
                       help='Minimum temperature gradient magnitude (°C/km) for front detection')
    parser.add_argument('--min-front-length', type=int, default=5,
                       help='Minimum length (grid points) for a valid front segment')
    parser.add_argument('--smoothing-sigma', type=float, default=1.0,
                       help='Gaussian smoothing parameter for temperature field')
    
    args = parser.parse_args()
    
    try:
        # Load atmospheric data
        print("Loading atmospheric data...")
        temperature, lat, lon, grid_spacing = load_atmospheric_data(args.input_data)
        
        # Validate input parameters
        if args.gradient_threshold <= 0:
            raise ValueError("Gradient threshold must be positive")
        if args.min_front_length < 1:
            raise ValueError("Minimum front length must be at least 1")
        if args.smoothing_sigma < 0:
            raise ValueError("Smoothing sigma must be non-negative")
        
        # Detect weather fronts
        print("Detecting weather fronts...")
        front_segments, grad_magnitude, labeled_fronts = detect_weather_fronts(
            temperature, grid_spacing, args.gradient_threshold,
            args.min_front_length, args.smoothing_sigma
        )
        
        # Prepare metadata
        metadata = {
            'gradient_threshold': args.gradient_threshold,
            'min_front_length': args.min_front_length,
            'smoothing_sigma': args.smoothing_sigma,
            'grid_spacing_km': float(grid_spacing),
            'temperature_range': {
                'min': float(np.min(temperature)),
                'max': float(np.max(temperature))
            },
            'domain_extent': {
                'lat_min': float(np.min(lat)),
                'lat_max': float(np.max(lat)),
                'lon_min': float(np.min(lon)),
                'lon_max': float(np.max(lon))
            }
        }
        
        # Save front detection results
        print(f"Saving {len(front_segments)} detected fronts...")
        save_front_data(front_segments, args.output_fronts, metadata)
        
        # Create visualization
        print("Creating visualization...")
        create_visualization(temperature, lat, lon, front_segments, 
                           labeled_fronts, grad_magnitude, args.output_plot)
        
        print(f"Front detection complete. Found {len(front_segments)} weather fronts.")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
