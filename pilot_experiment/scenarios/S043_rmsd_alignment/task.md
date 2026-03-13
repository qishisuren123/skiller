# Protein Structure RMSD Alignment Tool

Create a command-line tool that performs structural alignment of protein conformations and computes Root Mean Square Deviation (RMSD) values.

Your script should accept two sets of 3D coordinates representing protein structures (reference and target) and perform optimal structural alignment using the Kabsch algorithm. The tool should compute RMSD values before and after alignment, apply the optimal rotation and translation to align the structures, and generate comprehensive alignment statistics.

## Requirements

1. **Input Processing**: Accept two coordinate arrays via command-line arguments representing reference and target protein structures. Each structure should contain N atoms with (x, y, z) coordinates.

2. **Initial RMSD Calculation**: Compute the initial RMSD between reference and target structures before any alignment, using the formula: RMSD = sqrt(mean(sum((ref - target)²))).

3. **Kabsch Alignment**: Implement the Kabsch algorithm to find the optimal rotation matrix and translation vector that minimizes RMSD between the two structures. Center both structures at their centroids before computing the rotation matrix using Singular Value Decomposition (SVD).

4. **Structure Transformation**: Apply the computed rotation matrix and translation vector to transform the target structure coordinates to optimally align with the reference structure.

5. **Final RMSD and Statistics**: Calculate the final RMSD after alignment and generate alignment statistics including the rotation matrix, translation vector, and RMSD improvement percentage.

6. **Output Generation**: Save the aligned target coordinates to a specified output file and create a JSON report containing all alignment metrics, transformation parameters, and statistical summaries.

The tool should handle coordinate arrays of varying sizes and provide robust error handling for degenerate cases where alignment cannot be computed.

## Command Line Interface
