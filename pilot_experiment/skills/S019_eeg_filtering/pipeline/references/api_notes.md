# SciPy Signal Processing
signal.butter(order, [low, high], btype='band')  # Butterworth bandpass filter
signal.iirnotch(freq, Q)  # Notch filter for power line interference
signal.filtfilt(b, a, data)  # Zero-phase filtering (requires min length)
signal.welch(data, fs, nperseg, noverlap, detrend)  # Power spectral density

# Pandas Data Validation
pd.api.types.is_numeric_dtype(series)  # Check if column is numeric
data.columns  # Get column names
data[col].max(), data[col].min()  # Get value ranges

# NumPy Type Checking
isinstance(obj, np.floating)  # Check for numpy float types
isinstance(obj, np.integer)  # Check for numpy integer types
isinstance(obj, np.ndarray)  # Check for numpy arrays

# File Operations
Path(filename).exists()  # Check file existence
Path(directory).mkdir(parents=True, exist_ok=True)  # Create directories
