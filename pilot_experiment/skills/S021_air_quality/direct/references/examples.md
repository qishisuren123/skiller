# Example 1: Basic AQI calculation for single pollutant
import pandas as pd
import numpy as np

# Sample hourly PM2.5 data
data = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=48, freq='H'),
    'pm25': [15.2, 18.7, 22.1, 19.8, 25.3, 28.9] * 8
})

# Calculate 24-hour average
data['date'] = data['timestamp'].dt.date
daily_pm25 = data.groupby('date')['pm25'].mean()

# Apply AQI breakpoints for PM2.5
def pm25_to_aqi(concentration):
    if 0 <= concentration <= 12.0:
        return ((50 - 0) / (12.0 - 0)) * (concentration - 0) + 0
    elif 12.1 <= concentration <= 35.4:
        return ((100 - 51) / (35.4 - 12.1)) * (concentration - 12.1) + 51
    # ... additional breakpoints
    return np.nan

daily_aqi = daily_pm25.apply(pm25_to_aqi)
print(f"Daily PM2.5 AQI: {daily_aqi.values}")

# Example 2: Complete workflow with multiple pollutants
hourly_data = pd.read_csv('air_quality.csv')
hourly_data['timestamp'] = pd.to_datetime(hourly_data['timestamp'])

# Apply averaging rules
daily_results = []
for date in hourly_data['timestamp'].dt.date.unique():
    day_data = hourly_data[hourly_data['timestamp'].dt.date == date]
    
    # 24-hour averages
    pm25_avg = day_data['pm25'].mean()
    pm10_avg = day_data['pm10'].mean()
    
    # 8-hour rolling maximum
    o3_8hr = day_data['o3'].rolling(window=8, min_periods=6).mean().max()
    
    # Calculate sub-indices
    pm25_aqi = calculate_aqi_subindex(pm25_avg, 'pm25')
    pm10_aqi = calculate_aqi_subindex(pm10_avg, 'pm10') 
    o3_aqi = calculate_aqi_subindex(o3_8hr, 'o3')
    
    # Overall AQI is maximum
    overall_aqi = max([pm25_aqi, pm10_aqi, o3_aqi])
    
    daily_results.append({
        'date': date,
        'aqi': overall_aqi,
        'category': get_aqi_category(overall_aqi)
    })

daily_df = pd.DataFrame(daily_results)
