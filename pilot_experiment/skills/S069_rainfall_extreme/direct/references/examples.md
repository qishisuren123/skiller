# Example 1: Basic return period analysis
import numpy as np

# Sample annual maxima data (mm/day)
annual_maxima = np.array([45.2, 67.8, 23.1, 89.4, 34.7, 56.3, 78.9, 41.2, 92.1, 38.5])

# Calculate return periods using Weibull formula
n = len(annual_maxima)
sorted_maxima = np.sort(annual_maxima)[::-1]  # [92.1, 89.4, 78.9, ...]
ranks = np.arange(1, n + 1)                   # [1, 2, 3, ...]
return_periods = (n + 1) / ranks              # [11.0, 5.5, 3.67, ...]

# Find 10-year return period threshold
threshold_10yr = np.interp(10.0, return_periods[::-1], sorted_maxima[::-1])
print(f"10-year return period: {threshold_10yr:.1f} mm/day")

# Example 2: Complete workflow with pandas
import pandas as pd
from datetime import datetime, timedelta

# Create sample daily precipitation data
np.random.seed(42)
n_days = 1095  # 3 years
daily_precip = np.random.exponential(2.0, n_days)  # Exponential distribution
daily_precip[daily_precip > 50] = -1  # Simulate some missing data

# Create date index
start_date = datetime(2020, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(n_days)]

# Process data
valid_mask = daily_precip >= 0
df = pd.DataFrame({
    'precip': daily_precip[valid_mask],
    'date': pd.to_datetime(np.array(dates)[valid_mask])
})
df['year'] = df['date'].dt.year

# Extract annual maxima for complete years
days_per_year = df.groupby('year').size()
complete_years = days_per_year[days_per_year >= 365].index
annual_maxima = df[df['year'].isin(complete_years)].groupby('year')['precip'].max()

print(f"Annual maxima: {annual_maxima.values}")
print(f"Complete years: {complete_years.tolist()}")
