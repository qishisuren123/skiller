2024-01-15 10:30:15,123 - INFO - Generating 24h of synthetic data with 1min resolution
2024-01-15 10:30:15,145 - INFO - Detecting flare events...
2024-01-15 10:30:15,167 - INFO - Saving results to flare_results.json
2024-01-15 10:30:15,189 - INFO - Generating plot: flare_lightcurve.png
2024-01-15 10:30:15,234 - INFO - Analysis complete. Detected 4 flares.
2024-01-15 10:30:15,234 - INFO - Class M flare: Peak at 167.0 min, Duration: 44.0 min
2024-01-15 10:30:15,234 - INFO - Class C flare: Peak at 456.0 min, Duration: 23.0 min
2024-01-15 10:30:15,234 - INFO - Class X flare: Peak at 789.0 min, Duration: 67.0 min
2024-01-15 10:30:15,234 - INFO - Class C flare: Peak at 1123.0 min, Duration: 18.0 min

JSON Output (flare_results.json):
[
  {
    "start_time": 145.0,
    "peak_time": 167.0,
    "end_time": 189.0,
    "peak_flux": 1.5e-05,
    "duration": 44.0,
    "classification": "M"
  },
  {
    "start_time": 434.0,
    "peak_time": 456.0,
    "end_time": 457.0,
    "peak_flux": 5.2e-06,
    "duration": 23.0,
    "classification": "C"
  }
]
