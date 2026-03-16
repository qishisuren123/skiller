## CSV Reading StopIteration Error

**Error**: StopIteration exception when reading CSV file with csv.DictReader
**Root Cause**: Empty CSV file or file with no content after headers
**Fix**: Add file content validation before creating DictReader, check for empty files and validate required columns exist

## Incorrect Sentiment Score Calculation

**Error**: Positive responses getting negative sentiment scores
**Root Cause**: Dividing by total word count instead of sentiment word count in score calculation
**Fix**: Change denominator to (positive_count + negative_count) instead of total_words, normalize only by sentiment-bearing words

## JSON File Data Corruption

**Error**: Correct sentiment scores during processing but wrong values in saved JSON file
**Root Cause**: Old JSON files with same name interfering with new results
**Fix**: Delete existing output files before running script, add file validation and proper error handling for file operations

## Matplotlib String Comparison Error

**Error**: TypeError with string comparison in matplotlib bar charts for age groups
**Root Cause**: Matplotlib trying to sort string labels like "18-25", "26-40" causing comparison issues
**Fix**: Use numeric positions with range() for bar placement, then set labels with set_xticks() and set_xticklabels()

## Performance Issues with Large Datasets

**Error**: Script hanging or running very slowly on datasets with 10,000+ responses
**Root Cause**: Inefficient text processing and memory usage in sentiment calculation loops
**Fix**: Optimize word processing with single-pass loops, use batch processing with progress logging, switch to numpy for statistical calculations
