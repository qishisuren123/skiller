# NumPy - Core numerical operations
np.corrcoef(x, y)  # Correlation coefficient matrix
np.sign(x)  # Element-wise sign function
np.unique(arr, return_counts=True)  # Unique values and counts
np.isnan(arr)  # Test for NaN values
np.var(arr)  # Variance calculation
np.median(arr)  # Median value

# Pandas - Data manipulation
pd.read_csv(filepath)  # Load CSV data
df.interpolate(method='linear', limit=n)  # Interpolate missing values
df.quantile(q)  # Calculate quantiles
df.sort_values(column)  # Sort by column values
df.iloc[start:end]  # Integer-location based indexing

# SciPy Stats - Statistical functions
stats.norm.cdf(x)  # Cumulative distribution function
stats.pearsonr(x, y)  # Pearson correlation coefficient
stats.spearmanr(x, y)  # Spearman rank correlation
curve_fit(func, xdata, ydata, p0)  # Non-linear least squares fitting

# Matplotlib - Plotting
plt.subplots(nrows, ncols, figsize)  # Create subplot grid
ax.scatter(x, y, alpha, s)  # Scatter plot
ax.axvline(x, color, linestyle, alpha)  # Vertical line
ax.imshow(data, cmap, aspect, vmin, vmax)  # Display image/heatmap
plt.colorbar(mappable, ax)  # Add colorbar to plot
