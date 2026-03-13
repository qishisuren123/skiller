# NumPy Functions for Grain Size Analysis
numpy.percentile(a, q, method='linear')
  - Calculate percentiles for D-value determination
  - method='linear' ensures consistent interpolation for materials standards

numpy.mean(a), numpy.median(a), numpy.std(a, ddof=1)
  - Basic statistical measures
  - ddof=1 for sample standard deviation in materials characterization

# Matplotlib for Materials Science Visualization
matplotlib.pyplot.hist(x, bins, alpha, edgecolor)
  - bins: Use Freedman-Diaconis rule for grain size data
  - alpha=0.7, edgecolor='black' for publication-quality plots

matplotlib.pyplot.axvline(x, color, linestyle, label)
  - Add statistical reference lines (mean, percentiles)
  - Essential for materials characterization plots

# Data Validation Patterns
np.any(condition) - Check for invalid measurements
np.sum(boolean_mask) - Count grains in size categories
len(array) - Total grain count for percentage calculations
