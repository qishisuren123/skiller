# scipy.signal.lombscargle
lombscargle(x, y, freqs, precenter=False, normalize=False)
# x: sample times (array)
# y: measurement values (array) 
# freqs: angular frequencies (array) - use 2*pi*frequency
# normalize: True for normalized periodogram
# Returns: power spectral density array

# Key frequency relationships
omega = 2 * np.pi * frequency  # Convert to angular frequency
period = 2 * np.pi / omega     # Convert back to period
min_freq = 1.0 / max_period    # Frequency limits
max_freq = 1.0 / min_period

# False alarm probability calculation
N_eff = N_frequencies * 2.0 / N_datapoints  # Effective independent frequencies
fap = 1.0 - (1.0 - np.exp(-power_max))**N_eff  # Exponential distribution
