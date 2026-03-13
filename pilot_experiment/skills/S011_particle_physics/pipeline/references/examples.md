# Memory-efficient boolean masking
mask = pd.Series(True, index=df.index)
mask &= (df['column'] > threshold)
result_df = df[mask].copy()

# Safe division with zero checking
if denominator == 0:
    ratio = float('inf') if numerator > 0 else 0
else:
    ratio = numerator / denominator

# Proper DataFrame column assignment
df['new_column'] = 'default_value'
df.loc[condition_mask, 'new_column'] = 'special_value'

# Data type optimization for memory
dtype_dict = {
    'int_column': 'int16',    # For small integers
    'float_column': 'float32', # For reduced precision floats
    'small_int': 'int8'       # For very small integers (0-255)
}
df = pd.read_csv(file, dtype=dtype_dict)

# Cut flow tracking pattern
cut_flow = {}
cut_flow['initial'] = len(df)
df = df[condition1]
cut_flow['after_cut1'] = len(df)
df = df[condition2] 
cut_flow['after_cut2'] = len(df)
