# NumPy - Array operations and angle handling
np.random.normal(mean, std)  # Generate normally distributed angles
np.column_stack([array1, array2])  # Combine phi/psi for analysis
((angle + 180) % 360) - 180  # Normalize angles to [-180, 180]

# SciPy - Statistical analysis
from scipy.stats import gaussian_kde
kde = gaussian_kde(data.T)  # Create kernel density estimator
densities = kde(data.T)  # Evaluate density at data points

# Matplotlib - Plotting
plt.scatter(x, y, c=colors, cmap='viridis', alpha=0.6)  # Density-colored scatter
plt.colorbar(scatter, ax=ax)  # Add density colorbar
ax.set_xlim(-180, 180)  # Set angle range for both axes
plt.savefig(filename, dpi=300, bbox_inches='tight')  # High-quality output

# JSON - Data export
json.dump(data, file, indent=2)  # Pretty-printed JSON output
array.tolist()  # Convert numpy arrays for JSON serialization

# Pathlib - File handling
Path(filename).parent.mkdir(parents=True, exist_ok=True)  # Create directories
