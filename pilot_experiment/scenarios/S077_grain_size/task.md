# Grain Size Distribution Analysis

Create a CLI script that analyzes grain size measurements from materials science image analysis and computes statistical distributions.

Your script should accept grain diameter measurements (in micrometers) and generate comprehensive grain size distribution statistics commonly used in materials characterization.

## Requirements

1. **Input Processing**: Accept grain diameter measurements as a comma-separated list via command line argument `--diameters` or `--grain_diameters`. Parse the string into numerical values for analysis.

2. **Basic Statistics**: Calculate and store basic statistical measures including mean, median, standard deviation, minimum, and maximum grain diameters.

3. **Distribution Analysis**: Compute grain size distribution metrics including:
   - D10, D50 (median), and D90 percentiles (diameters below which 10%, 50%, and 90% of grains fall)
   - Coefficient of uniformity (Cu = D60/D10)
   - Coefficient of curvature (Cc = D30²/(D60×D10))

4. **Size Classification**: Classify grains into standard size categories:
   - Fine: < 50 μm
   - Medium: 50-200 μm  
   - Coarse: > 200 μm
   Count and calculate the percentage of grains in each category.

5. **Histogram Generation**: Create a histogram of grain size distribution and save it as `grain_histogram.png`. Include appropriate axis labels, title, and bin sizing.

6. **Output Results**: Save all computed statistics and classifications to a JSON file specified by `--output` argument (default: `grain_analysis.json`). Structure the output with clear sections for basic stats, distribution metrics, and size classifications.

The script should handle typical grain size datasets (50-500 measurements) and provide meaningful statistical analysis for materials characterization applications.

Example usage:
