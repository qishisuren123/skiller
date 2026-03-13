# ADCP Velocity Profile Quality Control and Analysis

Create a CLI script that processes Acoustic Doppler Current Profiler (ADCP) velocity data to identify and remove bad measurements, then compute oceanographic statistics.

ADCP instruments measure water velocity profiles by analyzing Doppler shifts in acoustic signals reflected by particles in the water column. Raw data often contains outliers, beam correlation issues, and velocity spikes that must be filtered before analysis.

Your script should accept velocity components (u, v, w), echo intensities, correlation values, and depth bins as input parameters, then apply sophisticated quality control algorithms.

## Requirements

1. **Velocity Spike Detection**: Implement a phase-space method to detect velocity spikes by analyzing the relationship between velocity and its first derivative. Flag measurements where the phase-space radius exceeds 2 standard deviations from the mean.

2. **Correlation Filtering**: Remove velocity measurements where any beam correlation falls below a threshold (default 70%). Apply this filter independently to each depth bin and velocity component.

3. **Echo Intensity Analysis**: Flag depth bins where echo intensity drops below background noise levels, indicating weak acoustic returns. Use a sliding window approach to identify regions with consistently low signal strength.

4. **Vertical Shear Validation**: Calculate velocity shear (du/dz, dv/dz) and flag profiles with unrealistic shear values exceeding typical oceanic limits (>0.1 s⁻¹). Apply median filtering to smooth shear estimates.

5. **Statistical Summary**: Compute depth-averaged currents, maximum velocities, shear statistics, and data quality percentages. Output results as structured JSON with uncertainty estimates.

6. **Profile Visualization**: Generate a comprehensive plot showing original vs. quality-controlled velocity profiles, correlation values, and flagged data points with depth.

Use argparse for command-line interface with options for QC thresholds, output files, and processing parameters.
