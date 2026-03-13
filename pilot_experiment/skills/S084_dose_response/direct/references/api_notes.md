# scipy.optimize.curve_fit
curve_fit(f, xdata, ydata, p0=None, bounds=(-inf, inf), maxfev=None)
# f: callable function to fit
# p0: initial parameter estimates (array-like)
# bounds: tuple of (lower_bounds, upper_bounds) arrays
# Returns: popt (optimal parameters), pcov (covariance matrix)

# numpy.log10 / numpy.logspace
np.log10(x)  # Base-10 logarithm
np.logspace(start, stop, num)  # Log-spaced array from 10^start to 10^stop

# matplotlib.pyplot log scaling
plt.xscale('log')  # Set x-axis to logarithmic scale
plt.axvline(x=value, color='color', linestyle='--')  # Vertical reference line

# pandas data validation
df[(df['col'] > 0) & (df['col'] < 100) & pd.notna(df['col'])]  # Boolean indexing
