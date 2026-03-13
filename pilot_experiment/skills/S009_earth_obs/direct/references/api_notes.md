# Pandas Key Functions for Time Series Processing

## DateTime Handling
- pd.to_datetime(series, utc=True, errors='coerce'): Convert to UTC datetime with error handling
- df.set_index('timestamp').sort_index(): Set datetime index and sort chronologically

## Time Series Resampling  
- df.resample(freq).mean(): Resample to frequency using mean aggregation
- df.reindex(new_index): Align DataFrame to new time index
- pd.date_range(start, end, freq): Generate regular datetime index

## Missing Value Handling
- df.fillna(method='ffill', limit=3): Forward fill with maximum of 3 consecutive fills
- df.fillna(method='bfill', limit=3): Backward fill with limit
- df.dropna(subset=['column']): Remove rows with NaN in specific columns

## Data Validation and Cleaning
- df.drop_duplicates(subset=['column']): Remove duplicate rows based on column
- required_cols.issubset(set(df.columns)): Check if required columns exist
- df.isna().sum().sum(): Count total missing values across DataFrame

## File Operations
- Path(directory).glob("*.csv"): Find all CSV files in directory
- pd.read_csv(filepath, nrows=1): Read only header row for validation
