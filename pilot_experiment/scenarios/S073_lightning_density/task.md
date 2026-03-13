# Lightning Flash Density Analysis

Create a CLI script that processes lightning stroke data to generate flash density maps and statistical summaries for atmospheric research.

Lightning detection networks record individual strokes, but researchers need to group these into flashes (multiple strokes from the same discharge) and compute spatial density maps for weather analysis and risk assessment.

## Requirements

Your script should accept the following arguments:
- `--input-data`: Path to save synthetic stroke data (CSV format)
- `--output-density`: Path to save the density map (HDF5 format)
- `--output-stats`: Path to save statistical summary (JSON format)
- `--grid-resolution`: Grid cell size in kilometers (default: 5.0)
- `--time-window`: Time window in milliseconds for grouping strokes into flashes (default: 500)
- `--distance-threshold`: Maximum distance in kilometers between strokes in the same flash (default: 10.0)

The script must:

1. **Generate synthetic lightning stroke data** with columns: timestamp (milliseconds), latitude, longitude, peak_current (kA), and stroke_id. Create 1000-5000 strokes distributed across a 200x200 km area with realistic clustering patterns.

2. **Group strokes into flashes** by identifying strokes that occur within the specified time window and distance threshold. Assign a unique flash_id to each group and save the enhanced dataset.

3. **Create a spatial density grid** covering the data extent with the specified resolution. Count the number of flashes per grid cell and compute flash density as flashes per km² per year (assume data represents one storm season = 0.25 years).

4. **Calculate statistical metrics** including total flashes, mean/max density, peak current statistics (mean, std, max), and the coordinates of the highest density grid cell.

5. **Save the density map** as an HDF5 file with datasets for latitude/longitude coordinates, flash counts, and density values, plus metadata attributes.

6. **Export summary statistics** as a JSON file containing all computed metrics, grid parameters, and processing timestamp.

The output should enable researchers to visualize lightning activity patterns and identify high-risk areas for further analysis.
