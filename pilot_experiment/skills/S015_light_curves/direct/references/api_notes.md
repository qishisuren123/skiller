# scipy.signal.lombscargle
lombscargle(x, y, freqs, precenter=False, normalize=False)
# x: sample times, y: measurements, freqs: angular frequencies
# normalize=True gives normalized periodogram with exponential null hypothesis
# Returns: power spectral density at given frequencies

# Key parameters for astronomical periodograms:
# - Use angular frequencies: freqs = 2*pi*f_hz  
# - normalize=True for statistical significance testing
# - Frequency grid: typically 5-10x oversampled

# numpy statistical functions:
np.mean(array)           # Mean magnitude
np.max(array) - np.min(array)  # Peak-to-peak amplitude  
np.histogram(data, bins) # Phase coverage analysis

# pandas DataFrame operations:
df.groupby('column')     # Group by filter band
df['column'].unique()    # Get unique filter values
df[df['col'] == value]   # Filter rows by condition
