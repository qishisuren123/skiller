Write a Python CLI script to process CTD (Conductivity-Temperature-Depth) oceanographic profile data.

Input: A CSV file with columns: station_id, depth_m, temperature_C, salinity_PSU, dissolved_oxygen_mL_L.

Requirements:
1. Use argparse: --input CSV, --output directory, --depth-resolution (default 1.0 meter)
2. For each station:
   a. Interpolate all variables to regular depth grid (0 to max_depth at specified resolution)
   b. Compute potential density (sigma-t) using simplified UNESCO equation: sigma_t ≈ -0.093 + 0.808*S - 0.0016*S^2 + (-0.0069 + 0.0025*S)*T - 0.0001*T^2
   c. Find thermocline depth (depth of maximum dT/dz)
   d. Find mixed layer depth (depth where T differs from surface by > 0.5°C)
3. Output: interpolated_profiles.csv, station_summary.json
4. Print: number of stations, depth range, mean thermocline depth
