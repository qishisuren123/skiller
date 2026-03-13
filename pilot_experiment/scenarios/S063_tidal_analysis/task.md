# Tidal Harmonic Analysis Tool

Create a command-line tool that performs basic harmonic analysis on synthetic tidal height data to identify dominant tidal constituents and their characteristics.

Your script should accept the following arguments:
- `--duration`: Duration of tidal record in days (integer)
- `--sampling_interval`: Sampling interval in hours (float)
- `--output_harmonics`: Path to save harmonic analysis results as JSON
- `--output_plot`: Path to save time series plot as PNG
- `--min_amplitude`: Minimum amplitude threshold for reporting constituents (float, in meters)

## Requirements

1. **Generate synthetic tidal data**: Create a time series of tidal heights using the specified duration and sampling interval. The data should include at least M2 (12.42h), S2 (12h), and O1 (25.82h) tidal constituents with realistic amplitudes and random phases, plus Gaussian noise.

2. **Perform harmonic analysis**: Use Fourier analysis to identify the dominant tidal frequencies in the generated data. Calculate amplitude and phase for each significant frequency component.

3. **Identify tidal constituents**: Match the detected frequencies to known tidal constituents (M2, S2, O1, K1, N2) within a reasonable tolerance. Report constituent name, period, amplitude, and phase.

4. **Apply amplitude filtering**: Only include constituents in the output that have amplitudes greater than or equal to the specified minimum amplitude threshold.

5. **Save results**: Export the identified constituents and their properties to a JSON file with keys: "constituent", "period_hours", "amplitude_m", "phase_degrees".

6. **Generate visualization**: Create a time series plot showing the original tidal data and save it as a PNG file. Include proper axis labels and title.

The tool should handle typical tidal analysis scenarios with sampling intervals from 0.1 to 2 hours and durations from 1 to 30 days.
