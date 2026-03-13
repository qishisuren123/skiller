# Disulfide Bond Detection and Validation

Create a CLI script that analyzes protein structures to detect and validate disulfide bonds between cysteine residues based on atomic distances and geometric constraints.

## Requirements

Your script should accept the following arguments:
- `--input` or `--pdb`: Input PDB structure data (JSON format with atomic coordinates)
- `--output` or `--out`: Output JSON file containing disulfide bond analysis
- `--distance-cutoff` or `--cutoff`: Maximum distance threshold for disulfide bonds (default: 2.5 Å)
- `--angle-tolerance` or `--tolerance`: Angular tolerance for C-S-S bond geometry validation (default: 20 degrees)
- `--energy-model` or `--model`: Energy calculation model ('simple' or 'advanced', default: 'simple')

## Task Requirements

1. **Parse PDB Data**: Read protein structure data containing atomic coordinates, residue information, and chain identifiers for cysteine residues with sulfur atoms.

2. **Distance-Based Detection**: Identify potential disulfide bonds by calculating distances between sulfur atoms of cysteine residues. Bonds must be within the specified distance cutoff and between different residues.

3. **Geometric Validation**: Validate detected bonds using geometric constraints including C-S-S bond angles (expected ~104°) and dihedral angles. Reject bonds that deviate beyond the angular tolerance.

4. **Energy Assessment**: Calculate disulfide bond formation energy using the specified model. Simple model uses distance-based potential, advanced model includes angular strain and electrostatic contributions.

5. **Cross-Chain Analysis**: Distinguish between intra-chain and inter-chain disulfide bonds, reporting statistics for each category including average distances and energy distributions.

6. **Output Generation**: Generate comprehensive JSON output containing detected bonds with coordinates, distances, angles, energies, validation status, and summary statistics including total bonds found and geometric quality metrics.

The output should enable structural biologists to assess disulfide bond networks and their contribution to protein stability.
