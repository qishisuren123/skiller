# pandas
pd.read_csv(filepath) - Read CSV file into DataFrame
pd.to_datetime(series) - Convert to datetime objects
pd.cut(series, bins, labels, right=False) - Create categorical bins
pd.date_range(start, end, freq='D') - Generate date range
df.groupby(column).size() - Count occurrences by group
df.merge(other, on=column, how='left') - Join DataFrames

# numpy
np.log(array) - Natural logarithm
np.arange(n) - Create array [0, 1, ..., n-1]
np.any(condition) - Test if any element is True
np.unique(array) - Get unique values

# scipy.stats
stats.linregress(x, y) - Linear regression returning slope, intercept, r_value, p_value, std_err

# argparse
parser.add_argument('--name', required=True, type=float, default=value, help='description')
