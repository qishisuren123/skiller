# Example 1: Basic AQI calculation for PM2.5
concentration = 25.3  # μg/m³
breakpoints = AQI_BREAKPOINTS['pm25']
# Finds range [12.1, 35.4] -> [51, 100]
# AQI = ((100-51)/(35.4-12.1)) * (25.3-12.1) + 51 = 79

# Example 2: Rolling 8-hour average calculation
df_sorted = df.sort_values('timestamp')
df_sorted['o3_8hr'] = df_sorted['o3'].rolling(window=8, min_periods=6).mean()
daily_o3_max = df_sorted.groupby('date')['o3_8hr'].max()

# Example 3: Monthly aggregation pattern
monthly_data = defaultdict(list)
for date in all_dates:
    month_key = f"{date.year}-{date.month:02d}"
    if aqi_value is not None:
        monthly_data[month_key].append(aqi_value)

# Example 4: Safe data access from grouped series
pm25_conc = daily_pm25.loc[date] if date in daily_pm25.index else None
aqi_value = calculate_aqi(pm25_conc, 'pm25')
