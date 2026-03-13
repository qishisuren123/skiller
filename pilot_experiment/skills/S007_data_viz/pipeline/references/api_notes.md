# Pandas operations for neural data
df.groupby('time')[neuron_cols].mean()  # Group by time, average across trials
df.pivot_table(index='trial', columns='time', values='pop_mean')  # Restructure for statistics
df.mean(axis=1, skipna=True)  # Row-wise mean ignoring NaN
df.sem(axis=0, skipna=True)   # Standard error of mean across columns
df.fillna(0)  # Replace NaN with 0

# Numpy operations for performance
np.nanmean(data, axis=1)  # Mean ignoring NaN values
np.linspace(0, n-1, n_ticks, dtype=int)  # Create evenly spaced indices

# Matplotlib heatmap setup
matplotlib.use('Agg')  # Non-interactive backend
plt.imshow(data, aspect='auto', cmap='viridis', origin='lower')
plt.xticks(indices, labels)  # Custom tick positions and labels
plt.colorbar(im, label='Firing Rate')
plt.savefig(path, dpi=300, bbox_inches='tight')
