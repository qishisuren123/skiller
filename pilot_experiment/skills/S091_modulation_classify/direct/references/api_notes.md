# Key Libraries for Digital Modulation Classification

## h5py - HDF5 File Handling
- `h5py.File(filename, 'r')`: Open HDF5 file for reading
- `file.keys()`: Get dataset names in HDF5 file
- `file[dataset_name][:]`: Read entire dataset as numpy array

## numpy - Signal Processing
- `np.abs(complex_array)`: Compute instantaneous amplitude
- `np.angle(complex_array)`: Compute instantaneous phase
- `np.unwrap(phase)`: Remove phase discontinuities
- `np.fft.fft(signal)`: Compute Fast Fourier Transform
- `np.var(array)`: Compute variance for feature extraction

## scipy.stats - Statistical Features
- `stats.kurtosis(data)`: Compute kurtosis (4th moment)
- `stats.skew(data)`: Compute skewness (3rd moment)
- Used for higher-order moment analysis of constellation points

## sklearn - Machine Learning Classification
- `RandomForestClassifier`: Robust classifier for modulation recognition
- `cross_val_score()`: K-fold cross-validation for performance estimation
- `confusion_matrix()`: Generate confusion matrix for multi-class evaluation
- `classification_report()`: Detailed precision/recall/F1 metrics

## matplotlib.pyplot - Constellation Visualization
- `plt.scatter(I, Q)`: Create constellation diagram scatter plot
- `plt.axis('equal')`: Ensure equal scaling for I/Q axes
- Essential for visual verification of modulation schemes
