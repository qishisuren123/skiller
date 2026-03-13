#!/usr/bin/env python3
"""
Ramachandran Plot Analysis Tool
Generates synthetic protein backbone dihedral angles and performs structural analysis.
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from pathlib import Path

def generate_synthetic_angles(num_residues):
    """Generate realistic phi/psi dihedral angles with biological distributions."""
    np.random.seed(42)  # For reproducible results
    
    phi_angles = []
    psi_angles = []
    
    # Define structural regions with realistic parameters
    # Alpha-helix: phi≈-60°, psi≈-45°
    # Beta-sheet: phi≈-120°, psi≈+120°
    # Random coil: broader distribution
    
    for i in range(num_residues):
        rand = np.random.random()
        
        if rand < 0.4:  # 40% alpha-helix
            phi = np.random.normal(-60, 15)
            psi = np.random.normal(-45, 15)
        elif rand < 0.7:  # 30% beta-sheet
            phi = np.random.normal(-120, 20)
            psi = np.random.normal(120, 20)
        else:  # 30% random coil + outliers
            phi = np.random.uniform(-180, 180)
            psi = np.random.uniform(-180, 180)
        
        # Ensure angles are in [-180, 180] range
        phi = ((phi + 180) % 360) - 180
        psi = ((psi + 180) % 360) - 180
        
        phi_angles.append(phi)
        psi_angles.append(psi)
    
    return np.array(phi_angles), np.array(psi_angles)

def detect_outliers(phi, psi, threshold=2.5):
    """Identify structural outliers using kernel density estimation."""
    # Prepare data for KDE
    angles = np.column_stack([phi, psi])
    
    try:
        # Perform kernel density estimation
        kde = gaussian_kde(angles.T)
        densities = kde(angles.T)
        
        # Calculate z-scores based on density
        mean_density = np.mean(densities)
        std_density = np.std(densities)
        
        if std_density == 0:
            return np.array([]), np.zeros(len(phi))
        
        z_scores = (densities - mean_density) / std_density
        
        # Identify outliers (low density regions)
        outlier_indices = np.where(z_scores < -threshold)[0]
        
        return outlier_indices, z_scores
        
    except Exception as e:
        print(f"Warning: Outlier detection failed: {e}")
        return np.array([]), np.zeros(len(phi))

def calculate_regional_statistics(phi, psi):
    """Calculate percentage of residues in different structural regions."""
    stats = {
        'alpha_helix': 0,
        'beta_sheet': 0,
        'left_handed_helix': 0,
        'disallowed': 0,
        'other_allowed': 0
    }
    
    total = len(phi)
    
    for p, s in zip(phi, psi):
        # Alpha-helix region: phi ∈ [-90, -30], psi ∈ [-70, -20]
        if -90 <= p <= -30 and -70 <= s <= -20:
            stats['alpha_helix'] += 1
        # Beta-sheet region: phi ∈ [-150, -90], psi ∈ [90, 150]
        elif -150 <= p <= -90 and 90 <= s <= 150:
            stats['beta_sheet'] += 1
        # Left-handed helix: phi ∈ [30, 90], psi ∈ [30, 90]
        elif 30 <= p <= 90 and 30 <= s <= 90:
            stats['left_handed_helix'] += 1
        # Disallowed regions (simplified)
        elif (-90 <= p <= 30 and -90 <= s <= 30) or (90 <= p <= 150 and -30 <= s <= 30):
            stats['disallowed'] += 1
        else:
            stats['other_allowed'] += 1
    
    # Convert to percentages
    for key in stats:
        stats[key] = (stats[key] / total) * 100
    
    return stats

def create_ramachandran_plot(phi, psi, outliers, output_file):
    """Generate a publication-quality Ramachandran plot."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create density-based coloring
    angles = np.column_stack([phi, psi])
    try:
        kde = gaussian_kde(angles.T)
        densities = kde(angles.T)
    except:
        densities = np.ones(len(phi))  # Fallback to uniform coloring
    
    # Create scatter plot with density coloring
    scatter = ax.scatter(phi, psi, c=densities, cmap='viridis', 
                        alpha=0.6, s=20, edgecolors='none')
    
    # Highlight outliers
    if len(outliers) > 0:
        ax.scatter(phi[outliers], psi[outliers], c='red', s=30, 
                  marker='x', linewidths=2, label=f'Outliers ({len(outliers)})')
    
    # Set up the plot
    ax.set_xlim(-180, 180)
    ax.set_ylim(-180, 180)
    ax.set_xlabel('φ (phi) angle (degrees)', fontsize=12)
    ax.set_ylabel('ψ (psi) angle (degrees)', fontsize=12)
    ax.set_title('Ramachandran Plot', fontsize=14, fontweight='bold')
    
    # Add grid
    ax.grid(True, alpha=0.3)
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(-180, 181, 60))
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Density', fontsize=10)
    
    # Add legend if outliers exist
    if len(outliers) > 0:
        ax.legend()
    
    # Add structural region annotations
    ax.text(-60, -45, 'α', fontsize=16, fontweight='bold', 
            ha='center', va='center', color='white',
            bbox=dict(boxstyle='circle', facecolor='black', alpha=0.7))
    ax.text(-120, 120, 'β', fontsize=16, fontweight='bold',
            ha='center', va='center', color='white',
            bbox=dict(boxstyle='circle', facecolor='black', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def export_analysis_results(phi, psi, outliers, z_scores, stats, output_file):
    """Export comprehensive analysis results to JSON."""
    results = {
        'metadata': {
            'num_residues': len(phi),
            'num_outliers': len(outliers),
            'outlier_percentage': (len(outliers) / len(phi)) * 100
        },
        'angles': {
            'phi': phi.tolist(),
            'psi': psi.tolist()
        },
        'outlier_analysis': {
            'outlier_indices': outliers.tolist(),
            'z_scores': z_scores.tolist()
        },
        'structural_statistics': stats,
        'summary': {
            'favored_regions': stats['alpha_helix'] + stats['beta_sheet'],
            'allowed_regions': stats['other_allowed'] + stats['left_handed_helix'],
            'disallowed_regions': stats['disallowed']
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(
        description='Generate Ramachandran plot analysis for protein backbone dihedral angles'
    )
    parser.add_argument('--num-residues', '--num_residues', type=int, default=500,
                       help='Number of residues to generate (default: 500)')
    parser.add_argument('--output-plot', '--output_plot', type=str, required=True,
                       help='Output PNG file for the Ramachandran plot')
    parser.add_argument('--output-data', '--output_data', type=str, required=True,
                       help='Output JSON file containing angle data and analysis')
    parser.add_argument('--outlier-threshold', '--outlier_threshold', type=float, default=2.5,
                       help='Z-score threshold for outlier detection (default: 2.5)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.num_residues < 10:
        raise ValueError("Number of residues must be at least 10")
    if args.outlier_threshold < 0:
        raise ValueError("Outlier threshold must be positive")
    
    # Create output directories if needed
    Path(args.output_plot).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_data).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {args.num_residues} synthetic dihedral angles...")
    phi, psi = generate_synthetic_angles(args.num_residues)
    
    print("Detecting structural outliers...")
    outliers, z_scores = detect_outliers(phi, psi, args.outlier_threshold)
    
    print("Calculating regional statistics...")
    stats = calculate_regional_statistics(phi, psi)
    
    print("Creating Ramachandran plot...")
    create_ramachandran_plot(phi, psi, outliers, args.output_plot)
    
    print("Exporting analysis results...")
    export_analysis_results(phi, psi, outliers, z_scores, stats, args.output_data)
    
    # Print summary
    print("\n=== Analysis Summary ===")
    print(f"Total residues: {len(phi)}")
    print(f"Outliers detected: {len(outliers)} ({len(outliers)/len(phi)*100:.1f}%)")
    print(f"Alpha-helix region: {stats['alpha_helix']:.1f}%")
    print(f"Beta-sheet region: {stats['beta_sheet']:.1f}%")
    print(f"Disallowed regions: {stats['disallowed']:.1f}%")
    print(f"\nPlot saved to: {args.output_plot}")
    print(f"Data saved to: {args.output_data}")

if __name__ == "__main__":
    main()
