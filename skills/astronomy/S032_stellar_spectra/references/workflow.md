1. Initialize StellarSpectraProcessor with spectral line definitions and classification templates
2. Parse command-line arguments for wavelength range, number of spectra, and SNR parameters
3. Create output directory structure for results storage
4. Generate wavelength array with specified range and resolution
5. For each synthetic spectrum:
   a. Randomly select spectral type from O, B, A, F, G, K, M classes
   b. Generate synthetic flux with realistic continuum and absorption lines
   c. Add Gaussian noise based on specified SNR level
6. Apply continuum normalization:
   a. Scale wavelength values to prevent numerical instability
   b. Iteratively fit polynomial continuum with sigma clipping
   c. Handle SVD convergence failures with polynomial order reduction
   d. Normalize flux by dividing by fitted continuum
7. Extract spectral features:
   a. Calculate equivalent widths for H-alpha, H-beta, Ca H&K, Mg I lines
   b. Measure line depths and continuum slope
   c. Estimate actual SNR using median absolute deviation
8. Apply classification algorithm:
   a. Compare measured features to spectral type templates
   b. Calculate weighted scores for Balmer ratios, metal line strengths
   c. Generate probability distribution over spectral types
   d. Assign quality flags based on SNR and measurement validity
9. Save results to HDF5 files with normalized spectra and metadata
10. Export classification summary to JSON format with confidence scores
