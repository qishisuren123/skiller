# Wind Rose Statistics Generator

Create a CLI script that processes meteorological wind data to generate wind rose statistics and visualizations. Wind roses are circular plots that show the frequency and strength of winds from different directions at a given location.

Your script should accept wind speed and direction data, then compute directional statistics and generate both tabular summaries and a wind rose plot.

## Requirements

1. **Data Input**: Accept wind speed (m/s) and wind direction (degrees, 0-360) data via command-line arguments. The script should handle both individual values and arrays of measurements.

2. **Direction Binning**: Bin wind directions into 16 compass sectors (N, NNE, NE, ENE, E, ESE, SE, SSE, S, SSW, SW, WSW, W, WNW, NW, NNW), each covering 22.5 degrees.

3. **Speed Classification**: Classify wind speeds into 4 categories: Calm (0-2 m/s), Light (2-5 m/s), Moderate (5-8 m/s), and Strong (>8 m/s).

4. **Statistical Summary**: Generate a JSON file containing frequency statistics for each direction bin, including total frequency, mean wind speed, and frequency distribution across speed categories.

5. **Wind Rose Plot**: Create a polar bar chart (wind rose) showing wind frequency by direction, with bars colored by speed category. Save as PNG format.

6. **Calm Conditions**: Calculate and report the percentage of calm conditions (wind speed < 2 m/s) separately in the statistics.

## Command Line Interface
