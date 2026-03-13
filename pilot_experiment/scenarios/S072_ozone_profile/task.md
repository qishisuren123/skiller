# Atmospheric Ozone Profile Analysis

Create a CLI script that processes vertical ozone profiles from ozonesonde balloon measurements and generates standardized analysis outputs.

Ozonesondes are balloon-borne instruments that measure ozone concentrations at different altitudes in the atmosphere. Your script should analyze these vertical profiles to extract key atmospheric parameters and generate both statistical summaries and visualization outputs.

## Requirements

1. **Data Processing**: Accept synthetic ozonesonde data containing altitude (km), pressure (hPa), temperature (K), and ozone concentration (mPa) measurements. Handle missing values and apply basic quality control by removing measurements where ozone concentrations are negative or unrealistically high (>20 mPa).

2. **Tropospheric Analysis**: Identify the tropopause height using the temperature lapse rate method (first altitude where lapse rate becomes less than 2 K/km over a 2 km layer). Calculate total tropospheric ozone column by integrating ozone concentrations from surface to tropopause.

3. **Stratospheric Metrics**: Determine the altitude and concentration of the ozone maximum in the stratosphere (above tropopause). Calculate the stratospheric ozone column from tropopause to 30 km altitude.

4. **Profile Characterization**: Compute ozone scale height in the lower stratosphere (tropopause + 5 km to tropopause + 15 km) by fitting an exponential decay model to the ozone concentration profile.

5. **Statistical Output**: Generate a JSON summary file containing tropopause height, tropospheric column, stratospheric column, ozone maximum altitude and concentration, and stratospheric scale height with their respective units.

6. **Visualization**: Create a publication-quality plot showing the ozone concentration profile vs altitude, marking the tropopause height and ozone maximum, and save as PNG format.

Use argparse to handle input data dimensions, output file paths, and optional parameters for quality control thresholds.
