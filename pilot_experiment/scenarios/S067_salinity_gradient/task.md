# Estuarine Salinity Gradient Analysis from CTD Transects

Create a CLI script that analyzes salinity gradients in estuarine environments using Conductivity-Temperature-Depth (CTD) transect data. The script should identify mixing zones, calculate stratification indices, and detect haloclines across multiple transect lines.

Your script should accept CTD transect data containing station positions, depths, temperature, salinity, and conductivity measurements. The analysis must account for tidal influences and spatial variability typical of estuarine systems.

## Requirements

1. **Halocline Detection**: Identify halocline layers where salinity gradient exceeds 0.5 PSU/m over a minimum 2-meter depth range. Output the depth range, maximum gradient strength, and geographic position for each detected halocline.

2. **Stratification Analysis**: Calculate the Simpson's Stratification Parameter (Φ) for each station using the formula Φ = (g/ρ₀) ∫(ρ-ρ_surface)z dz from surface to bottom, where g=9.81 m/s², ρ₀=1025 kg/m³. Classify stations as well-mixed (Φ<10), partially mixed (10≤Φ<50), or stratified (Φ≥50).

3. **Salt Wedge Mapping**: Detect estuarine salt wedge intrusion by identifying the 2 PSU isohaline position along each transect. Calculate the salt wedge penetration distance from the river mouth and maximum intrusion depth.

4. **Tidal Mixing Efficiency**: Compute the mixing efficiency parameter η = Ri/(Ri+0.2) where Ri is the Richardson number (Ri = N²/S², N² is buoyancy frequency, S² is shear squared). Identify regions where η<0.15 indicating active turbulent mixing.

5. **Cross-Transect Interpolation**: Generate a 2D salinity field using optimal interpolation with a decorrelation length scale of 500m horizontally and 5m vertically. Output interpolated values on a regular 50m×0.5m grid.

6. **Quality Control**: Flag and report suspicious data points where salinity changes >2 PSU between adjacent depth measurements or where density inversions exceed 0.1 kg/m³.

## Arguments
- `--input`: Input data format (JSON with station arrays)
- `--output-dir`: Directory for output files
- `--transect-id`: Transect identifier for file naming
- `--river-mouth-lat`: River mouth latitude for distance calculations
- `--river-mouth-lon`: River mouth longitude for distance calculations

## Outputs
- `haloclines.json`: Detected halocline characteristics
- `stratification.json`: Station stratification parameters
- `salt_wedge.json`: Salt wedge intrusion metrics  
- `mixing_zones.json`: Tidal mixing efficiency results
- `interpolated_field.h5`: 2D interpolated salinity field
- `quality_flags.json`: Data quality assessment results
