# Pandas Operations for AQI Calculation

## Data Reading and Preprocessing
- `pd.read_csv(filepath)` - Read pollutant data from CSV
- `pd.to_datetime(series)` - Convert timestamp strings to datetime objects
- `df['date'] = df['timestamp'].dt.date` - Extract date component

## Grouping and Aggregation
- `df.groupby('date')['pollutant'].mean()` - Calculate daily averages
- `df.groupby('date')['pollutant'].max()` - Calculate daily maximums
- `series.rolling(window=8, min_periods=6).mean()` - Rolling averages with minimum data requirement

## Safe Data Access
- `series.loc[key] if key in series.index else None` - Safe access to grouped series
- `pd.isna(value) or value is None` - Comprehensive null checking

## File Operations
- `os.makedirs(path, exist_ok=True)` - Create output directories
- `df.to_csv(filepath, index=False)` - Write DataFrame to CSV
- `json.dump(data, file, indent=2)` - Write formatted JSON files
