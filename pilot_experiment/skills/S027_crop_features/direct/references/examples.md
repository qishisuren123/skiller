# Example 1: Basic GDD calculation with field grouping
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'field_id': ['F001', 'F001', 'F002', 'F002'],
    'date': ['2023-05-01', '2023-05-02', '2023-05-01', '2023-05-02'],
    'temperature': [15.2, 18.5, 12.1, 16.8]
})

base_temp = 10.0
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['field_id', 'date'])
df['gdd_daily'] = np.maximum(0, df['temperature'] - base_temp)
df['cumulative_gdd'] = df.groupby('field_id')['gdd_daily'].cumsum()
print(df)

# Example 2: NDVI peak detection and feature aggregation
df_extended = pd.DataFrame({
    'field_id': ['F001', 'F001', 'F001', 'F002', 'F002'],
    'date': pd.to_datetime(['2023-05-01', '2023-06-01', '2023-07-01', '2023-05-01', '2023-06-01']),
    'ndvi': [0.3, 0.8, 0.6, 0.4, 0.7],
    'yield_tons': [4.2, 4.2, 4.2, 3.8, 3.8]
})

# Find peak NDVI dates
peak_idx = df_extended.groupby('field_id')['ndvi'].idxmax()
peak_info = df_extended.loc[peak_idx][['field_id', 'date', 'ndvi']]
peak_info['peak_date'] = peak_info['date'].dt.strftime('%Y-%m-%d')

# Aggregate NDVI stats
ndvi_stats = df_extended.groupby('field_id')['ndvi'].agg(['mean', 'max', 'std'])
print("Peak NDVI info:")
print(peak_info)
print("\nNDVI statistics:")
print(ndvi_stats)
