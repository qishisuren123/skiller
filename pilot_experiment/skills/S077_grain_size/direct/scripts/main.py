#!/usr/bin/env python3
"""
Grain Size Distribution Analysis Tool
Analyzes grain diameter measurements for materials science characterization
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any

def parse_diameter_input(diameter_string: str) -> np.ndarray:
    """Parse comma-separated diameter string into numpy array."""
    try:
        diameters = [float(x.strip()) for x in diameter_string.split(',')]
        diameters = np.array(diameters)
        
        # Validate grain size ranges (typical: 0.1 to 10000 μm)
        if np.any(diameters <= 0):
            raise ValueError("All grain diameters must be positive")
        if np.any(diameters > 10000):
            print("Warning: Some grain sizes >10000 μm detected. Verify units are in micrometers.")
        if np.any(diameters < 0.1):
            print("Warning: Some grain sizes <0.1 μm detected. Verify measurement accuracy.")
            
        return diameters
    except ValueError as e:
        raise ValueError(f"Error parsing diameter data: {e}")

def calculate_basic_statistics(diameters: np.ndarray) -> Dict[str, float]:
    """Calculate fundamental statistical measures."""
    return {
        'mean': float(np.mean(diameters)),
        'median': float(np.median(diameters)),
        'std_dev': float(np.std(diameters, ddof=1)),  # Sample standard deviation
        'minimum': float(np.min(diameters)),
        'maximum': float(np.max(diameters)),
        'count': int(len(diameters))
    }

def calculate_distribution_metrics(diameters: np.ndarray) -> Dict[str, float]:
    """Calculate grain size distribution percentiles and coefficients."""
    # Calculate key percentiles using linear interpolation
    d10, d30, d50, d60, d90 = np.percentile(diameters, [10, 30, 50, 60, 90], method='linear')
    
    # Calculate uniformity and curvature coefficients
    cu = d60 / d10 if d10 > 0 else float('inf')
    cc = (d30**2) / (d60 * d10) if (d60 * d10) > 0 else float('inf')
    
    return {
        'd10': float(d10),
        'd30': float(d30),
        'd50': float(d50),
        'd60': float(d60),
        'd90': float(d90),
        'coefficient_uniformity': float(cu),
        'coefficient_curvature': float(cc)
    }

def classify_grain_sizes(diameters: np.ndarray) -> Dict[str, Any]:
    """Classify grains into standard materials science size categories."""
    fine_mask = diameters < 50
    medium_mask = (diameters >= 50) & (diameters <= 200)
    coarse_mask = diameters > 200
    
    fine_count = int(np.sum(fine_mask))
    medium_count = int(np.sum(medium_mask))
    coarse_count = int(np.sum(coarse_mask))
    total_count = len(diameters)
    
    return {
        'fine_grains': {
            'range': '< 50 μm',
            'count': fine_count,
            'percentage': float(fine_count / total_count * 100)
        },
        'medium_grains': {
            'range': '50-200 μm',
            'count': medium_count,
            'percentage': float(medium_count / total_count * 100)
        },
        'coarse_grains': {
            'range': '> 200 μm',
            'count': coarse_count,
            'percentage': float(coarse_count / total_count * 100)
        }
    }

def create_histogram(diameters: np.ndarray, output_file: str = 'grain_histogram.png'):
    """Generate grain size distribution histogram."""
    plt.figure(figsize=(10, 6))
    
    # Use Freedman-Diaconis rule for bin selection
    q75, q25 = np.percentile(diameters, [75, 25])
    iqr = q75 - q25
    bin_width = 2 * iqr / (len(diameters) ** (1/3))
    n_bins = max(10, int((np.max(diameters) - np.min(diameters)) / bin_width))
    n_bins = min(n_bins, 50)  # Cap at 50 bins for readability
    
    plt.hist(diameters, bins=n_bins, alpha=0.7, color='steelblue', edgecolor='black', linewidth=0.5)
    plt.xlabel('Grain Diameter (μm)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Grain Size Distribution', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Add statistical annotations
    mean_val = np.mean(diameters)
    plt.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f} μm')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Histogram saved as {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Analyze grain size distribution from materials science measurements')
    parser.add_argument('--diameters', '--grain_diameters', required=True,
                       help='Comma-separated grain diameters in micrometers')
    parser.add_argument('--output', default='grain_analysis.json',
                       help='Output JSON file for analysis results')
    
    args = parser.parse_args()
    
    try:
        # Parse and validate input data
        diameters = parse_diameter_input(args.diameters)
        
        if len(diameters) < 10:
            print("Warning: Dataset contains <10 measurements. Statistical reliability may be limited.")
        
        print(f"Analyzing {len(diameters)} grain measurements...")
        
        # Perform comprehensive analysis
        basic_stats = calculate_basic_statistics(diameters)
        distribution_metrics = calculate_distribution_metrics(diameters)
        size_classification = classify_grain_sizes(diameters)
        
        # Generate visualization
        create_histogram(diameters)
        
        # Compile results
        results = {
            'analysis_summary': {
                'total_grains': len(diameters),
                'analysis_type': 'Grain Size Distribution Analysis'
            },
            'basic_statistics': basic_stats,
            'distribution_metrics': distribution_metrics,
            'size_classification': size_classification,
            'units': 'micrometers (μm)'
        }
        
        # Save results to JSON
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nAnalysis Results:")
        print(f"Mean grain size: {basic_stats['mean']:.2f} μm")
        print(f"D50 (median): {distribution_metrics['d50']:.2f} μm")
        print(f"Coefficient of uniformity: {distribution_metrics['coefficient_uniformity']:.2f}")
        print(f"Fine grains (<50μm): {size_classification['fine_grains']['percentage']:.1f}%")
        print(f"Results saved to {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
