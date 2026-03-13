# Spirometry Flow-Volume Analysis

Create a CLI script that processes spirometry flow-volume data and computes key pulmonary function parameters.

Spirometry is a common pulmonary function test that measures how much air a person can inhale and exhale, and how quickly they can exhale. The test produces flow-volume loops showing the relationship between airflow rate and lung volume during forced breathing maneuvers.

Your script should accept synthetic spirometry data (flow rates and volumes over time) and compute standard diagnostic parameters used in clinical practice.

## Requirements

1. **Data Input**: Accept flow-volume data via command line arguments specifying the number of data points to generate (default 1000). Generate synthetic spirometry data representing a complete breathing cycle with realistic flow rates (-8 to +8 L/s) and volumes (0 to 6 L).

2. **FEV1 Calculation**: Compute the Forced Expiratory Volume in 1 second (FEV1) - the volume of air exhaled in the first second of forced expiration. Assume the sampling rate is 100 Hz.

3. **FVC Calculation**: Compute the Forced Vital Capacity (FVC) - the total volume of air exhaled during the forced expiration phase.

4. **FEV1/FVC Ratio**: Calculate the ratio of FEV1 to FVC, which is a key diagnostic parameter for respiratory conditions.

5. **Flow-Volume Plot**: Generate and save a flow-volume loop plot showing flow rate (y-axis) vs. volume (x-axis) as a PNG file.

6. **Results Output**: Save all computed parameters (FEV1, FVC, FEV1/FVC ratio) to a JSON file with appropriate units and formatting.

Use argparse to handle command line arguments for the number of data points, output plot filename, and output JSON filename.
