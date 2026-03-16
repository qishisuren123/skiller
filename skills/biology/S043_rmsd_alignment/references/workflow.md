1. Load reference and target coordinate files in xyz format
2. Validate coordinate data and check for format consistency
3. Handle atom count mismatches using truncation or padding methods
4. Apply subsampling for large structures exceeding memory limits
5. Center both coordinate sets at their respective centroids
6. Compute covariance matrix using memory-efficient chunked operations
7. Perform Singular Value Decomposition (SVD) on covariance matrix
8. Calculate optimal rotation matrix using Kabsch algorithm
9. Apply rotation transformation to target coordinates
10. Compute final RMSD after optimal alignment
11. Transform coordinates back to reference frame
12. Save aligned coordinates and generate comprehensive JSON report
13. Output alignment statistics and performance metrics
