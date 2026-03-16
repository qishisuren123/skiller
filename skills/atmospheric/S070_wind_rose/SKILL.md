---
name: wind_rose
description: "# Wind Rose Statistics Generator

Create a CLI script that processes meteorological wind data to generate wind rose statistics and visualizations. Wind roses are circular plots that show the frequency"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: atmospheric
---

# Wind Rose Statistics Generator

## Overview
Generate wind rose statistics and visualizations from meteorological wind data. This tool processes wind speed and direction measurements, bins them into 16 compass sectors and 4 speed categories, then produces statistical summaries and polar bar chart visualizations. Supports both CSV file input and command-line data entry with automatic column detection.

## When to Use
- Analyzing meteorological wind patterns from weather station data
- Creating wind rose plots for environmental impact assessments
- Processing large datasets of wind measurements for research
- Generating directional wind statistics for renewable energy planning
- Visualizing seasonal or temporal wind patterns

## Inputs
- **CSV Files**: Wind data with speed and direction columns
- **Command Line**: Individual speed and direction values
- **Speed Units**: Wind speeds in m/s
- **Direction Units**: Wind directions in degrees (0-360)
- **Output Options**: JSON statistics file and PNG wind rose plot

## Workflow
1. Execute `scripts/main.py` with appropriate input arguments
2. Load wind data from CSV file or command line arguments
3. Auto-detect column names using common meteorological patterns
4. Bin directions into 16 compass sectors (N, NNE, NE, etc.)
5. Classify speeds into 4 categories (Calm, Light, Moderate, Strong)
6. Calculate frequency statistics for each sector and speed category
7. Generate JSON output with detailed statistics
8. Create polar bar chart visualization with stacked speed categories
9. Reference `references/workflow.md` for detailed processing steps

## Error Handling
The system includes comprehensive error handling for common issues. Memory errors with large datasets are handled by pre-calculating frequency matrices instead of passing raw data to matplotlib. CSV column detection errors are handled with auto-detection fallback and clear error messages listing available columns. Data validation handles NaN values and mismatched array lengths gracefully.

## Common Pitfalls
- **Polar Plot Array Dimensions**: Matplotlib polar projections require careful array dimension handling
- **Memory Issues with Large Datasets**: Pre-calculate binned frequencies rather than plotting raw data
- **CSV Column Name Variations**: Implement auto-detection for common meteorological column naming conventions
- **Direction Binning Alignment**: Ensure compass sectors are properly centered on cardinal directions

## Output Format
- **JSON Statistics**: Sector-wise frequencies, percentages, mean speeds, and speed category breakdowns
- **PNG Wind Rose**: Polar bar chart with 16 directional sectors and color-coded speed categories
- **Logging Output**: Processing status, auto-detection results, and file save confirmations
