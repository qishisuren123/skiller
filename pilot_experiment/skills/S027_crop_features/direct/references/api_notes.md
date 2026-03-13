# pandas key functions for agricultural data processing
pd.read_csv(filepath) - Load field observation data
pd.to_datetime(series) - Parse date strings to datetime objects
df.groupby('field_id') - Group operations by individual fields
df.agg({'col': 'func'}) - Aggregate multiple columns with different functions
df.groupby().cumsum() - Calculate cumulative sums within groups (for GDD)
df.groupby().idxmax() - Find index of maximum value per group (peak NDVI)

# numpy functions for agricultural calculations  
np.maximum(0, values) - Element-wise maximum for GDD thresholding
np.number - Data type selector for numeric columns only

# datetime formatting
dt.strftime('%Y-%m-%d') - Convert datetime to string format for JSON compatibility

# correlation analysis
df.corr() - Compute Pearson correlation matrix
series.abs().sort_values(ascending=False) - Rank correlations by absolute strength
