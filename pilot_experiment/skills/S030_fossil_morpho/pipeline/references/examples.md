# Safe division with zero checking
df['ratio'] = np.where(df['denominator'] > 0, 
                      df['numerator'] / df['denominator'], 
                      np.nan)

# Multiple condition checking
df['result'] = np.where((df['a'] > 0) & (df['b'] > 0),
                       df['a'] * df['b'],
                       np.nan)

# PCA standardization with zero std protection
X_std = np.std(X, axis=0)
X_std = np.where(X_std == 0, 1e-10, X_std)
X_standardized = (X - X_mean) / X_std

# Statistics with NaN handling
valid_data = group_data[col].dropna()
if len(valid_data) > 0:
    mean_val = float(valid_data.mean())
    std_val = float(valid_data.std()) if len(valid_data) > 1 else 0.0
else:
    mean_val = None
    std_val = None

# Edge case handling for PCA
if len(df_clean) < 2:
    for i in range(4):
        df[f'PC{i+1}'] = np.nan
    return df, empty_pca_results
