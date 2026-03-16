Initial RMSD: 12.3456 Å
Final RMSD: 2.1234 Å
Improvement: 82.79%
Aligned coordinates saved to: aligned_structure.xyz
Alignment report saved to: alignment_report.json

Example alignment_report.json:
{
  "alignment_statistics": {
    "initial_rmsd_angstrom": 12.3456,
    "final_rmsd_angstrom": 2.1234,
    "improvement_percentage": 82.79,
    "num_atoms_aligned": 1247
  },
  "transformation_parameters": {
    "rotation_matrix": [
      [0.9234, -0.2145, 0.3156],
      [0.1987, 0.9756, 0.0987],
      [-0.3287, 0.0456, 0.9434]
    ],
    "reference_centroid": [-2.14, 5.67, -1.23],
    "target_centroid": [3.45, -1.89, 4.56],
    "translation_vector": [-5.59, 7.56, -5.79]
  }
}
