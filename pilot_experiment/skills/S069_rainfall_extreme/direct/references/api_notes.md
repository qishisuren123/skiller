# NumPy - Array operations and statistical functions
np.array(data)                    # Convert list to numpy array
np.sort(array)[::-1]             # Sort in descending order
np.argsort(array)[::-1]          # Get indices for descending sort
np.arange(start, stop)           # Create sequence of integers
np.mean(array)                   # Calculate mean
np.std(array, ddof=1)            # Sample standard deviation
np.percentile(array, percentile) # Calculate percentile
np.interp(x, xp, fp)            # Linear interpolation
np.sum(boolean_array)           # Count True values

# Pandas - Time series and grouping operations
pd.DataFrame(dict)               # Create DataFrame from dictionary
pd.to_datetime(dates)           # Convert to datetime objects
df.groupby('column')            # Group by column values
df.groupby('year').max()        # Annual maximum aggregation
df.groupby('year').size()       # Count records per group
df['date'].dt.year              # Extract year from datetime
df[condition]                   # Boolean indexing

# DateTime - Date manipulation
datetime(year, month, day)       # Create datetime object
timedelta(days=n)               # Time difference
date.strftime('%Y-%m-%d')       # Format date as string
datetime.now().isoformat()      # Current timestamp
