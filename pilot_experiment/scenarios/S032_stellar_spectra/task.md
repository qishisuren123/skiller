# Stellar Spectra Classification and Normalization

Create a command-line tool that processes synthetic stellar spectra data to perform normalization and spectral type classification. Your script should handle multiple stellar spectra simultaneously and output both normalized spectra and classification results.

## Requirements

1. **Data Processing**: Accept wavelength ranges and generate synthetic stellar spectra with realistic absorption features characteristic of different spectral types (O, B, A, F, G, K, M). Each spectrum should contain noise and multiple absorption lines at wavelengths typical for stellar classification (hydrogen Balmer series, calcium H&K lines, etc.).

2. **Continuum Normalization**: Implement a robust continuum normalization algorithm that fits a polynomial baseline to the spectrum while avoiding absorption lines. The algorithm should automatically identify continuum regions and fit an appropriate polynomial order (typically 3-5) to normalize flux values to unity in line-free regions.

3. **Feature Extraction**: Extract key spectral features used in stellar classification including equivalent widths of major absorption lines (Hα, Hβ, Ca II H&K, Mg I), line depth ratios, and continuum slope measurements. Calculate uncertainties for each measurement based on local noise levels.

4. **Spectral Classification**: Implement a classification algorithm that assigns spectral types (O, B, A, F, G, K, M) based on extracted features. Use a combination of line strength ratios and temperature-sensitive features. The classifier should output both the most likely spectral type and a confidence score.

5. **Quality Assessment**: Perform quality checks on input spectra including signal-to-noise ratio estimation, wavelength coverage validation, and identification of problematic regions (cosmic rays, telluric contamination). Flag spectra that don't meet minimum quality thresholds.

6. **Output Generation**: Save results in multiple formats: normalized spectra as HDF5 files, classification results as JSON with confidence scores and feature measurements, and generate diagnostic plots showing the normalization process and key spectral features for each input spectrum.

The tool should be robust to varying input data quality and provide meaningful error messages for problematic cases.
