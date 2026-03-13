# Key Libraries for Atmospheric Ozone Analysis

## NumPy Functions
- `np.gradient(y, x)`: Calculate temperature lapse rates and pressure gradients
- `np.isfinite()`: Check for valid numerical values in atmospheric data
- `np.argmax()`: Find altitude of maximum ozone concentration
- `np.sum(mask)`: Count valid data points after quality control

## SciPy Integration & Optimization  
- `scipy.integrate.trapz(y, x)`: Integrate ozone columns using trapezoidal rule
- `scipy.optimize.curve_fit()`: Fit exponential decay model for scale height calculation
- Parameters: func, xdata, ydata, p0 (initial guess)

## Pandas Data Handling
- `pd.read_csv()`: Load ozonesonde measurement files
- Expected columns: altitude_km, pressure_hPa, temperature_K, ozone_mPa
- `.values`: Convert DataFrame columns to NumPy arrays for numerical processing

## Matplotlib Atmospheric Plotting
- `plt.subplots(figsize=(8,10))`: Create vertical profile plot format
- `ax.axhline()`: Mark tropopause and ozone maximum altitudes
- `ax.set_ylim(0, 35)`: Standard atmospheric altitude range
- `plt.savefig(dpi=300)`: Publication-quality output resolution

## Atmospheric Constants
- Tropopause lapse rate threshold: 2 K/km (WMO definition)
- Typical ozone scale height: 5-10 km in lower stratosphere  
- Dobson Unit conversion: ~2.69e16 molecules/cm²
- Standard atmosphere: 1013.25 hPa surface pressure
