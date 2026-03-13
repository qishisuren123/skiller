# scipy.signal functions for peak analysis
from scipy.signal import find_peaks, peak_widths, savgol_filter

# find_peaks parameters:
# - height: minimum peak height
# - distance: minimum distance between peaks (in indices)
# - prominence: minimum prominence (peak height above surrounding baseline)
# - width: minimum peak width (in indices)

# peak_widths parameters:
# - rel_height: relative height at which to measure width (0.5 for FWHM)

# savgol_filter parameters:
# - window_length: must be odd, controls smoothing strength
# - polyorder: polynomial order for fitting, must be < window_length

# trapz for numerical integration:
# trapz(y, x) - integrates y over x using trapezoidal rule
