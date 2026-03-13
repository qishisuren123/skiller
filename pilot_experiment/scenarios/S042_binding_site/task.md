# Protein Binding Site Prediction from Surface Analysis

Create a CLI tool that identifies potential ligand binding sites on protein surfaces using geometric and physicochemical analysis. The tool should analyze protein surface properties to predict cavities and pockets that could serve as binding sites for small molecule ligands.

## Requirements

Your script should accept the following arguments:
- `--protein_coords`: Path to input file containing 3D protein coordinates (CSV format)
- `--atom_properties`: Path to input file containing atomic properties (CSV format)  
- `--probe_radius`: Radius of spherical probe for surface analysis (default: 1.4 Å)
- `--min_cavity_volume`: Minimum volume threshold for cavity detection (default: 50.0 Å³)
- `--output_sites`: Path to output JSON file containing predicted binding sites
- `--output_surface`: Path to output CSV file containing surface point analysis

The tool must implement the following functionality:

1. **Surface Point Generation**: Generate a grid of surface points around the protein using the probe radius. Calculate solvent-accessible surface points by checking probe accessibility around each atom.

2. **Cavity Detection**: Identify cavities and pockets by clustering surface points that are enclosed or partially enclosed by protein atoms. Use geometric analysis to determine cavity boundaries and volumes.

3. **Physicochemical Scoring**: For each detected cavity, calculate binding site scores based on:
   - Hydrophobic surface area ratio
   - Electrostatic potential distribution
   - Geometric complementarity metrics
   - Cavity depth and accessibility

4. **Site Ranking and Filtering**: Rank potential binding sites by composite scores combining geometric and physicochemical properties. Filter sites below the minimum volume threshold and merge overlapping cavities.

5. **Druggability Assessment**: Evaluate each binding site's druggability using Lipinski-like descriptors adapted for binding pockets, including surface area to volume ratios and hydrophobic moment calculations.

6. **Output Generation**: Export ranked binding sites as JSON with coordinates, volumes, scores, and druggability metrics. Generate detailed surface analysis data as CSV including point coordinates, properties, and cavity assignments.

The algorithm should handle typical protein sizes (100-500 residues) and identify 3-10 potential binding sites ranked by predicted affinity and druggability.
