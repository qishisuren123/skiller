Write a Python CLI script to detect and analyze peaks in UV-Vis absorption spectroscopy data.

Input: A CSV file with columns: wavelength (nm), absorbance. May contain multiple samples as additional columns (sample_1, sample_2, ...).

Requirements:
1. Use argparse: --input CSV, --output JSON, --min-height (default 0.1), --min-distance (default 10 nm)
2. For each sample, detect absorption peaks using prominence-based detection
3. For each peak: record wavelength, height, width at half maximum (FWHM), area (by integration)
4. Identify the dominant peak (highest absorbance) for each sample
5. Output JSON: {sample_name: {peaks: [{wavelength, height, fwhm, area}], dominant_peak, n_peaks}}
6. Print summary: number of peaks per sample, wavelength range of dominant peaks
