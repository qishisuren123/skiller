Write a Python CLI script to analyze radiosonde atmospheric sounding profile data.

Input: A CSV file with columns: pressure (hPa), temperature (°C), dewpoint (°C), wind_speed (m/s), wind_direction (degrees), altitude (m).

Requirements:
1. Use argparse: --input CSV path, --output directory
2. Compute environmental lapse rate between consecutive levels (°C/km). Use formula: lapse_rate = -(T2 - T1) / ((alt2 - alt1) / 1000)
3. Find the tropopause: the lowest level above 5 km altitude where the lapse rate drops below 2 °C/km for at least 2 km depth
4. Compute approximate CAPE (Convective Available Potential Energy, J/kg) using a simple parcel method:
   - Lift a surface parcel dry-adiabatically (9.8 °C/km) until it reaches saturation (temperature == dewpoint)
   - Then lift moist-adiabatically (6.0 °C/km approximation) above the LCL
   - CAPE = sum of g * (T_parcel - T_env) / T_env * dz for layers where T_parcel > T_env (positive buoyancy)
   - CIN = sum of g * (T_parcel - T_env) / T_env * dz for layers where T_parcel < T_env below the LFC (negative buoyancy)
5. Detect temperature inversions: layers where temperature increases with altitude
6. Output: processed_profile.csv (original data + lapse_rate column) and summary.json containing:
   - tropopause_height_m, tropopause_pressure_hPa, CAPE_J_kg, CIN_J_kg
   - inversions: list of {base_altitude_m, top_altitude_m, strength_C}
   - surface_temperature_C, surface_dewpoint_C
7. Print summary: tropopause height, CAPE, CIN, number of inversions
