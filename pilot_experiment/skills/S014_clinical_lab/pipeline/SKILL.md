# Clinical Lab Results Processing with Unit Normalization

## Overview
This skill helps create a robust Python CLI script to process clinical laboratory results, normalize units to standard formats, flag abnormal values, and generate both CSV and JSON outputs with comprehensive error handling.

## Workflow
1. **Set up data structures** - Define normalization functions for values, reference ranges, and units
2. **Implement flexible parsing** - Handle various timestamp formats and whitespace issues in CSV data
3. **Process each row** with error handling:
   - Strip whitespace from all fields
   - Validate required fields and data ranges
   - Normalize values and reference ranges consistently
   - Flag results using normalized values against normalized ranges
   - Track patient summaries with most recent dates
4. **Generate outputs** - Write processed CSV with both original and normalized data, plus JSON summary
5. **Report statistics** - Display processing summary and error counts

## Common Pitfalls
- **Whitespace in CSV data**: Always `.strip()` all parsed CSV fields to avoid conversion errors
- **Inconsistent normalization**: Must normalize both values AND reference ranges, not just values
- **Reference range logic**: Compare normalized values against normalized reference ranges for consistency
- **Critical flagging logic**: Use simple `value < (ref_low * 0.5) or value > (ref_high * 2.0)` formula
- **Timestamp format assumptions**: Use flexible parsing to handle date-only vs datetime formats
- **Missing error handling**: Always wrap data processing in try-catch blocks for malformed data
- **Output completeness**: Include both original and normalized data in output for transparency

## Error Handling
- Catch `ValueError` for numeric conversion failures
- Catch `KeyError` for missing CSV columns
- Validate reference ranges (ref_low < ref_high)
- Check for required fields (patient_id, test_name)
- Continue processing after errors with warning messages
- Track and report error counts

## Quick Reference
