# Ocean Wave Frequency Spectrum Analysis

Create a CLI script that processes synthetic ocean buoy data to compute and analyze wave frequency spectra. Ocean buoys measure sea surface elevation over time, and the frequency spectrum reveals the energy distribution across different wave frequencies, which is crucial for understanding wave conditions and predicting wave behavior.

Your script should accept time series data of sea surface elevation measurements and compute the power spectral density using appropriate windowing and filtering techniques. The analysis should identify dominant wave frequencies, calculate significant wave height, and export results in multiple formats.

## Requirements

1. **Data Processing**: Read synthetic buoy data containing timestamps and sea surface elevation measurements. Handle data gaps and apply appropriate detrending to remove low-frequency drift.

2. **Spectrum Computation**: Calculate the power spectral density using Welch's method with Hanning windowing. Apply appropriate frequency binning and normalize the spectrum to units of m²/Hz.

3. **Wave Parameters**: Extract key wave statistics including significant wave height (Hs), peak frequency (fp), mean frequency, and spectral bandwidth. Identify the dominant frequency band containing maximum energy.

4. **Quality Control**: Implement basic quality checks including detection of unrealistic elevation values, identification of data gaps longer than 10% of the record, and flagging of spectra with insufficient energy in the wave frequency band (0.05-0.5 Hz).

5. **Visualization**: Generate a publication-quality plot showing the frequency spectrum with logarithmic scaling, marked peak frequency, and annotated wave parameters.

6. **Output Export**: Save results as both a JSON summary file containing all computed parameters and a CSV file with the complete frequency spectrum data (frequency, power spectral density, and cumulative energy).

Use argparse to handle command-line arguments for input parameters, output directory, and analysis options.
