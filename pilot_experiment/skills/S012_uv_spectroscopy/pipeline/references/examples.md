# Basic peak detection
peaks, properties = find_peaks(absorbance, height=0.1, distance=5, prominence=0.01)

# Peak width calculation
widths, width_heights, left_ips, right_ips = peak_widths(absorbance, peaks, rel_height=0.5)

# Savitzky-Golay smoothing
smoothed = savgol_filter(absorbance, window_length=5, polyorder=2)

# Baseline correction and integration
baseline = np.linspace(abs_left, abs_right, len(peak_region))
corrected = peak_region - baseline
area = trapz(corrected, wavelength_region)

# Adaptive prominence based on noise
noise_level = np.std(np.diff(absorbance))
min_prominence = max(0.01, noise_level * 3)

# Column detection for various naming conventions
sample_columns = [col for col in df.columns if col.lower() != 'wavelength']
