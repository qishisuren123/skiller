# Lapse rate calculation with NaN handling
for i in range(len(df) - 1):
    t1, t2 = df.iloc[i]['temperature'], df.iloc[i+1]['temperature']
    alt1, alt2 = df.iloc[i]['altitude'], df.iloc[i+1]['altitude']
    
    if pd.isna(t1) or pd.isna(t2):
        lapse_rates.append(np.nan)
        continue
        
    lapse_rate = -(t2 - t1) / ((alt2 - alt1) / 1000)
    lapse_rates.append(lapse_rate)

# Tropopause detection with flexible depth requirement
upper_limit = current_alt + 2000
levels_above = above_5km[above_5km['altitude'] > current_alt]
max_alt_above = levels_above['altitude'].max()
if max_alt_above < upper_limit:
    continue  # Not enough vertical coverage

# CAPE calculation with proper parcel lifting
if not lcl_found:
    # Dry adiabatic lifting
    parcel_temp -= 9.8 * (dz / 1000)
    parcel_dewpoint -= 2.0 * (dz / 1000)
else:
    # Moist adiabatic lifting
    parcel_temp -= 6.0 * (dz / 1000)

# Data validation pattern
required_cols = ['pressure', 'temperature', 'dewpoint', 'altitude']
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")
