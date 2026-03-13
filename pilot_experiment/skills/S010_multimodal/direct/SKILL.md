# Multimodal Biology Dataset Preprocessing

## Overview
This skill helps preprocess multimodal biology datasets by standardizing images, extracting text statistics, and creating a unified manifest for machine learning model training. It handles image resizing, text analysis, and metadata generation while maintaining data integrity across modalities.

## Workflow
1. Parse command-line arguments for input directory, output directory, and target image size
2. Load and validate the labels.csv file, creating a sample_id to label mapping
3. Create output directory structure (images/, texts/, manifest.json)
4. Process each image: load, capture original dimensions, resize to target size, save as PNG
5. Process corresponding text files: read content, compute word and character counts
6. Generate manifest.json with sample metadata including paths, labels, and statistics
7. Print comprehensive summary with sample counts, label distribution, and text statistics

## Common Pitfalls
- **Missing file pairs**: Not all images have corresponding text files or vice versa. Solution: Use set intersection to process only complete sample pairs and log missing files.
- **Invalid image formats**: Some .jpg files may be corrupted or in unexpected formats. Solution: Wrap PIL operations in try-catch blocks and skip invalid files with logging.
- **Memory issues with large datasets**: Loading all data at once can cause memory problems. Solution: Process files one at a time and use generators for large datasets.
- **Inconsistent sample_id formats**: Image filenames might not exactly match sample_ids in CSV. Solution: Normalize sample_ids by removing extensions and standardizing case.
- **Text encoding issues**: Biology text files may contain special characters or different encodings. Solution: Use UTF-8 with error handling and fallback to latin-1 encoding.

## Error Handling
- Validate input directory structure exists before processing
- Use try-catch blocks around file I/O operations with specific error logging
- Check for empty or malformed CSV files with pandas error handling
- Implement graceful degradation: skip problematic samples but continue processing
- Validate output directory permissions before starting batch operations

## Quick Reference
