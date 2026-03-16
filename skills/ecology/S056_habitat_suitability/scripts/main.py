#!/usr/bin/env python3
"""
Habitat Suitability Index Calculator
Calculates HSI for species based on environmental variables
"""

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
import re
from scipy import ndimage
import logging

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

def sanitize_filename(species_name):
    """Convert species name to filesystem-safe filename"""
    # Replace spaces with underscores and remove special characters
    safe_name = re.sub(r'[^\w\s-]', '', species_name)
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    return safe_name.lower()

def generate_synthetic_data(grid_size=50, seed=42):
    """Generate synthetic environmental data layers"""
    np.random.seed(seed)
    logger = logging.getLogger(__name__)
    logger.info(f"Generating synthetic environmental data ({grid_size}x{grid_size})...")
    
    # Temperature (°C) - realistic spatial pattern with some noise
    base_temp = np.random.normal(20, 5, (grid_size, grid_size))
    # Add spatial correlation using gaussian filter
    temperature = ndimage.gaussian_filter(base_temp, sigma=2)
    temperature = np.clip(temperature, -5, 40)  # Realistic temperature range
    
    # Precipitation (mm) - higher values with spatial clustering
    base_precip = np.random.exponential(800, (grid_size, grid_size))
    precipitation = ndimage.gaussian_filter(base_precip, sigma=3)
    precipitation = np.clip(precipitation, 100, 2000)
    
    # Elevation (m) - create some realistic terrain
    x, y = np.meshgrid(np.linspace(0, 10, grid_size), np.linspace(0, 10, grid_size))
    elevation = 500 + 300 * np.sin(x) * np.cos(y) + np.random.normal(0, 50, (grid_size, grid_size))
    elevation = np.clip(elevation, 0, 2000)
    
    # Vegetation density (0-1) - correlated with precipitation
    vegetation = (precipitation - precipitation.min()) / (precipitation.max() - precipitation.min())
    vegetation += np.random.normal(0, 0.1, (grid_size, grid_size))
    vegetation = np.clip(vegetation, 0, 1)
    
    return {
        'temperature': temperature,
        'precipitation': precipitation, 
        'elevation': elevation,
        'vegetation': vegetation
    }

def calculate_temperature_suitability(temperature, temp_range):
    """Calculate temperature suitability using Gaussian curve"""
    temp_min, temp_max = map(float, temp_range.split(','))
    optimal_temp = (temp_min + temp_max) / 2
    temp_std = (temp_max - temp_min) / 4  # 95% within range
    
    suitability = np.exp(-0.5 * ((temperature - optimal_temp) / temp_std) ** 2)
    return suitability

def calculate_precipitation_suitability(precipitation, precip_min):
    """Calculate precipitation suitability - linear increase above minimum"""
    suitability = np.zeros_like(precipitation)
    above_min = precipitation >= precip_min
    
    # Linear increase from minimum to maximum observed precipitation
    precip_max = np.max(precipitation)
    suitability[above_min] = (precipitation[above_min] - precip_min) / (precip_max - precip_min)
    suitability = np.clip(suitability, 0, 1)
    
    return suitability

def calculate_elevation_suitability(elevation):
    """Calculate elevation suitability - inverse relationship"""
    # Normalize elevation to 0-1, then invert
    elev_normalized = (elevation - np.min(elevation)) / (np.max(elevation) - np.min(elevation))
    suitability = 1 - elev_normalized
    return suitability

def calculate_vegetation_suitability(vegetation):
    """Calculate vegetation suitability - direct linear relationship"""
    # Vegetation is already 0-1, so direct relationship
    return vegetation.copy()

def calculate_individual_suitabilities(env_data, temp_range, precip_min):
    """Calculate all individual suitability scores"""
    logger = logging.getLogger(__name__)
    logger.info("Calculating individual suitability scores...")
    
    suitabilities = {}
    suitabilities['temperature'] = calculate_temperature_suitability(env_data['temperature'], temp_range)
    suitabilities['precipitation'] = calculate_precipitation_suitability(env_data['precipitation'], precip_min)
    suitabilities['elevation'] = calculate_elevation_suitability(env_data['elevation'])
    suitabilities['vegetation'] = calculate_vegetation_suitability(env_data['vegetation'])
    
    return suitabilities

def calculate_hsi(suitabilities, weights):
    """Calculate weighted Habitat Suitability Index"""
    logger = logging.getLogger(__name__)
    
    # Validate weights
    weights_array = np.array([float(w) for w in weights.split(',')])
    if len(weights_array) != 4:
        raise ValueError("Must provide exactly 4 weights")
    if not np.isclose(np.sum(weights_array), 1.0):
        raise ValueError(f"Weights must sum to 1.0, got {np.sum(weights_array)}")
    
    logger.info("Calculating weighted HSI...")
    
    # Calculate weighted sum
    factors = ['temperature', 'precipitation', 'elevation', 'vegetation']
    hsi = np.zeros_like(suitabilities['temperature'])
    
    for i, factor in enumerate(factors):
        hsi += weights_array[i] * suitabilities[factor]
    
    return hsi

