# Safe depth grid generation
depth_min, depth_max = df['depth'].min(), df['depth'].max()
new_depths = np.arange(depth_min, depth_max + step/2, step)
new_depths = new_depths[new_depths <= depth_max]  # Ensure bounds

# Robust interpolation
for col in log_columns:
    interpolator = interp1d(df['depth'], df[col], kind='linear', 
                           bounds_error=False, 
                           fill_value=(df[col].iloc[0], df[col].iloc[-1]))
    resampled_data[col] = interpolator(new_depths)

# Safe porosity calculation with validation
raw_phit = (2.65 - bulk_density) / (2.65 - 1.0)
phit = np.clip(raw_phit, 0.0, 0.5)
negative_count = (raw_phit < 0).sum()
if negative_count > 0:
    print(f"Warning: {negative_count} negative porosity values clipped")

# Vectorized lithology classification
def classify_lithology(vsh, phit, resistivity, bulk_density, neutron_porosity):
    lithology = np.full(len(vsh), 'siltstone', dtype=object)
    
    limestone_mask = (bulk_density > 2.5) & (neutron_porosity < 0.15) & (vsh < 0.3)
    sandstone_mask = (vsh < 0.3) & (phit > 0.1) & (resistivity > 10) & (~limestone_mask)
    shale_mask = vsh >= 0.6
    
    lithology[limestone_mask] = 'limestone'
    lithology[sandstone_mask] = 'sandstone'
    lithology[shale_mask] = 'shale'
    
    return lithology
