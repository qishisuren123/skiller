# Safe field-level aggregation with NaN handling
def safe_aggregation(df):
    # Always reset_index after groupby operations
    result = df.groupby('field_id').agg({
        'temperature': 'mean',
        'rainfall': 'sum'
    }).reset_index()
    
    # Use explicit rename for clarity
    result = result.rename(columns={
        'rainfall': 'total_rainfall'
    })
    return result

# Robust cumulative calculation with NaN handling
def calculate_cumulative_with_nans(df, value_col, group_col):
    df_copy = df.copy().sort_values([group_col, 'date']).reset_index(drop=True)
    
    # Handle NaN values explicitly
    df_copy[f'{value_col}_clean'] = np.where(
        df_copy[value_col].isna(),
        0,  # or appropriate default
        df_copy[value_col]
    )
    
    # Calculate cumulative per group
    df_copy[f'cumulative_{value_col}'] = df_copy.groupby(group_col)[f'{value_col}_clean'].cumsum()
    return df_copy

# Safe statistics calculation with all-NaN handling
def safe_stats_calculation(series):
    if series.dropna().empty:
        return {
            'mean': np.nan,
            'max': np.nan,
            'min': np.nan,
            'std': np.nan
        }
    else:
        return {
            'mean': series.mean(),
            'max': series.max(),
            'min': series.min(),
            'std': series.std()
        }
