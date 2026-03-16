#!/usr/bin/env python3
import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_bfactors(bfactor_string):
    """Parse comma-separated B-factor values from command line."""
    return [float(x.strip()) for x in bfactor_string.split(',')]

def calculate_statistics(bfactors):
    """Calculate basic statistics for B-factor distribution."""
    bfactors = np.array(bfactors)
    
    stats = {
        'mean': float(np.mean(bfactors)),
        'median': float(np.median(bfactors)),
        'std': float(np.std(bfactors)),
        'q25': float(np.percentile(bfactors, 25)),
        'q75': float(np.percentile(bfactors, 75)),
        'min': float(np.min(bfactors)),
        'max': float(np.max(bfactors))
    }
    
    return stats

def identify_flexible_regions(bfactors, threshold_percentile=75):
    """Identify residues with high B-factors (flexible regions)."""
    bfactors = np.array(bfactors)
    threshold = np.percentile(bfactors, threshold_percentile)
    
    flexible_residues = []
    for i, bf in enumerate(bfactors):
        if bf >= threshold:
            flexible_residues.append(i + 1)  # 1-based residue numbering
    
    return flexible_residues, float(threshold)

def group_consecutive_segments(residue_list):
    """Group consecutive residues into segments."""
    if not residue_list:
        return []
    
    segments = []
    start = residue_list[0]
    end = start
    
    for i in range(1, len(residue_list)):
        current_residue = residue_list[i]
        
        if current_residue == end + 1:
            end = current_residue
        else:
            segments.append({'start': int(start), 'end': int(end)})
            start = current_residue
            end = start
    
    # Add the final segment
    segments.append({'start': int(start), 'end': int(end)})
    
    return segments

def normalize_bfactors(bfactors):
    """Normalize B-factors to 0-100 scale."""
    bfactors = np.array(bfactors)
    min_val = np.min(bfactors)
    max_val = np.max(bfactors)
    
    if max_val == min_val:
        return [50.0] * len(bfactors)
    
    normalized = 100 * (bfactors - min_val) / (max_val - min_val)
    return [float(x) for x in normalized]

def create_bfactor_plot(bfactors, flexible_residues, flexible_segments, threshold, output_prefix='bfactor_plot'):
    """Create a line plot of B-factors with highlighted flexible regions."""
    residue_positions = range(1, len(bfactors) + 1)
    
    plt.figure(figsize=(12, 6))
    
    # Plot all B-factors
    plt.plot(residue_positions, bfactors, 'b-', linewidth=1.5, label='B-factors')
    
    # Highlight flexible residues
    if flexible_residues:
        flexible_positions = [pos - 1 for pos in flexible_residues]  # Convert to 0-based
        flexible_bfactors = [bfactors[pos] for pos in flexible_positions]
        
        plt.scatter(flexible_residues, flexible_bfactors, color='red', s=50, 
                    label=f'Flexible regions (>{threshold:.1f})', zorder=5)
    
    # Add colored spans for flexible segments
    colors = ['yellow', 'lightgreen', 'lightcoral', 'lightblue', 'plum']
    for i, segment in enumerate(flexible_segments):
        color = colors[i % len(colors)]
        plt.axvspan(segment['start'] - 0.5, segment['end'] + 0.5, 
                   alpha=0.2, color=color, 
                   label=f"Segment {i+1}: {segment['start']}-{segment['end']}")
    
    # Add threshold line
    plt.axhline(y=threshold, color='red', linestyle='--', alpha=0.7, 
                label=f'75th percentile ({threshold:.1f})')
    
    plt.xlabel('Residue Position')
    plt.ylabel('B-factor')
    plt.title('B-factor Distribution Along Protein Sequence')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save plot
    plot_filename = f"{output_prefix}.png"
    plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    return plot_filename

def main():
    parser = argparse.ArgumentParser(description='Analyze B-factor distributions in protein structures')
    parser.add_argument('bfactors', help='Comma-separated B-factor values')
    parser.add_argument('-o', '--output', default='bfactor_analysis.json', 
                       help='Output JSON file (default: bfactor_analysis.json)')
    parser.add_argument('--normalize', action='store_true', 
                       help='Normalize B-factors to 0-100 scale')
    parser.add_argument('--plot', default='bfactor_plot',
                       help='Output plot filename prefix (default: bfactor_plot)')
    
    args = parser.parse_args()
    
    # Parse input data
    bfactors = parse_bfactors(args.bfactors)
    print(f"Loaded {len(bfactors)} B-factor values")
    
    # Calculate statistics
    stats = calculate_statistics(bfactors)
    print(f"Mean B-factor: {stats['mean']:.2f}")
    print(f"Standard deviation: {stats['std']:.2f}")
    
    # Identify flexible regions
    flexible_residues, threshold = identify_flexible_regions(bfactors)
    flexible_segments = group_consecutive_segments(flexible_residues)
    
    print(f"Flexibility threshold (75th percentile): {threshold:.2f}")
    print(f"Found {len(flexible_residues)} flexible residues")
    print(f"Grouped into {len(flexible_segments)} segments")
    
    # Print segment details
    for i, segment in enumerate(flexible_segments):
        if segment['start'] == segment['end']:
            print(f"  Segment {i+1}: Residue {segment['start']}")
        else:
            print(f"  Segment {i+1}: Residues {segment['start']}-{segment['end']}")
    
    # Create visualization
    plot_filename = create_bfactor_plot(bfactors, flexible_residues, flexible_segments, threshold, args.plot)
    print(f"Plot saved to {plot_filename}")
    
    # Prepare results
    results = {
        'statistics': stats,
        'flexible_residues': flexible_residues,
        'flexible_segments': flexible_segments,
        'threshold': threshold,
        'plot_filename': plot_filename
    }
    
    # Add normalized B-factors if requested
    if args.normalize:
        normalized_bfactors = normalize_bfactors(bfactors)
        results['normalized_bfactors'] = normalized_bfactors
        print("B-factors normalized to 0-100 scale")
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {args.output}")

if __name__ == '__main__':
    main()
