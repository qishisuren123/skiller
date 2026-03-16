# CMB Power Spectrum Analysis Workflow

1. **Data Preparation**
   - Ensure CMB temperature map is in HEALPix format
   - Save as NumPy array (.npy file) with temperature values in microkelvin
   - Verify pixel count matches valid HEALPix NSIDE (12*NSIDE²)

2. **Load and Validate Data**
   - Use load_cmb_map() to read temperature map
   - Automatically detect NSIDE parameter from pixel count
   - Log map statistics for verification

3. **Preprocessing**
   - Remove monopole and dipole components using healpy.remove_monopole()
   - This is standard practice in CMB cosmological analysis

4. **Spherical Harmonic Analysis**
   - Compute alm coefficients using healpy.map2alm() with 3 iterations
   - Set lmax based on map resolution (3*NSIDE-1) or user specification
   - Use optimized healpy transforms for performance

5. **Power Spectrum Computation**
   - Convert alm to power spectrum using healpy.alm2cl()
   - Extract multipoles l≥2 (exclude monopole and dipole)
   - Validate array indexing to avoid zero values

6. **Statistical Analysis**
   - Compute total power, peak multipole, RMS temperature
   - Check for zero fraction to detect computation errors
   - Filter invalid values (NaN, infinite)

7. **Output Generation**
   - Save numerical results to JSON format
   - Create diagnostic plot in standard CMB format: l(l+1)Cl/(2π)
   - Use log-log scale when appropriate for visualization
