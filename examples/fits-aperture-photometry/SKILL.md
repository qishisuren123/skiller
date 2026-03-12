---
name: fits-aperture-photometry
description: "对天文FITS图像数据执行孔径测光(Aperture Photometry)。功能：支持固定孔径、FWHM自适应孔径、椭圆孔径；支持局部天光环估计与坏像元掩膜；批量输出目标星+比较星+检验星的测光结果。数据需求：每帧需有EXPTIME、滤光片、增益/读噪、WCS信息。质量：同一夜同一目标在不同孔径策略下结果可追溯；给出孔径修正(curve of growth)。验收：亮星区与参考星表零点偏差可控； Use this skill when the user needs to 对天文fits图像数据执行孔径测光(aperture photometry)。功能：支持固定孔径、fwhm自适应孔径、椭圆孔径；支持局部天光环估计与坏像元掩膜；批量输出目标星+比较星+检验星的测光结果."
license: MIT
compatibility: "Python >=3.9; astropy, photutils, sep, numpy, matplotlib"
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---

# FITS Aperture Photometry

## Overview
Comprehensive aperture photometry system for astronomical FITS images supporting multiple aperture strategies, bad pixel masking, curve of growth analysis, and proper error estimation. Handles target, comparison, and check stars with coordinate conversion via WCS.

## When to Use
- Processing astronomical CCD/CMOS images for photometric analysis
- Variable star monitoring requiring precise magnitude measurements
- Differential photometry with comparison stars
- Quality assessment of photometric data with multiple aperture sizes
- Curve of growth analysis for aperture corrections

## Inputs
- FITS images with WCS headers (EXPTIME, FILTER, GAIN, RDNOISE required)
- CSV star catalog with columns: star_id, ra, dec, star_type (target/comparison/check)
- Configuration parameters for aperture sizes, sky annulus, detection thresholds

## Workflow
1. Load FITS image using `scripts/main.py --input image.fits --catalog stars.csv`
2. Handle data type conversion and byte order for SEP compatibility
3. Create bad pixel mask from image statistics and morphological filtering
4. Convert RA/Dec coordinates to pixel positions using WCS
5. Detect sources for FWHM estimation using SEP background subtraction
6. Perform aperture photometry with multiple strategies (fixed/adaptive/elliptical)
7. Calculate instrumental magnitudes with proper error propagation
8. Generate curve of growth analysis for aperture corrections
9. Output results to CSV with all photometric measurements
10. Reference `references/workflow.md` for detailed processing steps

## Error Handling
The system must handle and error-check several critical issues:
- **SEP Data Type Error**: Handle FITS byte order incompatibility by converting to little-endian float64
- **Photutils Position Error**: Convert coordinate lists to numpy arrays for aperture_photometry compatibility  
- **WCS Conversion Error**: Validate coordinate transformations and handle stars outside image bounds
- **Bad Pixel Masking**: Implement sigma clipping and morphological filtering to handle cosmic rays and detector artifacts
- **Missing Metadata Error**: Provide defaults for missing FITS header values (EXPTIME, GAIN, etc.)

## Common Pitfalls
- FITS images with big-endian byte order cause SEP failures - always convert to native byte order
- Photutils expects positions as (x_array, y_array) tuples, not list of (x,y) pairs
- Sky annulus must not overlap with source aperture to avoid flux contamination
- Curve of growth analysis requires sufficient radial sampling and bright enough stars
- Error propagation must include Poisson noise, sky noise, and readout noise components

## Quick Reference

```bash
# Fixed aperture photometry
python scripts/main.py --input image.fits --catalog stars.csv --output phot.csv \
    --aperture-type fixed --aperture-radius 8.0

# FWHM-adaptive aperture
python scripts/main.py --input image.fits --catalog stars.csv --output phot.csv \
    --aperture-type fwhm --fwhm-multiplier 2.5
```

```python
# Core aperture photometry pattern with SEP
import sep
import numpy as np
from astropy.io import fits

data = fits.getdata('image.fits').astype(np.float64, order='C')  # fix byte order
bkg = sep.Background(data)
data_sub = data - bkg.back()
flux, fluxerr, flag = sep.sum_circle(data_sub, x, y, r, err=bkg.globalrms)
mag = -2.5 * np.log10(flux) + 25.0  # instrumental magnitude
```

## Output Format
CSV file with columns:
- star_id, ra, dec, star_type, x_pixel, y_pixel
- aperture_type, aperture_radius, fwhm, exptime, filter, filename
- aperture_sum, sky_mean, aperture_sum_bkgsub
- instrumental_mag, mag_error, aperture_correction
- Separate curve of growth table with radius vs flux measurements
