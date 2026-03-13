# NumPy - Core array operations
np.load(file)                    # Load .npy audio file
np.correlate(a, v, mode='full')  # Calculate autocorrelation
np.argmax(array)                 # Find index of maximum value
np.clip(array, min, max)         # Clamp values to range
np.mean(array**2)                # Calculate signal power

# SciPy Signal Processing
from scipy.signal import find_peaks
find_peaks(data, prominence=0.1, distance=20)  # Detect autocorrelation peaks

# Matplotlib - Visualization
plt.subplots(rows, cols, figsize=(w, h))  # Create subplot grid
plt.specgram(signal, Fs=sample_rate)      # Generate spectrogram
plt.axvline(x=value, color='r')           # Add vertical reference line

# JSON - Report generation
json.dump(data, file, indent=2)           # Save structured report

# Key DSP Formulas
# ERLE = 10 * log10(echo_power_before / echo_power_after)
# SER = 10 * log10(signal_power / echo_power)
# Autocorrelation normalization: autocorr / autocorr[0]
