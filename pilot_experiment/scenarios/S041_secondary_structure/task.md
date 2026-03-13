# Secondary Structure Assignment from Backbone Dihedral Angles

Create a CLI script that assigns secondary structure elements to protein residues based on their backbone dihedral angles (phi and psi). This is a fundamental task in protein structure analysis where regions of the protein backbone are classified into alpha-helices, beta-sheets, or coil/loop regions based on their local geometry.

Your script should accept phi and psi dihedral angles for a protein sequence and output secondary structure assignments using a simplified Ramachandran plot-based classification scheme.

## Requirements

1. **Input Processing**: Accept a CSV file path containing columns 'residue_id', 'phi', and 'psi' representing residue identifiers and their backbone dihedral angles in degrees. Handle missing angle values (NaN) by assigning them as 'C' (coil).

2. **Secondary Structure Classification**: Implement a Ramachandran-based classification system:
   - Alpha-helix (H): -180° ≤ phi ≤ 0° and -90° ≤ psi ≤ 50°
   - Beta-sheet (E): -180° ≤ phi ≤ -50° and 50° ≤ psi ≤ 180°
   - Coil/Loop (C): All other angle combinations

3. **Smoothing Filter**: Apply a simple smoothing rule where isolated single residues (length 1) of H or E surrounded by different secondary structure are converted to C to reduce noise in assignments.

4. **Statistics Calculation**: Calculate and display summary statistics including the percentage of residues in each secondary structure class and the average length of continuous H and E segments.

5. **Output Generation**: Save results to a JSON file containing the residue-by-residue assignments and summary statistics, and create a CSV file with columns 'residue_id', 'phi', 'psi', 'ss_assignment'.

6. **Visualization**: Generate a Ramachandran plot showing the phi/psi angles colored by assigned secondary structure and save as a PNG file.

Use argparse for command-line interface with arguments for input file path, output JSON path, output CSV path, and plot path.
