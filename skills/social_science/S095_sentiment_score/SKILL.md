---
name: sentiment_score
description: "# Sentiment Score Analysis for Survey Responses

Create a CLI script that analyzes sentiment scores for open-ended survey responses using a simple lexicon-based approach. Your script should process survey data with demographic information and generate statistical summaries and visualizations by demographic groups."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: social_science
---

# Sentiment Score

## Overview
A command-line tool for analyzing sentiment in survey responses using lexicon-based scoring. Processes CSV files containing survey responses with demographic data (age groups, regions) and generates sentiment statistics, visualizations, and detailed reports. Optimized for large datasets with batch processing and efficient memory usage.

## When to Use
- Analyzing customer feedback surveys with demographic breakdowns
- Processing open-ended survey responses for sentiment trends
- Generating demographic-based sentiment reports for research
- Quick sentiment analysis without machine learning dependencies
- Batch processing of large survey datasets (1000+ responses)

## Inputs
- CSV file with columns: response_text, age_group, region
- Optional output file paths for JSON results, CSV scores, and charts
- Age groups should follow format: "18-25", "26-40", "41-60", "60+"
- Text responses can contain any open-ended survey feedback

## Workflow
1. Run `python scripts/main.py input_survey.csv` to process survey data
2. Script validates CSV format and required columns (response_text, age_group, region)
3. Calculates sentiment scores using lexicon-based approach with positive/negative word lists
4. Groups responses by demographic categories and calculates statistics
5. Generates JSON summary, CSV with individual scores, and demographic charts
6. Follow troubleshooting steps in references/pitfalls.md for common issues
7. Review output files for sentiment trends across demographic groups

## Error Handling
The script includes comprehensive error handling for file processing issues. It will handle missing CSV files, empty datasets, malformed rows, and invalid column formats. When errors occur during processing, the script logs warnings and continues with valid data. File writing operations include proper error checking and validation to ensure output integrity.

## Common Pitfalls
- CSV files with missing required columns cause validation errors
- Old output files can interfere with results - always check for existing files
- Large datasets may require performance optimization with batch processing
- Matplotlib string sorting issues with age group labels need numeric positioning
- Empty or corrupted CSV files need proper validation before processing

## Output Format
- JSON file: Complete results with overall statistics, demographic breakdowns, and individual responses
- CSV file: Individual responses with calculated sentiment scores
- PNG chart: Bar charts showing average sentiment by age group and region
- Console output: Processing progress and summary statistics
- Sentiment scores range from -1.0 (most negative) to 1.0 (most positive)
