# Protein Contact Map Generator

Create a CLI script that generates residue contact maps from protein atomic coordinates. Contact maps are binary matrices indicating which amino acid residues are in close spatial proximity, providing a simplified representation of protein structure that's useful for fold recognition and structure prediction.

Your script should accept atomic coordinates in a simple format and compute contact maps based on different distance criteria and atom selection methods.

## Requirements

1. **Input Processing**: Accept atomic coordinates via `--coords` argument as a JSON string containing a list of atoms. Each atom should have fields: `residue_id` (integer), `atom_name` (string), `x`, `y`, `z` (float coordinates). Parse and organize atoms by residue.

2. **Distance Calculation**: Implement `--method` argument with options:
   - `ca_only`: Use only C-alpha atoms for distance calculations
   - `min_distance`: Use minimum distance between any atoms of two residues
   - `cb_distance`: Use C-beta atoms (C-alpha for glycine)

3. **Contact Definition**: Accept `--threshold` argument (default 8.0 Angstroms) to define the distance cutoff for considering residues in contact. Residues within this distance are marked as 1 in the contact map, others as 0.

4. **Sequence Separation**: Implement `--min_separation` argument (default 4) to exclude contacts between residues that are too close in sequence (i.e., |i-j| < min_separation).

5. **Output Generation**: Save the contact map as a CSV file specified by `--output` argument, where rows and columns represent residues ordered by residue_id. Include a header row and index column with residue numbers.

6. **Statistics**: Generate a summary JSON file (same name as output but .json extension) containing: total residues, total contacts, contact density (contacts/total_possible), and average contacts per residue.

The contact map should be symmetric and have zeros on the diagonal (residue cannot contact itself).
