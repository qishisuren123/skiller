# Boolean array handling (avoid ambiguity error)
# Wrong:
in_cell = (lat >= grid_lat) & (lat < grid_lat + resolution) & (lon >= grid_lon) & (lon < grid_lon + resolution) & valid_mask

# Correct:
lat_condition = (lat >= grid_lat) & (lat < grid_lat + resolution)
lon_condition = (lon >= grid_lon) & (lon < grid_lon + resolution)
in_cell = lat_condition & lon_condition & valid_mask

# Efficient grid indexing (avoid nested loops)
# Wrong:
for i, grid_lat in enumerate(lat_grid):
    for j, grid_lon in enumerate(lon_grid):
        # Process each grid cell individually

# Correct:
lat_indices = np.floor((lat_flat - lat_start) / resolution).astype(int)
lon_indices = np.floor((lon_flat - lon_start) / resolution).astype(int)
grid_data = defaultdict(list)
for lat_idx, lon_idx, bt_val in zip(lat_indices, lon_indices, bt_valid):
    grid_data[(lat_idx, lon_idx)].append(bt_val)

# Longitude wraparound handling
def handle_longitude_wraparound(lon_flat):
    lon_range = lon_flat.max() - lon_flat.min()
    if lon_range > 180:
        lon_flat = np.where(lon_flat < 0, lon_flat + 360, lon_flat)
        wraparound = True
    else:
        wraparound = False
    return lon_flat, wraparound

# IQR-based outlier removal
q1, q3 = np.percentile(bt_flat, [25, 75])
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr
outlier_mask = (bt_flat >= lower_bound) & (bt_flat <= upper_bound)
