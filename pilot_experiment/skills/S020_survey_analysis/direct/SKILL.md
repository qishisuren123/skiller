# Likert Scale Survey Analysis with Reverse Coding

## Overview
This skill enables comprehensive analysis of Likert-scale survey data including reverse coding of negatively worded items, composite score calculation, reliability analysis using Cronbach's alpha, and demographic group comparisons.

## Workflow
1. **Parse command line arguments** using argparse to get input CSV path, output directory, and items to reverse-code
2. **Load and validate survey data** ensuring all required columns exist and Likert values are in valid range (1-5)
3. **Apply reverse coding transformation** to specified items using formula: reverse_value = 6 - original_value
4. **Calculate composite scale scores** by computing means of item groups (scale_A: q1-q5, scale_B: q6-q10)
5. **Compute Cronbach's alpha reliability** for each scale using the standardized formula with item and total variances
6. **Perform demographic group analysis** calculating means and standard deviations by gender groups
7. **Export results** to CSV and JSON files, and print summary statistics to console

## Common Pitfalls
- **Missing data handling**: Likert data often has missing values - use pandas dropna() or fillna() appropriately before calculations
- **Cronbach's alpha edge cases**: Formula fails when total variance is zero (all responses identical) - add validation checks
- **Reverse coding confusion**: Ensure reverse coding is applied before composite score calculation, not after
- **Gender group filtering**: Handle case-sensitive gender values and potential missing/invalid gender entries
- **Output directory creation**: Script fails if output directory doesn't exist - use os.makedirs(exist_ok=True)

## Error Handling
- Validate input CSV has required columns and numeric Likert values in range 1-5
- Check for sufficient sample size (n≥3) before computing Cronbach's alpha
- Handle division by zero in reliability calculations when variance is zero
- Gracefully handle empty gender groups in demographic analysis

## Quick Reference
