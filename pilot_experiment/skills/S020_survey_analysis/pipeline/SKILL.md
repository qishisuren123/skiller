# Likert Scale Survey Data Analysis CLI

## Overview
This skill helps create a robust Python CLI script for analyzing Likert-scale survey data, including reverse-coding items, computing composite scores, calculating Cronbach's alpha reliability, and performing group comparisons.

## Workflow
1. **Set up argument parsing** with proper hyphen-to-underscore handling
2. **Load and validate data** from CSV input
3. **Reverse-code specified items** using the formula: 6 - original_value
4. **Compute composite scores** using appropriate original or reverse-coded items
5. **Calculate Cronbach's alpha** using correlation-based approach for numerical stability
6. **Perform group comparisons** by demographic variables
7. **Save outputs** in structured JSON and CSV formats
8. **Add debug output** for troubleshooting during development

## Common Pitfalls
- **Argument parsing confusion**: `--reverse-items` becomes `args.reverse_items` (argparse converts hyphens to underscores)
- **Column reference errors**: Check that reverse-coded columns (e.g., `q3_r`) exist before referencing them in composite score calculations
- **Cronbach's alpha calculation issues**: Using variance-based formula can produce invalid results; correlation-based approach is more numerically stable
- **Composite score logic errors**: Must check both if item is in reverse_items list AND if the reverse-coded column actually exists in dataframe

## Error Handling
- **KeyError prevention**: Always verify column existence before accessing: `if f'{item}_r' in df.columns`
- **Invalid alpha values**: Use correlation-based formula and validate k >= 2 items
- **Missing data handling**: Use `.dropna()` before statistical calculations
- **Empty groups**: Check for sufficient sample sizes in group comparisons

## Quick Reference
