---
name: neural_population_viz
description: "Create a Python CLI script to visualize neural population activity data from CSV files. Handles large datasets, missing values, and variable neuron recording across trials. Generates heatmaps and population PSTHs with proper error handling."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: neuroscience
---

# Neural Population Visualization

## Overview
This skill creates a robust Python CLI tool for visualizing neural population activity data from CSV files. It processes datasets with trial, time, and neuron firing rate columns to generate trial-averaged heatmaps and population PSTHs (Peri-Stimulus Time Histograms) with error bars.

## When to Use
- Analyzing neural population recordings with multiple neurons across trials
- Creating publication-ready visualizations of firing rate data
- Processing large neural datasets that may exceed memory limits
- Handling datasets with missing values or variable neuron recording across trials
- Converting raw neural data into interpretable population-level summaries

## Inputs
- CSV file with columns: `trial`, `time`, and multiple `neuron_X` columns (where X is neuron index)
- Firing rates can contain commas (European decimal format) or missing values
- Supports various CSV delimiters (comma, semicolon, tab)
- Command line arguments for input file and output directory

## Workflow
1. Execute `scripts/main.py` with required arguments for input CSV and output directory
2. Script automatically detects CSV format and handles numeric formatting issues
3. Loads large datasets in memory-efficient chunks to prevent crashes
4. Processes missing values and calculates robust population statistics
5. Generates two visualizations: trial-averaged heatmap and population PSTH
6. Saves high-resolution plots and prints data summary statistics
7. Refer to `references/workflow.md` for detailed step-by-step process

## Error Handling
The script includes comprehensive error handling for common data issues. It can handle and recover from CSV parsing errors by trying multiple delimiters, manages memory efficiently for large datasets, and processes missing neuron data gracefully. When insufficient neurons are active in trials, it excludes those data points rather than producing misleading statistics.

## Common Pitfalls
- CSV parsing failures due to European number formats with commas
- Memory crashes when processing large neural datasets without chunking
- Misleading population statistics when trials have different numbers of active neurons
- Cluttered heatmap axes when displaying raw time values without proper binning
- SEM calculation errors when trials have insufficient data points

## Output Format
- `firing_rate_heatmap.png`: Trial-averaged heatmap (neurons × time) with proper axis labeling
- `population_psth.png`: Population PSTH with mean firing rate and SEM error bars
- Console output with data summary statistics (neuron count, trial count, time range)
- All plots saved as high-resolution PNG files (300 DPI) with tight bounding boxes
