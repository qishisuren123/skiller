# Multimodal Biology Dataset Preprocessing

## Overview
This skill helps create a robust Python CLI script for preprocessing multimodal biology datasets containing images, text files, and labels. The script handles file validation, data cleaning, format conversion, and generates a portable manifest with metadata.

## Workflow
1. **Validate inputs**: Check directory structure, file existence, and parameter validity
2. **Load labels**: Read CSV file and create lookup dictionary
3. **Process files**: Iterate through images, match with text files and labels
4. **Handle naming mismatches**: Convert between different ID formats (e.g., "001.jpg" → "sample_001")
5. **Transform data**: Resize images, extract text metadata, copy files to output structure
6. **Generate manifest**: Create JSON manifest with relative paths for portability
7. **Report summary**: Provide statistics on processed/skipped samples

## Common Pitfalls
- **KeyError on missing labels**: Always check if sample_id exists in labels dictionary before accessing
- **ZeroDivisionError on empty results**: Validate that samples were processed before calculating averages
- **Naming convention mismatches**: Image files may use different naming than CSV (e.g., "001.jpg" vs "sample_001")
- **Absolute vs relative paths**: Use relative paths in manifest for portability across systems
- **Missing validation**: Always validate input parameters (positive image sizes, existing directories)
- **Corrupted files**: Images may be corrupted and fail to open - handle gracefully

## Error Handling
- Validate all inputs before processing (directories exist, positive parameters)
- Use try-catch blocks around file operations (image loading, text reading)
- Check file existence before attempting operations
- Gracefully skip problematic samples and report them
- Protect against division by zero when no samples are processed
- Verify image integrity after opening but before processing

## Quick Reference
