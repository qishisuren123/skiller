# Proper time indexing after filtering
early_data = early_data.reset_index()
days = early_data['index'].values  # Preserves original spacing

# Age binning with correct edges
pd.cut(df['age'], bins=[0, 19, 41, 61, float('inf')], 
       labels=['0-18', '19-40', '41-60', '61+'], 
       right=False, include_lowest=True)

# Complete date series with zero-filling
date_range = pd.date_range(start=df['onset_date'].min(), end=df['onset_date'].max(), freq='D')
complete_series = pd.DataFrame({'date': date_range})
daily_cases = complete_series.merge(daily_cases, on='date', how='left')
daily_cases['daily_cases'] = daily_cases['daily_cases'].fillna(0)

# R0 calculation with validation
if len(early_data) >= 3 and len(np.unique(days)) >= 2:
    slope, _, r_value, _, _ = stats.linregress(days, np.log(cumulative_cases))
    R0 = 1 + slope * serial_interval
