# SciPy Functions Used
from scipy.signal import find_peaks
# find_peaks(data, height=None, prominence=None) - detects peaks with specified criteria

from scipy.ndimage import minimum_filter1d, gaussian_filter1d  
# minimum_filter1d(input, size, mode='nearest') - applies minimum filter for background estimation
# gaussian_filter1d(input, sigma) - applies Gaussian smoothing

from scipy.optimize import curve_fit
# curve_fit(func, xdata, ydata, p0=None, bounds=None, maxfev=800) - fits function to data

# NumPy Functions
np.radians() - converts degrees to radians
np.sin() - sine function for Bragg's law
np.maximum() - element-wise maximum (for ensuring non-negative values)
np.std() - standard deviation for noise estimation

# Pandas Functions  
pd.read_csv() - loads CSV data
pd.DataFrame() - creates structured data tables
df.to_csv() - saves data to CSV format
