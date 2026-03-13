# Example 1: Basic usage with default parameters
python main.py --output-plot ramachandran.png --output-data analysis.json

# Example 2: Large dataset with strict outlier detection
python main.py --num-residues 1000 --outlier-threshold 3.0 \
    --output-plot large_rama.png --output-data large_analysis.json

# Example 3: Programmatic usage of core functions
import numpy as np
from main import generate_synthetic_angles, detect_outliers, calculate_regional_statistics

# Generate test data
phi, psi = generate_synthetic_angles(200)

# Find outliers with custom threshold
outliers, z_scores = detect_outliers(phi, psi, threshold=2.0)
print(f"Found {len(outliers)} outliers")

# Calculate structural composition
stats = calculate_regional_statistics(phi, psi)
print(f"Alpha-helix: {stats['alpha_helix']:.1f}%")
print(f"Beta-sheet: {stats['beta_sheet']:.1f}%")

# Access specific outlier residues
outlier_phi = phi[outliers]
outlier_psi = psi[outliers]
print(f"Most extreme outlier: phi={outlier_phi[0]:.1f}, psi={outlier_psi[0]:.1f}")
