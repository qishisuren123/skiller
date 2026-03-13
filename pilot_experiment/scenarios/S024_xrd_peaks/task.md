Write a Python CLI script to analyze X-ray diffraction (XRD) patterns: subtract background, detect peaks, fit Gaussians, and compute d-spacings.

Input: A CSV file with columns: two_theta (degrees), intensity (counts).

Requirements:
1. Use argparse: --input CSV, --output directory, --wavelength (default 1.5406 Angstroms for Cu K-alpha), --min-height (default 50 counts), --prominence (default 30)
2. Background subtraction:
   - Estimate background using a rolling minimum with large window (e.g., 50 points), then smooth it
   - Subtract background from raw intensity
3. Peak detection:
   - Use scipy.signal.find_peaks with height and prominence thresholds on background-subtracted data
4. Gaussian peak fitting:
   - For each detected peak, fit a Gaussian: I(x) = A * exp(-(x - mu)^2 / (2*sigma^2))
   - Extract: peak position (mu), intensity (A), FWHM = 2*sqrt(2*ln(2))*sigma ≈ 2.3548*sigma
5. d-spacing calculation via Bragg's law:
   - d = wavelength / (2 * sin(theta)), where theta = two_theta_peak / 2 in radians
6. Output:
   - peaks.csv: columns peak_id, two_theta, intensity, fwhm, d_spacing
   - fitted_pattern.csv: columns two_theta, raw_intensity, background, corrected_intensity, fitted_intensity
   - summary.json: {n_peaks, wavelength, strongest_peak: {two_theta, d_spacing, intensity}, peaks: [...]}
7. Print: number of peaks found, strongest peak position and d-spacing
