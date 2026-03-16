1. Prepare PDB structure data in JSON format with chains, residues, and atomic coordinates
2. Execute the main script with input file and desired parameters
3. Tool loads PDB data and extracts cysteine residues with SG and CB atoms
4. Distance-based filtering identifies potential disulfide bonds within cutoff threshold
5. Geometric validation calculates C-S-S bond angles for each potential bond
6. Angles are compared against expected 104° with specified tolerance
7. Results are compiled with validation statistics and detailed bond information
8. Output is saved as JSON with numpy arrays converted to serializable format
9. Review summary statistics for total cysteines, validated bonds, and chain classifications
10. Examine individual bond details including coordinates, distances, and geometric validation
