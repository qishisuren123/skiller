# scipy.signal.find_peaks
find_peaks(x, height=None, threshold=None, distance=None, prominence=None, width=None, wlen=None, rel_height=0.5, plateau_size=None)
- height: minimum peak height threshold
- distance: minimum distance between peaks in samples
- Returns: (peaks, properties) where peaks are indices

# scipy.signal.peak_widths  
peak_widths(x, peaks, rel_height=0.5, prominence_data=None, wlen=None)
- rel_height: relative height at which width is measured (0.5 = FWHM)
- Returns: (widths, width_heights, left_ips, right_ips)
- widths: peak widths in samples
- left_ips, right_ips: interpolated left and right intersection points

# numpy.trapz
trapz(y, x=None, dx=1.0, axis=-1)
- Integrate using trapezoidal rule
- y: values to integrate
- x: sample points corresponding to y values
