# High-Energy Physics Event Analysis

## Overview
This skill enables analysis of particle collision event data from high-energy physics experiments, applying quality cuts, event classification, and statistical analysis to identify signal events and compute significance metrics.

## Workflow
1. Parse command-line arguments for input CSV, output directory, and mass window parameters
2. Load collision event data and validate required columns are present
3. Apply sequential quality cuts (track count, energy threshold, jet pseudorapidity) with cut flow tracking
4. Classify events as "signal" or "background" based on invariant mass window and lepton multiplicity
5. Calculate statistical metrics including signal-to-noise ratio and significance (S/√(S+B))
6. Export filtered events to CSV and generate summary statistics in JSON format
7. Display analysis summary with cut efficiency and physics significance

## Common Pitfalls
- **Missing pseudorapidity bounds**: Always apply |eta| < 2.5 cut for detector acceptance, not just eta < 2.5
- **Mass window parsing errors**: Handle both comma-separated strings and numeric ranges, validate min < max
- **Zero background division**: Check for B=0 before computing S/√(S+B) to avoid mathematical errors
- **Cut flow ordering**: Apply cuts sequentially and track cumulative effects, not independent filtering
- **Energy unit assumptions**: Ensure consistent GeV units across total_energy and leading_jet_pt columns

## Error Handling
- Validate CSV contains all required physics columns before processing
- Handle empty datasets after cuts with graceful warnings
- Check for non-numeric values in physics quantities and skip malformed events
- Ensure output directory exists or create it before writing results
- Catch and report file I/O errors with descriptive physics context

## Quick Reference
