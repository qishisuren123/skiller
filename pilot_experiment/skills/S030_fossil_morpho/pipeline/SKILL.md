# Morphometric Analysis CLI Script Development

## Overview
This skill helps create robust Python CLI scripts for morphometric analysis of fossil specimens, including shape index calculations, PCA analysis, and statistical summaries with proper error handling for real-world data issues.

## Workflow
1. **Set up CLI structure** with argparse for input/output paths
2. **Validate input data** - check file existence and required columns
3. **Calculate shape indices** with division-by-zero protection using np.where()
4. **Perform PCA analysis** with missing data handling and edge case protection
5. **Generate group statistics** that properly handle NaN values
6. **Output results** to multiple file formats (CSV, JSON)

## Common Pitfalls
- **Division by zero in shape indices**: Use np.where() to check denominators before division
- **NaN propagation in PCA**: Remove specimens with missing measurements before standardization
- **Single specimen datasets**: PCA fails with n<2, need special handling
- **Zero standard deviation**: Add epsilon (1e-10) to prevent division by zero in standardization
- **Missing data in statistics**: Use pandas .dropna() and check for empty groups
- **JSON serialization**: Convert numpy types to native Python types with float()

## Error Handling
- Check for file existence before reading CSV
- Validate required columns are present
- Handle specimens with zero/negative measurements
- Remove invalid specimens from PCA but keep in output with NaN
- Check for sufficient specimens (n>=2) for meaningful statistics
- Provide detailed logging of data quality issues

## Quick Reference
