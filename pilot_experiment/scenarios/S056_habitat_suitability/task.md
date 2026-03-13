# Habitat Suitability Index Calculator

Create a CLI script that calculates habitat suitability indices for species based on multiple environmental variables. The script should process synthetic environmental data layers and generate suitability maps using weighted scoring functions.

Your script should accept the following arguments:
- `--output` or `-o`: Output directory for results
- `--species` or `-s`: Target species name (string)
- `--weights` or `-w`: Comma-separated weights for environmental factors (4 values)
- `--temp_range` or `-t`: Optimal temperature range as "min,max" (default: "15,25")
- `--precip_min` or `-p`: Minimum precipitation threshold in mm (default: 500)

## Requirements:

1. **Generate synthetic environmental data**: Create four 50x50 grids representing temperature (°C), precipitation (mm), elevation (m), and vegetation density (0-1). Use realistic value ranges and spatial patterns.

2. **Calculate individual suitability scores**: For each environmental layer, compute suitability scores (0-1) based on species preferences:
   - Temperature: Gaussian curve centered on optimal range
   - Precipitation: Linear increase above minimum threshold, capped at 1.0
   - Elevation: Inverse relationship (higher elevation = lower suitability)
   - Vegetation: Direct linear relationship

3. **Compute weighted habitat suitability index (HSI)**: Combine individual scores using provided weights (must sum to 1.0). Create a final HSI grid with values 0-1.

4. **Generate summary statistics**: Calculate and save statistics including mean HSI, percentage of highly suitable habitat (HSI > 0.7), and optimal locations (top 5 grid coordinates).

5. **Export results**: Save the HSI grid as a CSV file named `{species}_hsi.csv` and summary statistics as `{species}_summary.json`.

6. **Create visualization**: Generate a matplotlib heatmap of the HSI with appropriate colormap and save as `{species}_hsi_map.png`.

The script should validate that weights sum to 1.0 and handle edge cases appropriately.
