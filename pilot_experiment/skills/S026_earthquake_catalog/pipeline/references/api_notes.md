# pandas DataFrame operations
df = pd.read_csv(filename)
df['datetime'] = pd.to_datetime(df[column])
df.sort_values('column_name')
df[df['column'] >= value]  # filtering
df.loc[df['column'].idxmax()]  # find row with max value

# numpy histogram and mathematical operations
hist, bins = np.histogram(data, bins=bin_array)
np.sum(array[i:])  # sum from index i to end
np.mean(array)
np.arange(start, stop, step)

# argparse for CLI
parser = argparse.ArgumentParser(description='...')
parser.add_argument('--input', required=True, help='...')
parser.add_argument('--param', type=float, default=50.0, help='...')
args = parser.parse_args()

# datetime operations
from datetime import timedelta
time_mask = (df['datetime'] > start_time) & (df['datetime'] <= end_time)
time_diff = (time2 - time1).total_seconds() / 3600  # hours
