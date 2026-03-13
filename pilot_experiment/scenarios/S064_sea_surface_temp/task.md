# Sea Surface Temperature Anomaly Analysis

Create a CLI script that processes satellite-derived sea surface temperature (SST) data to compute temperature anomalies and generate summary statistics.

Your script should accept gridded SST data as input and compute anomalies relative to a climatological baseline. The analysis will help identify regions of unusual warming or cooling in ocean surface waters.

## Requirements

1. **Data Input**: Accept SST data as a 2D numpy array representing a spatial grid of temperatures in Celsius. The script should generate synthetic SST data when no input file is provided, simulating realistic ocean temperature patterns.

2. **Climatology Calculation**: Compute a baseline climatology by calculating the spatial mean temperature across the entire grid. This represents the expected "normal" temperature for the region.

3. **Anomaly Computation**: Calculate SST anomalies by subtracting the climatological baseline from each grid point. Positive anomalies indicate warmer than normal conditions, while negative anomalies indicate cooler conditions.

4. **Statistical Analysis**: Generate summary statistics including the mean anomaly, standard deviation of anomalies, and the percentage of grid points with anomalies exceeding ±1°C and ±2°C thresholds.

5. **Spatial Analysis**: Identify and report the locations (grid indices) of the maximum positive and negative anomalies, along with their values.

6. **Output Generation**: Save results to a JSON file containing all computed statistics and anomaly threshold information. Also save the anomaly grid as a CSV file for further analysis.

Use argparse to handle command-line arguments for input data dimensions, output filenames, and any processing options. The script should be robust and handle edge cases such as missing data or uniform temperature fields.
