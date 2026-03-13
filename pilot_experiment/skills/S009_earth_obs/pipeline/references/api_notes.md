# Pandas Time Series Operations
pd.to_datetime(series)                    # Convert to datetime
df.set_index('timestamp')                 # Set timestamp as index
df.resample('1H').mean()                  # Resample to hourly averages
df.reindex(common_index)                  # Align to common time grid
pd.date_range(start, end, freq='1H')      # Create time range
df.ffill(limit=3)                         # Forward fill missing values
df.bfill(limit=3)                         # Backward fill missing values

# Pandas DataFrame Operations
pd.concat([df1, df2], axis=1)             # Concatenate horizontally
df.groupby('column')                      # Group by column values
df.select_dtypes(include=[float, int])    # Select numeric columns only
df.drop_duplicates()                      # Remove duplicate rows
df.sort_index()                           # Sort by index

# Frequency String Formats
'T' or 'min'    # Minutes
'H'             # Hours  
'D'             # Days
'30T'           # 30 minutes
'2H'            # 2 hours