def calculate_summary_stats(hsi):
    """Calculate summary statistics for HSI"""
    logger = logging.getLogger(__name__)
    logger.info("Calculating summary statistics...")
    
    mean_hsi = np.mean(hsi)
    highly_suitable_pct = np.sum(hsi > 0.7) / hsi.size * 100
    
    # Memory-efficient approach to find top 5 locations
    # Process in chunks to avoid memory issues
    chunk_size = min(1000000, hsi.size)  # 1M elements max per chunk
    top_values = []
    top_indices = []
    
    hsi_flat = hsi.ravel()
    
    for start_idx in range(0, hsi.size, chunk_size):
        end_idx = min(start_idx + chunk_size, hsi.size)
        chunk = hsi_flat[start_idx:end_idx]
        
        # Find top values in this chunk
        if len(chunk) >= 5:
            chunk_top_idx = np.argpartition(chunk, -5)[-5:]
        else:
            chunk_top_idx = np.arange(len(chunk))
        
        # Convert to global indices
        global_indices = start_idx + chunk_top_idx
        chunk_values = hsi_flat[global_indices]
        
        top_values.extend(chunk_values)
        top_indices.extend(global_indices)
    
    # Now find overall top 5
    if len(top_values) >= 5:
        overall_top_idx = np.argpartition(top_values, -5)[-5:]
        final_indices = [top_indices[i] for i in overall_top_idx]
    else:
        final_indices = top_indices
    
    # Convert flat indices to 2D coordinates
    top_coords = np.unravel_index(final_indices, hsi.shape)
    optimal_locations = [(int(row), int(col)) for row, col in zip(top_coords[0], top_coords[1])]
    
    # Sort by HSI value (highest first)
    optimal_locations.sort(key=lambda coord: hsi[coord], reverse=True)
    optimal_locations = optimal_locations[:5]  # Keep only top 5
    
    return {
        'mean_hsi': float(mean_hsi),
        'highly_suitable_percentage': float(highly_suitable_pct),
        'optimal_locations': optimal_locations
    }

def save_hsi_csv(hsi, species, output_dir):
    """Save HSI grid as CSV file"""
    logger = logging.getLogger(__name__)
    safe_species = sanitize_filename(species)
    filename = os.path.join(output_dir, f"{safe_species}_hsi.csv")
    
    # Convert to DataFrame for better CSV output
    df = pd.DataFrame(hsi)
    df.to_csv(filename, index=False)
    
    logger.info(f"HSI grid saved to {filename}")

def save_summary_json(summary_stats, species, output_dir):
    """Save summary statistics as JSON file"""
    logger = logging.getLogger(__name__)
    safe_species = sanitize_filename(species)
    filename = os.path.join(output_dir, f"{safe_species}_summary.json")
    
    with open(filename, 'w') as f:
        json.dump(summary_stats, f, indent=2)
    
    logger.info(f"Summary statistics saved to {filename}")

def create_hsi_visualization(hsi, species, output_dir):
    """Create and save HSI heatmap visualization"""
    logger = logging.getLogger(__name__)
    
    plt.figure(figsize=(10, 8))
    im = plt.imshow(hsi, cmap='RdYlGn', vmin=0, vmax=1, origin='lower')
    plt.colorbar(im, label='Habitat Suitability Index')
    plt.title(f'Habitat Suitability Map for {species}')
    plt.xlabel('Grid X Coordinate')
    plt.ylabel('Grid Y Coordinate')
    
    safe_species = sanitize_filename(species)
    filename = os.path.join(output_dir, f"{safe_species}_hsi_map.png")
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"HSI visualization saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Calculate Habitat Suitability Index')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('-s', '--species', required=True, help='Target species name')
    parser.add_argument('-w', '--weights', required=True, help='Comma-separated weights (4 values)')
    parser.add_argument('-t', '--temp_range', default='15,25', help='Optimal temperature range')
    parser.add_argument('-p', '--precip_min', type=float, default=500, help='Minimum precipitation threshold')
    parser.add_argument('--grid_size', type=int, default=50, help='Grid size for synthetic data')
    
    args = parser.parse_args()
    
    logger = setup_logging()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Generate synthetic data
    env_data = generate_synthetic_data(grid_size=args.grid_size)
    
    # Calculate individual suitabilities
    suitabilities = calculate_individual_suitabilities(env_data, args.temp_range, args.precip_min)
    
    # Calculate final HSI
    hsi = calculate_hsi(suitabilities, args.weights)
    
    # Calculate summary statistics
    summary_stats = calculate_summary_stats(hsi)
    
    # Save outputs
    save_hsi_csv(hsi, args.species, args.output)
    save_summary_json(summary_stats, args.species, args.output)
    create_hsi_visualization(hsi, args.species, args.output)
    
    logger.info(f"Analysis complete for {args.species}")
    logger.info(f"Mean HSI: {summary_stats['mean_hsi']:.3f}")
    logger.info(f"Highly suitable habitat: {summary_stats['highly_suitable_percentage']:.1f}%")

if __name__ == "__main__":
    main()
