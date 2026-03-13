Write a Python CLI script to analyze an earthquake catalog and identify aftershock sequences.

Input: A CSV file with columns:
- event_id, datetime, latitude, longitude, depth_km, magnitude, mag_type

Requirements:
1. Use argparse: --input CSV path, --output directory, --cluster-radius (default 50 km), --cluster-time (default 72 hours)
2. Compute the Gutenberg-Richter b-value using maximum-likelihood estimation (Aki formula): b = log10(e) / (mean_mag - completeness_mag + delta_bin/2), where completeness_mag is the magnitude of completeness estimated from the maximum of the magnitude-frequency histogram (bin width 0.1)
3. Identify aftershock sequences: for each event with magnitude >= 4.0, find subsequent events within --cluster-radius km and --cluster-time hours. Use Haversine formula for distance.
4. Compute magnitude-frequency statistics: count events per 0.1-magnitude bin
5. Output: catalog_stats.json (b_value, completeness_mag, largest_event {id, mag, lat, lon, depth}, total_events), aftershock_sequences.csv (mainshock_id, aftershock_id, distance_km, time_diff_hours, mag_diff), magnitude_freq.csv (mag_bin, count, cumulative_count, log10_cumulative)
6. Print summary: total events, b-value, number of identified sequences, largest event
