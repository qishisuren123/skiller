1. Prepare input CSV file with required columns: depth, gamma_ray, resistivity, neutron_porosity, bulk_density, caliper
2. Run the script: `python scripts/main.py --input data.csv --output results/ --depth-step 0.5`
3. Script loads and validates input data, checking for missing required columns
4. Data is resampled to uniform depth intervals using linear interpolation via numpy.interp
5. Matrix density is automatically estimated using 95th percentile of bulk density values plus 0.05 g/cm3 buffer
6. PHIT (total porosity) is calculated using: (matrix_density - bulk_density) / (matrix_density - fluid_density)
7. Vsh (shale volume) is computed from gamma ray normalization between min/max values
8. Lithology classification applies crossplot rules based on Vsh, PHIT, resistivity, bulk density, and neutron porosity
9. Three output files are generated: resampled_log.csv, lithology_classification.csv, and summary.json
10. Summary statistics include depth range, sample count, lithology distribution, and mean petrophysical properties
