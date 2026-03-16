---
name: solar_flare_detection
description: "# Solar Flare Detection and Classification

Create a CLI script that detects and classifies solar flare events from synthetic X-ray light curve data.

Solar flares are sudden releases of electromagnetic energy from the Sun's corona that can be detected through X-ray flux measurements. This tool generates synthetic data, applies threshold-based detection algorithms, and classifies flares into standard C/M/X categories based on peak intensity ratios."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: astronomy
---

# Solar Flare Detection and Classification

## Overview

This skill provides a complete CLI tool for solar flare detection and classification from X-ray light curve data. It generates synthetic solar X-ray flux data with embedded flare events, detects flares using robust threshold-based algorithms, classifies them into standard solar flare categories (C/M/X class), and produces both JSON results and visualization plots.

The tool handles various edge cases including different time resolutions, short observation periods, and datasets with high flare activity that can interfere with noise estimation.

## When to Use

- Analyzing solar X-ray light curve data for flare events
- Testing flare detection algorithms on synthetic data
- Educational demonstrations of solar flare classification
- Prototyping automated solar weather monitoring systems
- Benchmarking detection performance with known synthetic events

## Inputs

- **Duration**: Observation period in hours (default: 24)
- **Resolution**: Time sampling resolution in minutes (default: 1)
- **Output files**: JSON results file and PNG plot file paths
- **Verbosity**: Optional detailed logging for debugging

## Workflow

1. Execute `scripts/main.py` with desired parameters
2. Generate synthetic X-ray flux data with embedded flare events
3. Apply robust threshold-based detection algorithm with noise estimation
4. Classify detected flares into C/M/X categories based on peak flux ratios
5. Save results to JSON file and generate visualization plot
6. Review detection performance and flare statistics
7. Consult `references/pitfalls.md` for common error handling patterns

## Error Handling

The tool includes comprehensive error handling for common issues:
- **Empty noise arrays**: Uses fallback noise estimation when quiet periods cannot be identified
- **Array bounds errors**: Properly handles different time resolutions and prevents index overflow
- **Matplotlib legend conflicts**: Avoids duplicate labels that cause plotting errors
- **Edge case detection**: Handles flares extending to data boundaries
- **Invalid thresholds**: Provides robust threshold calculation even with limited data

## Common Pitfalls

- **Resolution mismatch**: Ensure flare duration calculations account for time resolution
- **Noise estimation failure**: Use multiple fallback methods for threshold calculation
- **Plotting legend errors**: Track added labels to prevent matplotlib conflicts
- **Boundary conditions**: Handle flares at start/end of observation period
- **Duration units**: Maintain consistency between minutes and data points

## Output Format

**JSON Results:**
