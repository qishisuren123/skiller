# pandas - Data manipulation
pd.read_csv(filepath)                    # Load CSV data
df.pivot_table(index, values, aggfunc)   # Reshape data with aggregation
df.groupby(column).mean()                # Group and aggregate operations
df.nunique()                             # Count unique values
series.sem()                             # Standard error of mean

# matplotlib - Plotting
matplotlib.use('Agg')                    # Set non-interactive backend
plt.figure(figsize=(width, height))      # Create figure with size
plt.fill_between(x, y1, y2, alpha)       # Shaded error regions
plt.savefig(path, dpi, bbox_inches)      # Save high-quality plots
plt.close()                              # Free memory after saving

# seaborn - Statistical visualization
sns.heatmap(data, cmap, cbar_kws)        # Create heatmap with colorbar
xticklabels, yticklabels                 # Control tick label frequency

# numpy - Numerical operations
np.array.T                               # Matrix transpose
np.mean(axis=0/1)                        # Mean along specific axis
