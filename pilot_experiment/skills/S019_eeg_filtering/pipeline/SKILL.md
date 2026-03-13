# EEG Signal Processing CLI Script Development

## Overview
This skill helps build robust Python CLI scripts for processing multi-channel EEG data, including filtering, power spectral density computation, and alpha wave detection. It covers handling common signal processing pitfalls and data validation challenges.

## Workflow
1. **Set up argument parsing** with required input/output paths and optional parameters
2. **Validate input data structure** - check for required columns, numeric data types, and reasonable value ranges
3. **Check signal length requirements** before applying filters to avoid padding errors
4. **Apply adaptive filtering** with length-dependent filter orders and proper error handling
5. **Compute PSD with appropriate parameters** - adjust window size based on signal length
6. **Analyze frequency bands** using physiologically relevant frequency ranges
7. **Handle data type conversion** for JSON serialization of numpy types
8. **Save results** with comprehensive error handling

## Common Pitfalls
- **Filter padding errors**: `filtfilt` requires minimum signal length (3 × max filter coefficient length). Solution: Check signal length and use adaptive filter orders
- **Unrealistic alpha power ratios**: Including DC and very low frequencies in total power calculation inflates denominators. Solution: Use 1-40 Hz range for total power instead of full spectrum
- **Dominant frequency at 0 Hz**: DC components dominating PSD analysis. Solution: Exclude 0-1 Hz range when finding dominant frequencies and use `detrend='constant'` in Welch's method
- **JSON serialization errors**: NumPy data types aren't JSON serializable. Solution: Convert all numpy types to native Python types before saving
- **Missing input validation**: Assuming CSV structure without verification. Solution: Validate column names, data types, and value ranges

## Error Handling
- Wrap filter operations in try-catch blocks to handle individual channel failures gracefully
- Check file existence before processing
- Validate data structure and provide informative error messages
- Use proper exit codes for different failure modes
- Provide fallback behavior (return unfiltered data) when filtering fails

## Quick Reference
