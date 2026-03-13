# Quasar Variability Analysis Tool

Create a CLI script that analyzes optical variability in quasar light curves from survey data. Quasars are highly variable astronomical objects, and characterizing their variability is crucial for understanding their physical properties and identifying them in large surveys.

Your script should accept synthetic photometric time series data and compute various variability metrics commonly used in astronomy. The input data represents observations of multiple quasars over time in different optical bands.

## Requirements

1. **Data Input**: Accept a CSV file path containing columns: `object_id`, `mjd` (Modified Julian Date), `band` (g, r, i), `magnitude`, and `mag_error`. Generate synthetic data if no input file is provided.

2. **Variability Metrics**: For each object and band, calculate:
   - Standard deviation of magnitudes
   - Excess variance (accounting for measurement errors)
   - Structure function at 30-day lag
   - Amplitude of variability (90th percentile - 10th percentile)

3. **Classification**: Classify objects as "variable" or "non-variable" based on excess variance > 0.05 mag² threshold. Output the classification for each object-band combination.

4. **Statistical Summary**: Generate summary statistics including the fraction of variable objects per band and median variability metrics for variable vs non-variable populations.

5. **Output Files**: Save results to JSON format containing per-object metrics and a separate summary statistics file. Include light curve plots for the top 3 most variable objects.

6. **Filtering**: Apply quality cuts by excluding measurements with magnitude errors > 0.2 mag and requiring minimum 20 observations per object-band combination for reliable variability analysis.

Use argparse for command-line interface with options for input file, output directory, and variability threshold.
