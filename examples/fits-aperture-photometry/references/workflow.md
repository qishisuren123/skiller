# FITS Aperture Photometry Workflow

## Step 1: Data Preparation
- Prepare FITS images with proper headers (EXPTIME, FILTER, GAIN, RDNOISE, WCS)
- Create star catalog CSV with columns: star_id, ra, dec, star_type
- Ensure star_type values are 'target', 'comparison', or 'check'

## Step 2: Image Loading and Preprocessing
- Load FITS data with proper byte order handling for SEP compatibility
- Convert to little-endian float64 format: `data.astype('<f8')`
- Extract metadata from headers with fallback defaults
- Create WCS object for coordinate transformations

## Step 3: Bad Pixel Masking
- Generate bad pixel mask using sigma clipping (default 5σ)
- Apply morphological dilation to catch neighboring affected pixels
- Use mask in all photometry operations to exclude bad regions

## Step 4: Source Detection and FWHM Estimation
- Use SEP for background subtraction and source detection
- Calculate median FWHM from detected sources: `2.0 * sqrt(a * b)`
- Use FWHM for adaptive aperture sizing

## Step 5: Coordinate Conversion
- Convert catalog RA/Dec to pixel coordinates using WCS
- Filter stars to include only those within image boundaries
- Handle coordinate transformation errors gracefully

## Step 6: Aperture Photometry
- Create apertures based on strategy (fixed/adaptive/elliptical)
- Define sky annulus for local background estimation
- Perform photometry with bad pixel mask applied
- Calculate sky-subtracted fluxes

## Step 7: Error Calculation
- Compute Poisson noise from source flux
- Add sky noise contribution with aperture area scaling
- Include readout noise component
- Propagate total noise to magnitude errors

## Step 8: Results Compilation
- Calculate instrumental magnitudes: -2.5 * log10(flux/exptime)
- Combine photometry results with catalog information
- Generate output table with all measurements and metadata

## Step 9: Quality Assessment
- Check for reasonable FWHM values (typically 2-10 pixels)
- Verify magnitude errors are reasonable (<0.1 mag for bright stars)
- Compare results across different aperture sizes for consistency
