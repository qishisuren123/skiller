1. Prepare earthquake catalog CSV file with required columns: event_id, datetime, latitude, longitude, depth_km, magnitude, mag_type
2. Run the analysis script: `python scripts/main.py --input catalog.csv --output results/`
3. Optional: Adjust clustering parameters with --cluster-radius (km) and --cluster-time (hours)
4. Script loads and validates the earthquake data, sorting by datetime
5. Calculates magnitude completeness using histogram peak method
6. Computes Gutenberg-Richter b-value using Aki formula with error handling
7. Identifies aftershock sequences using optimized spatiotemporal clustering
8. Generates magnitude-frequency distribution statistics
9. Exports results to three files: catalog_stats.json, aftershock_sequences.csv, magnitude_freq.csv
10. Review outputs for seismological analysis and interpretation
