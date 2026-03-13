# Key Libraries and Functions

## pandas
- pd.read_csv(): Load case report data
- pd.to_datetime(errors='coerce'): Parse onset dates with error handling
- pd.date_range(): Create complete date range for epidemic curve
- pd.cut(): Create age group bins for CFR analysis
- df.groupby().size(): Aggregate daily case counts
- df.merge(): Join datasets on date columns

## numpy
- np.log(): Natural logarithm for exponential growth fitting
- np.polyfit(x, y, 1): Linear regression for growth rate estimation
- np.isfinite(): Check for valid numerical values
- np.arange(): Create sequential day numbers for regression

## argparse
- ArgumentParser(): Command-line interface setup
- add_argument(): Define CLI parameters with types and defaults

## json
- json.dump(): Export analysis results as structured JSON

## datetime
- datetime.strftime(): Format dates for output
