#!/usr/bin/env python3
import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze grain size distribution from microscopy data')
    parser.add_argument('--diameters', '--grain_diameters', dest='diameters', required=True,
                       help='Comma-separated list of grain diameters in micrometers')
    parser.add_argument('--density', type=float,
                       help='Material density in g/cm³ for specific surface area calculation')
    parser.add_argument('--output', default='grain_analysis.json',
                       help='Output JSON file for analysis results')
    return parser.parse_args()

def clean_diameter_data(diameters):
    """Clean diameter data by removing invalid values"""
    original_count = len(diameters)
    
    # Remove NaN values
    diameters = diameters[~np.isnan(diameters)]
    nan_removed = original_count - len(diameters)
    if nan_removed > 0:
        logging.warning(f"Removed {nan_removed} NaN values")
    
    # Remove zero or negative values
    diameters = diameters[diameters > 0]
    invalid_removed = original_count - nan_removed - len(diameters)
    if invalid_removed > 0:
        logging.warning(f"Removed {invalid_removed} zero or negative values")
    
    # Remove infinite values
    diameters = diameters[np.isfinite(diameters)]
    inf_removed = original_count - nan_removed - invalid_removed - len(diameters)
    if inf_removed > 0:
        logging.warning(f"Removed {inf_removed} infinite values")
    
    logging.info(f"Using {len(diameters)} valid measurements out of {original_count} total")
    return diameters

def calculate_basic_stats(diameters):
    """Calculate basic statistical measures"""
    return {
        'mean': float(np.mean(diameters)),
        'median': float(np.median(diameters)),
        'std_dev': float(np.std(diameters)),
        'min': float(np.min(diameters)),
        'max': float(np.max(diameters)),
        'count': len(diameters)
    }

def calculate_specific_surface_area(mean_diameter_um, density_g_cm3):
    """Calculate specific surface area using SSA = 6/(ρ × d_mean)"""
    if density_g_cm3 is None or density_g_cm3 <= 0:
        return None
    
    # Convert diameter from micrometers to meters
    mean_diameter_m = mean_diameter_um * 1e-6
    # Convert density from g/cm³ to kg/m³
    density_kg_m3 = density_g_cm3 * 1000
    
    # Calculate SSA in m²/kg
    ssa_m2_kg = 6 / (density_kg_m3 * mean_diameter_m)
    # Convert to m²/g
    ssa_m2_g = ssa_m2_kg / 1000
    
    return {
        'value_m2_g': float(ssa_m2_g),
        'units': 'm²/g'
    }

def calculate_distribution_metrics(diameters):
    """Calculate grain size distribution percentiles and coefficients"""
    logging.info(f"Calculating percentiles for {len(diameters)} measurements")
    logging.info(f"Data range: {np.min(diameters):.2f} to {np.max(diameters):.2f} μm")
    
    d10 = np.percentile(diameters, 10)
    d30 = np.percentile(diameters, 30)
    d50 = np.percentile(diameters, 50)
    d60 = np.percentile(diameters, 60)
    d90 = np.percentile(diameters, 90)
    
    logging.info(f"Percentiles - D10: {d10:.2f}, D30: {d30:.2f}, D50: {d50:.2f}, D60: {d60:.2f}, D90: {d90:.2f}")
    
    # Calculate coefficients with proper handling of edge cases
    if d10 > 0:
        cu = d60 / d10
    else:
        cu = None
        logging.warning("Cannot calculate coefficient of uniformity: D10 is zero")
    
    if d10 > 0 and d60 > 0:
        cc = (d30 ** 2) / (d60 * d10)
    else:
        cc = None
        logging.warning("Cannot calculate coefficient of curvature: D10 or D60 is zero")
    
    return {
        'D10': float(d10),
        'D30': float(d30),
        'D50': float(d50),
        'D60': float(d60),
        'D90': float(d90),
        'coefficient_uniformity': cu,
        'coefficient_curvature': cc
    }

def classify_grain_sizes(diameters):
    """Classify grains into size categories"""
    fine = np.sum(diameters < 50)
    medium = np.sum((diameters >= 50) & (diameters <= 200))
    coarse = np.sum(diameters > 200)
    total = len(diameters)
    
    return {
        'fine_count': int(fine),
        'fine_percentage': float(fine / total * 100),
        'medium_count': int(medium),
        'medium_percentage': float(medium / total * 100),
        'coarse_count': int(coarse),
        'coarse_percentage': float(coarse / total * 100)
    }

def create_histogram(diameters, output_path='grain_histogram.png'):
    """Generate and save grain size histogram"""
    logging.info(f"Creating histogram for {len(diameters)} data points")
    logging.info(f"Histogram data range: {np.min(diameters):.2f} to {np.max(diameters):.2f} μm")
    logging.info(f"Data statistics: mean={np.mean(diameters):.2f}, std={np.std(diameters):.2f}")
    logging.info(f"Data type: {diameters.dtype}")
    
    # Ensure data is in the right format for matplotlib
    plot_data = np.asarray(diameters, dtype=np.float64)
    logging.info(f"Plot data type: {plot_data.dtype}")
    logging.info(f"Sample values: {plot_data[:5]}")
    
    # Check for data variability
    if np.std(plot_data) == 0:
        logging.warning("All diameter values are identical - histogram will be flat")
    
    plt.figure(figsize=(10, 6))
    
    # Use explicit bin edges to ensure proper binning
    bin_edges = np.linspace(np.min(plot_data), np.max(plot_data), 31)
    n, bins, patches = plt.hist(plot_data, bins=bin_edges, edgecolor='black', alpha=0.7)
    
    # Log histogram details
    logging.info(f"Histogram bins: {len(bins)} bins from {bins[0]:.2f} to {bins[-1]:.2f}")
    logging.info(f"Bin counts range: {np.min(n)} to {np.max(n)}")
    logging.info(f"Total points in histogram: {np.sum(n)}")
    
    plt.xlabel('Grain Diameter (μm)')
    plt.ylabel('Frequency')
    plt.title('Grain Size Distribution')
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Histogram saved to {output_path}")

def main():
    args = parse_arguments()
    
    # Parse diameter measurements
    diameter_strings = args.diameters.split(',')
    logging.info(f"Parsing {len(diameter_strings)} diameter measurements")
    
    diameters = np.array([float(d.strip()) for d in diameter_strings])
    logging.info(f"Successfully parsed {len(diameters)} measurements")
    
    # Clean the data
    cleaned_diameters = clean_diameter_data(diameters)
    
    if len(cleaned_diameters) == 0:
        logging.error("No valid diameter measurements remaining after cleaning")
        return
    
    # Perform analyses
    basic_stats = calculate_basic_stats(cleaned_diameters)
    distribution_metrics = calculate_distribution_metrics(cleaned_diameters)
    size_classification = classify_grain_sizes(cleaned_diameters)
    
    # Calculate specific surface area if density provided
    ssa = calculate_specific_surface_area(basic_stats['mean'], args.density)
    
    # Create histogram
    create_histogram(cleaned_diameters)
    
    # Compile results
    results = {
        'basic_statistics': basic_stats,
        'distribution_metrics': distribution_metrics,
        'size_classification': size_classification
    }
    
    if ssa is not None:
        results['specific_surface_area'] = ssa
    
    # Save to JSON
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis complete. Results saved to {args.output}")
    print(f"Histogram saved to grain_histogram.png")

if __name__ == '__main__':
    main()
