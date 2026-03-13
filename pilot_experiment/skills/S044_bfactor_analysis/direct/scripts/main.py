#!/usr/bin/env python3
"""
B-Factor Analysis Tool
Analyzes B-factor distributions in protein structures to identify flexible regions.
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def parse_bfactors(bfactor_string):
    """Parse comma-separated B-factor string into numpy array."""
    try:
        bfactors = np.array([float(x.strip()) for x in bfactor_string.split(',')])
        if len(bfactors) < 5:
            raise ValueError("Minimum 5 B-factor values required for meaningful analysis")
        if np.any(bfactors < 0):
            raise ValueError("B-factors must be non-negative values")
        return bfactors
    except ValueError as e:
        if "could not convert" in str(e):
            raise ValueError("Invalid B-factor data format. Use comma-separated numeric values.")
        raise

def calculate_statistics(bfactors):
    """Calculate comprehensive B-factor statistics."""
    stats = {
        'mean': float(np.mean(bfactors)),
        'median': float(np.median(bfactors)),
        'std': float(np.std(bfactors)),
        'min': float(np.min(bfactors)),
        'max': float(np.max(bfactors)),
        'q25': float(np.percentile(bfactors, 25)),
        'q75': float(np.percentile(bfactors, 75)),
        'count': len(bfactors)
    }
    return stats

def identify_flexible_regions(bfactors):
    """Identify flexible regions above 75th percentile and group into segments."""
    threshold = np.percentile(bfactors, 75)
    flexible_mask = bfactors > threshold
    flexible_positions = np.where(flexible_mask)[0].tolist()
    
    # Group consecutive positions into segments
    segments = []
    if len(flexible_positions) > 0:
        start = flexible_positions[0]
        for i in range(1, len(flexible_positions)):
            if flexible_positions[i] - flexible_positions[i-1] > 1:
                segments.append([start, flexible_positions[i-1]])
                start = flexible_positions[i]
        segments.append([start, flexible_positions[-1]])
    
    return {
        'threshold': float(threshold),
        'positions': flexible_positions,
        'segments': segments,
        'count': len(flexible_positions)
    }

def normalize_bfactors(bfactors):
    """Normalize B-factors to 0-100 scale using min-max normalization."""
    bmin, bmax = np.min(bfactors), np.max(bfactors)
    if bmax == bmin:
        return np.full_like(bfactors, 50.0)  # All values same, return middle value
    normalized = 100 * (bfactors - bmin) / (bmax - bmin)
    return normalized.tolist()

def create_visualization(bfactors, flexible_regions, output_file):
    """Generate B-factor profile plot with flexible regions highlighted."""
    try:
        plt.figure(figsize=(12, 6))
        residue_positions = np.arange(len(bfactors))
        
        # Plot B-factor profile
        plt.plot(residue_positions, bfactors, 'b-', linewidth=2, label='B-factors')
        
        # Highlight flexible regions
        threshold = flexible_regions['threshold']
        plt.axhline(y=threshold, color='red', linestyle='--', alpha=0.7, 
                   label=f'75th percentile ({threshold:.1f})')
        
        # Shade flexible segments
        for start, end in flexible_regions['segments']:
            plt.axvspan(start, end, alpha=0.3, color='red', label='Flexible region' if start == flexible_regions['segments'][0][0] else "")
        
        plt.xlabel('Residue Position')
        plt.ylabel('B-factor (Ų)')
        plt.title('B-factor Analysis: Protein Flexibility Profile')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Visualization saved to {output_file}")
        
    except Exception as e:
        print(f"Warning: Could not create visualization - {e}")

def save_results(results, output_file):
    """Save analysis results to JSON file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_file}")
    except Exception as e:
        print(f"Error saving results: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Analyze B-factor distributions in protein structures')
    parser.add_argument('bfactors', help='Comma-separated B-factor values')
    parser.add_argument('--normalize', action='store_true', 
                       help='Normalize B-factors to 0-100 scale')
    parser.add_argument('--output', default='bfactor_analysis', 
                       help='Output file prefix (default: bfactor_analysis)')
    
    args = parser.parse_args()
    
    try:
        # Parse and validate input data
        bfactors = parse_bfactors(args.bfactors)
        print(f"Analyzing {len(bfactors)} B-factor values...")
        
        # Perform statistical analysis
        stats = calculate_statistics(bfactors)
        flexible_regions = identify_flexible_regions(bfactors)
        
        # Prepare results
        results = {
            'statistics': stats,
            'flexible_regions': flexible_regions,
            'input_bfactors': bfactors.tolist()
        }
        
        # Add normalization if requested
        if args.normalize:
            results['normalized_bfactors'] = normalize_bfactors(bfactors)
            print("B-factors normalized to 0-100 scale")
        
        # Generate outputs
        json_file = f"{args.output}.json"
        png_file = f"{args.output}.png"
        
        save_results(results, json_file)
        create_visualization(bfactors, flexible_regions, png_file)
        
        # Print summary
        print(f"\nAnalysis Summary:")
        print(f"Mean B-factor: {stats['mean']:.2f}")
        print(f"Flexible regions: {flexible_regions['count']} residues in {len(flexible_regions['segments'])} segments")
        if flexible_regions['segments']:
            print(f"Flexible segments: {flexible_regions['segments']}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
