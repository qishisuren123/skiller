# Key Libraries for CTD Data Processing

## pandas
- pd.read_csv(): Load CTD data from CSV files
- df.groupby('station_id'): Group profiles by station
- df.sort_values('depth_m'): Ensure monotonic depth ordering
- df.drop_duplicates('depth_m'): Remove duplicate depth measurements
- df.isna(): Handle missing oceanographic measurements

## numpy  
- np.arange(start, stop, step): Create regular depth grids
- np.gradient(y, x): Calculate temperature gradients (dT/dz)
- np.nanargmax(): Find maximum gradient ignoring NaN values
- np.where(condition): Locate mixed layer depth threshold crossings
- np.isnan(): Check for invalid oceanographic calculations

## scipy.interpolate
- interp1d(x, y, kind='linear'): Interpolate CTD measurements to regular depths
- bounds_error=False: Allow interpolation within data range only
- fill_value=np.nan: Handle extrapolation beyond measured depths

## argparse
- add_argument('--depth-resolution', type=float): Parse oceanographic parameters
- required=True: Ensure critical file paths are provided

## json
- json.dump(data, file, indent=2): Export station summaries with formatting
