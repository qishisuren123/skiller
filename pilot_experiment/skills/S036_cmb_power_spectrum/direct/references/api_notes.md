# NumPy Array Operations
np.load(file) - Load HEALPix temperature map from .npy file
np.mean(array) - Remove monopole from temperature data
np.sum(array) - Compute spherical harmonic coefficients via integration
np.sqrt(value) - Calculate NSIDE parameter and RMS temperature

# SciPy Special Functions
scipy.special.sph_harm(m, l, phi, theta) - Spherical harmonic functions Y_l^m
scipy.special.legendre(n) - Associated Legendre polynomials (alternative)

# Matplotlib CMB Plotting
plt.loglog(x, y) - Standard log-log plot for power spectrum visualization
plt.xlabel(r'$\ell$') - LaTeX formatting for multipole axis labels
plt.ylabel(r'$\ell(\ell+1)C_\ell/(2\pi)$') - Standard CMB power spectrum units

# HEALPix Pixel Calculations
npix = 12 * nside**2 - Total pixels in HEALPix map
lmax = 3 * nside - 1 - Maximum reliable multipole for given resolution
pixel_area = 4π / npix - Solid angle per pixel for integration weights
