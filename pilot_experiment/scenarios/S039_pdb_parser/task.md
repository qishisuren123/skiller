# PDB Structure Parser and Residue Statistics

Create a command-line tool that parses synthetic PDB (Protein Data Bank) structure data and computes residue-level statistics for protein analysis.

## Task Description

Your script should process synthetic PDB-format protein structure data and generate comprehensive residue-level statistics. The tool will work with simplified PDB data containing atomic coordinates, residue information, and B-factors (temperature factors indicating atomic mobility).

## Requirements

1. **Data Input**: Accept synthetic PDB data via stdin or generate it internally. The data should contain typical PDB fields: atom type, residue name, residue number, chain ID, and XYZ coordinates with B-factors.

2. **Residue Statistics**: Calculate per-residue statistics including:
   - Number of atoms per residue
   - Average B-factor per residue
   - Geometric center coordinates (centroid)
   - Distance from the protein's overall center of mass

3. **Chain Analysis**: Group residues by chain ID and compute chain-level statistics:
   - Total number of residues per chain
   - Average residue B-factor per chain
   - Chain length (distance between first and last residue centroids)

4. **Output Formats**: Generate results in multiple formats:
   - JSON file with detailed residue and chain statistics
   - CSV file with per-residue data suitable for spreadsheet analysis

5. **Filtering Options**: Implement command-line options to:
   - Filter by specific chain IDs
   - Exclude residues with B-factors above a threshold
   - Include only specific residue types (e.g., only amino acids, exclude water)

6. **Summary Report**: Create a text summary showing:
   - Total number of atoms and residues processed
   - Range of B-factors observed
   - Most and least mobile residues (by B-factor)

The script should use argparse for command-line interface and handle typical PDB parsing challenges like missing atoms or non-standard residue names.
