# CMB Angular Power Spectrum Analysis

## Overview
This skill enables computation of angular power spectra from Cosmic Microwave Background (CMB) temperature maps using spherical harmonic decomposition. It processes HEALPix-formatted temperature data and extracts the statistical properties of CMB fluctuations across different angular scales.

## Workflow
1. **Load and validate CMB temperature map** from NumPy array file, ensuring proper HEALPix format and μK units
2. **Determine map parameters** including NSIDE resolution and maximum multipole ℓ_max based on pixel count
3. **Perform spherical harmonic decomposition** to extract a_ℓm coefficients using simplified discrete transform
4. **Calculate angular power spectrum** C_ℓ by averaging |a_ℓm|² over all m values for each multipole ℓ
5. **Compute statistical measures** including total power, peak multipole, and RMS temperature fluctuations
6. **Generate visualization** showing ℓ(ℓ+1)C_ℓ/(2π) vs ℓ plot with proper cosmological formatting
7. **Export results** to JSON format with multipole values and power spectrum data

## Common Pitfalls
- **Incorrect HEALPix pixel ordering**: Always verify RING vs NESTED pixel schemes affect spherical harmonic transforms
- **Units confusion**: Ensure temperature data is in μK and power spectrum output is in μK² units throughout
- **Multipole range errors**: ℓ_max must not exceed √(N_pixels/12) to avoid aliasing in the spherical harmonic transform
- **Memory issues with large maps**: For high-resolution maps, consider chunked processing of spherical harmonic coefficients
- **Statistical bias in low-ℓ modes**: Cosmic variance dominates at ℓ < 10, requiring careful interpretation of results

## Error Handling
Handle file I/O errors gracefully with informative messages about expected input formats. Validate that input arrays have valid HEALPix pixel counts (12×NSIDE²). Check for NaN or infinite values in temperature data before processing. Implement bounds checking for multipole calculations to prevent array index errors. Provide fallback options when output directories don't exist.

## Quick Reference
