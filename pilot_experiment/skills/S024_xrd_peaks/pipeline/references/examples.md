# Background subtraction example
background, corrected = subtract_background(two_theta, intensity, window_size=50)

# Peak detection with adaptive thresholds
peaks, properties = detect_peaks(two_theta, corrected, min_height=50, prominence=30)

# Gaussian fitting with robust parameter estimation
fitted_peaks = fit_gaussian_peaks(two_theta, corrected, peaks)

# D-spacing calculation using Bragg's law
fitted_peaks = calculate_d_spacings(fitted_peaks, wavelength=1.5406)

# Pattern reconstruction
fitted_pattern = generate_fitted_pattern(two_theta, fitted_peaks, background)

# CLI usage examples
python xrd_analysis.py --input data.csv --output results/ --wavelength 1.5406
python xrd_analysis.py --input noisy_data.csv --output results/ --min-height 20 --prominence 50
