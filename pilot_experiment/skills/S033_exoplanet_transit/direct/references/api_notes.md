# NumPy - Array operations and statistics
np.linspace(start, stop, num)  # Create evenly spaced time grid
np.random.normal(loc, scale, size)  # Generate Gaussian noise
np.median(array)  # Robust central tendency
np.abs(array)  # Element-wise absolute value
np.concatenate([array1, array2])  # Join arrays
np.argmax(array)  # Index of maximum value

# SciPy Optimization
from scipy.optimize import minimize
minimize(func, x0, args=(), bounds=None, method='L-BFGS-B')
# Returns OptimizeResult with .x (parameters), .fun (objective), .success

# Matplotlib - Astronomical plotting
plt.subplots(nrows, ncols, figsize=(w,h), gridspec_kw={})
ax.plot(x, y, 'b.', markersize=3, alpha=0.5)  # Scatter plot
ax.axhline(y, color='k', linestyle='--')  # Horizontal reference line
plt.tight_layout()  # Adjust subplot spacing
plt.savefig(path, dpi=150, bbox_inches='tight')

# JSON - Results serialization  
json.dump(data, file, indent=2)  # Pretty-print JSON output
# Note: Convert numpy types to Python types with float() for JSON compatibility
