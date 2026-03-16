1. Prepare ADCP data files in CSV format with headers for U, V, W velocities, correlations, echo intensity, and depths
2. Run the main script with required input file arguments: python scripts/main.py --u_data u_vel.csv --v_data v_vel.csv --w_data w_vel.csv --correlations corr.csv --echo_intensity echo.csv --depths depths.csv
3. The script loads CSV data using pandas with comprehensive NaN value handling for various text representations
4. Phase-space spike detection algorithm identifies velocity outliers using gradient analysis and statistical thresholds
5. Correlation filtering removes measurements below beam correlation quality thresholds
6. Echo intensity analysis flags weak acoustic returns using median filtering
7. Vertical shear validation checks for unrealistic velocity gradients between depth bins
8. All quality control flags are combined to create final data mask
9. Oceanographic statistics are computed from quality-controlled velocity data
10. Results are saved as JSON with proper NaN to null conversion for valid format
11. Velocity profile plots are generated showing original vs QC'd data with quality flags
12. Processing logs provide status updates and final data quality percentage
