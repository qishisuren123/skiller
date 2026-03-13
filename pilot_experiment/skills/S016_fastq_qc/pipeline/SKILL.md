# FASTQ Quality Trimming CLI Script Development

## Overview
This skill covers developing a robust Python CLI script for FASTQ quality trimming with proper error handling, memory efficiency, and comprehensive statistics reporting. The script trims low-quality bases from the 3' end of reads and filters by minimum length requirements.

## Workflow
1. **Set up argument parsing** with required parameters (input, output, report files, quality/length thresholds)
2. **Implement streaming FASTQ parser** to handle large files without loading everything into memory
3. **Create quality conversion function** to convert ASCII quality scores to Phred scores with validation
4. **Implement trimming logic** that removes bases from 3' end until finding a base with acceptable quality
5. **Process reads in single pass** collecting statistics and writing output simultaneously
6. **Generate comprehensive report** with before/after statistics and quality distributions
7. **Add robust error handling** for malformed files, edge cases, and invalid data

## Common Pitfalls
- **Loading entire FASTQ into memory**: Use streaming generators for large files instead of reading all reads into a list
- **Incorrect trimming logic**: Trim from 3' end sequentially until finding good quality base, don't remove all bad bases after last good base
- **Division by zero errors**: Always check if any reads passed filtering before calculating averages
- **Inconsistent statistics comparison**: Compare same set of reads before/after trimming, not all original reads vs filtered reads
- **Duplicate processing**: Avoid trimming reads twice by collecting all statistics in single processing loop
- **Poor error handling**: Validate FASTQ format, handle file not found, and gracefully handle edge cases

## Error Handling
- **File validation**: Check file exists and is readable before processing
- **FASTQ format validation**: Verify headers start with '@', plus lines start with '+', sequence/quality length match
- **Quality score validation**: Clamp invalid quality characters to valid Phred range (0-93) with warnings
- **Empty file handling**: Exit gracefully with informative message if no reads found
- **Memory management**: Use generators to avoid memory issues with large files
- **Edge case handling**: Handle reads with all low-quality bases (return empty strings, filter out)

## Quick Reference
