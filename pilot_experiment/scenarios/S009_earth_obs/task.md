Write a Python CLI script to merge and align multiple Earth observation station CSV files into a single dataset.

Input: A directory containing CSV files, each from a different weather station. Each CSV has columns: timestamp (ISO format), temperature, humidity, pressure, station_id.

Requirements:
1. Use argparse: --input-dir directory, --output CSV, --freq (default "1h" for hourly)
2. Read all CSV files from the directory
3. Align all stations to a common time grid (resample to specified frequency)
4. Handle missing values: forward-fill then backward-fill (limit=3)
5. Output merged CSV: timestamp as index, one column per station per variable (e.g., station_A_temperature)
6. Print summary: number of stations, time range, missing data percentage
