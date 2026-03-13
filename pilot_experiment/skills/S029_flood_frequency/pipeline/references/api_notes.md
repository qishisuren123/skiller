# Key API references for flood frequency analysis

## pandas
- pd.read_csv(): Load CSV data
- pd.to_datetime(): Convert date strings to datetime objects
- df.groupby(): Group data by year for annual maxima
- df.sort_values(): Sort data chronologically

## numpy
- np.isnan(): Check for missing values
- np.where(): Find indices of valid data
- np.percentile(): Calculate percentiles for outlier detection
- np.full_like(): Create arrays filled with specific values

## scipy.stats
- stats.genextreme.fit(): Fit GEV distribution (methods: 'MLE', 'MM')
- stats.genextreme.ppf(): Calculate quantiles from fitted distribution
- FitSolverError: Exception raised when optimization fails

## argparse
- ArgumentParser(): Create command-line interface
- add_argument(): Define CLI arguments with validation
- parse_args(): Parse command-line arguments
