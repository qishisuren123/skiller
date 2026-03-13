# Key Libraries for Estuarine CTD Analysis

## NumPy Functions
- `np.gradient(array, spacing)` - Calculate numerical gradient for salinity/density profiles
- `np.convolve(array, kernel, mode='same')` - Smooth noisy CTD data
- `np.where(condition)` - Find indices meeting gradient/inversion criteria
- `np.trapz(y, x)` - Integrate for Simpson's stratification parameter

## SciPy Integration & Interpolation
- `scipy.integrate.trapz(y, x)` - Numerical integration for stratification calculations
- `scipy.interpolate.griddata(points, values, xi, method='linear')` - 2D field interpolation
- Methods: 'linear', 'nearest', 'cubic' for different smoothness requirements

## HDF5 for Oceanographic Data
- `h5py.File(filename, 'w')` - Create HDF5 file for gridded salinity fields
- `file.create_dataset(name, data=array)` - Store 2D/3D oceanographic arrays
- `file.attrs[key] = value` - Store metadata (transect info, units, etc.)

## Pandas for Station Data
- `pd.DataFrame(stations_list)` - Organize multi-station CTD data
- `df.groupby('transect_id')` - Process multiple transect lines
- `df.interpolate(method='linear')` - Fill small gaps in depth series

## Seawater Equation of State
- UNESCO formula implementation for accurate density calculations
- Critical for stratification analysis in variable temperature/salinity conditions
- Pressure effects become important below 50m depth
