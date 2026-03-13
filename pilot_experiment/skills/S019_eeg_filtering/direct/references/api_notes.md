# scipy.signal - Digital Signal Processing
## Key Functions for EEG Analysis

# Filter Design
butter(N, Wn, btype='low', analog=False, output='ba', fs=None)
# N: filter order, Wn: critical frequencies (normalized 0-1 for analog=False)
# btype: 'low', 'high', 'band', 'bandstop'

iirnotch(w0, Q, fs)
# w0: frequency to remove, Q: quality factor, fs: sampling frequency

# Filter Application  
filtfilt(b, a, x, axis=-1, padtype='odd', padlen=None)
# Zero-phase filtering (forward-backward), no phase distortion

# Power Spectral Density
welch(x, fs=1.0, window='hann', nperseg=None, noverlap=None, nfft=None, 
      detrend='constant', return_onesided=True, scaling='density')
# nperseg: length of each segment (default: 256 for fs=1.0)
# noverlap: overlap between segments (default: nperseg//8)
# scaling: 'density' for V²/Hz, 'spectrum' for V²

# numpy integration
trapz(y, x=None, dx=1.0, axis=-1)
# Trapezoidal rule integration for power band calculations

# pandas data handling
read_csv(filepath, sep=',', header='infer', index_col=None, usecols=None, 
         dtype=None, na_values=None)
DataFrame.interpolate(method='linear', axis=0, limit=None, inplace=False)
