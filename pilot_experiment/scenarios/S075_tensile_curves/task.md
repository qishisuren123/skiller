# Tensile Test Curve Analysis

Create a CLI script that processes tensile test stress-strain data and extracts key mechanical properties from the curves.

Your script should accept tensile test data containing stress (MPa) and strain (dimensionless) measurements, then calculate and output important material properties commonly used in materials engineering.

## Requirements

1. **Input Processing**: Accept stress-strain data via command line arguments specifying the number of data points, maximum stress, and maximum strain. Generate a realistic tensile curve with elastic and plastic regions.

2. **Elastic Modulus Calculation**: Calculate Young's modulus (elastic modulus) from the linear portion of the stress-strain curve (typically the first 20-30% of the curve before yielding).

3. **Yield Strength Determination**: Determine the 0.2% offset yield strength by finding where a line parallel to the elastic region but offset by 0.002 strain intersects the stress-strain curve.

4. **Ultimate Tensile Strength**: Identify the maximum stress value in the curve, which represents the ultimate tensile strength (UTS).

5. **Curve Visualization**: Generate a matplotlib plot showing the stress-strain curve with key points marked (yield strength, UTS) and save it as a PNG file.

6. **Results Output**: Save all calculated properties to a JSON file containing elastic modulus, yield strength, ultimate tensile strength, and strain at failure.

The script should use argparse to handle command line arguments for the number of data points (default 1000), maximum stress (default 500 MPa), and maximum strain (default 0.25), plus output filenames for the plot and JSON results.

This tool would be useful for materials engineers to quickly analyze tensile test results and extract standardized mechanical properties for material characterization and comparison.
