# NumPy FFT Functions
np.fft.fft(x, axis=-1)  # Compute FFT along specified axis
np.fft.fftfreq(n, d=1.0)  # Return FFT sample frequencies

# SciPy DCT Function  
scipy.fft.dct(x, type=2, axis=-1, norm='ortho')  # Discrete Cosine Transform
# type=2: Most common DCT variant for MFCC
# norm='ortho': Orthogonal normalization

# NumPy Array Operations
np.linspace(start, stop, num)  # Evenly spaced numbers
np.column_stack([arr1, arr2])  # Stack 1D arrays as columns
np.diff(x, axis=-1)  # Calculate discrete differences
np.sign(x)  # Element-wise sign function

# Pandas DataFrame
pd.DataFrame(data)  # Create DataFrame from dict/list
df.to_csv(filename, index=False)  # Save to CSV without row indices

# File I/O
np.load(filename)  # Load NPZ file, returns dict-like object
json.dump(obj, file, indent=2)  # Save JSON with formatting
os.makedirs(path, exist_ok=True)  # Create directory if not exists
