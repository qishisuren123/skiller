---
name: particle_physics_analysis
description: "Write a Python CLI script to analyze particle collision event data from a high-energy physics experiment.

Input: A CSV file where each row is a collision event with columns:
- event_id, n_tracks, total_energy, missing_et, leading_jet_pt, leading_jet_eta, n_jets, n_leptons, invariant_mass

Output: Filtered events CSV, statistical analysis JSON, and significance calculations for signal vs background classification."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: physics
---

# Particle Physics Analysis

## Overview
This skill provides a complete CLI tool for analyzing particle collision event data from high-energy physics experiments. It handles data loading with encoding detection, robust data cleaning for detector output, quality cuts application, signal/background classification, and statistical significance calculations.

## When to Use
- Analyzing CSV data from particle physics detectors
- Filtering collision events based on physics criteria
- Computing signal-to-background ratios and statistical significance
- Handling messy detector data with missing values and encoding issues
- Performing cut-flow analysis for event selection

## Inputs
- CSV file with collision event data containing columns: event_id, n_tracks, total_energy, missing_et, leading_jet_pt, leading_jet_eta, n_jets, n_leptons, invariant_mass
- Mass window parameters for signal region definition
- Output directory path

## Workflow
1. Execute `scripts/main.py` with input CSV and output directory
2. Script detects file encoding automatically (UTF-8, latin-1, cp1252, iso-8859-1)
3. Clean data by converting string missing values ("N/A", "-") to numeric NaN
4. Apply physics quality cuts (n_tracks >= 2, total_energy > 10, |eta| < 2.5)
5. Classify events as signal (in mass window + n_leptons >= 2) or background
6. Calculate statistics only for events within the signal region
7. Output filtered events CSV and summary JSON with significance calculations
8. Reference `references/workflow.md` for detailed step-by-step process

## Error Handling
The script includes comprehensive error handling for common data issues:
- UnicodeDecodeError: Tries multiple encodings to handle detector file formats
- TypeError from string values: Converts non-numeric data to NaN with pd.to_numeric()
- SettingWithCopyWarning: Uses .copy() methods to avoid DataFrame view issues
- Missing critical data: Removes rows with NaN in essential columns
- Division by zero: Handles empty background counts in significance calculations

## Common Pitfalls
- Encoding issues with detector data files - use multiple encoding attempts
- String values in numeric columns - clean with pd.to_numeric(errors='coerce')
- Incorrect significance calculation using total dataset instead of signal region
- DataFrame view warnings - always use .copy() after filtering operations
- Unrealistic significance values - ensure background estimation is region-specific

## Output Format
- `filtered_events.csv`: Cleaned events with event_type classification column
- `event_summary.json`: Contains total_events, events_after_cleaning, events_after_cuts, signal_events, background_events, signal_in_window, background_in_window, significance, cut_flow
- Console output: Event counts, signal fraction, and statistical significance
