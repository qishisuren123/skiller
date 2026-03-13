Write a Python CLI script to analyze astronomical light curves and detect periodic variability.

Input: A CSV file with columns: time (days), magnitude, magnitude_error, filter_band.

Requirements:
1. Use argparse: --input CSV, --output JSON, --min-period (default 0.1 days), --max-period (default 100 days)
2. For each filter band separately:
   a. Compute Lomb-Scargle periodogram
   b. Find the dominant period and its significance (false alarm probability)
   c. Phase-fold the light curve at the best period
3. Output JSON: {filter: {best_period, significance, amplitude, mean_magnitude, n_points, phase_coverage}}
4. Print: detected periods per band, whether variability is significant (FAP < 0.01)
