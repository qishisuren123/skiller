# Key Libraries and Functions

## Pandas
- `pd.read_csv(file, parse_dates=[0], index_col=0)` - Load time series data
- `pd.Series.index.intersection()` - Align time series datasets
- `pd.Series.index.dayofyear` - Extract day of year for climatology
- `pd.DataFrame.to_csv()` - Save processed time series

## NumPy
- `np.asarray()` - Convert to arrays for vectorized heat index calculation
- `np.where(condition, x, y)` - Conditional array operations for formula branches
- `np.percentile(data, percentile)` - Calculate climatological thresholds
- `np.abs()`, `np.sqrt()` - Mathematical operations for NWS adjustments

## SciPy Stats
- `stats.linregress(x, y)` - Linear regression for trend analysis
- `stats.gumbel_r.fit(data)` - Fit Gumbel distribution for return periods
- `stats.gumbel_r.cdf(x, *params)` - Calculate exceedance probabilities

## DateTime Operations
- `datetime.strptime(date_str, format)` - Parse date strings
- `timedelta(days=n)` - Date arithmetic for event detection
- `date.strftime(format)` - Format dates for output

## Heat Index Formula Components
- Simple formula: `0.5 * (T + 61.0 + ((T-68.0)*1.2) + (RH*0.094))`
- Rothfusz regression: Multi-term polynomial with interaction terms
- Low humidity adjustment: `((13-RH)/4) * sqrt((17-|T-95|)/17)`
- High humidity adjustment: `((RH-85)/10) * ((87-T)/5)`
