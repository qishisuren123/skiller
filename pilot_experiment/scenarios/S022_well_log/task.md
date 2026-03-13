Write a Python CLI script to resample borehole well log data and classify lithology from crossplot rules.

Input: A CSV file with columns: depth, gamma_ray, resistivity, neutron_porosity, bulk_density, caliper.
- Depth is in meters (irregularly sampled).
- gamma_ray in API units, resistivity in ohm-m, neutron_porosity as fraction (0-1), bulk_density in g/cm3, caliper in inches.

Requirements:
1. Use argparse: --input CSV, --output directory, --depth-step (default 0.5 meters)
2. Resample all log curves to uniform depth intervals using linear interpolation (from min to max depth at --depth-step resolution)
3. Compute derived logs:
   - PHIT (total porosity) = (2.65 - bulk_density) / (2.65 - 1.0)  [matrix=2.65, fluid=1.0]
   - Vsh (shale volume) from gamma ray: Vsh = (GR - GR_min) / (GR_max - GR_min), clipped to [0, 1]
4. Classify lithology for each depth sample using these crossplot rules:
   - "sandstone": Vsh < 0.3 AND PHIT > 0.1 AND resistivity > 10
   - "shale": Vsh >= 0.6
   - "limestone": bulk_density > 2.5 AND neutron_porosity < 0.15 AND Vsh < 0.3
   - "siltstone": otherwise
5. Output:
   - resampled_log.csv: all original columns + PHIT + Vsh at uniform depth
   - lithology_classification.csv: depth, lithology columns
   - summary.json: {total_depth_range, n_samples, layer_counts: {sandstone: N, shale: N, ...}, mean_porosity, mean_Vsh}
6. Print: depth range, number of resampled points, lithology distribution
