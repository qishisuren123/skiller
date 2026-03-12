#!/usr/bin/env python3
"""
FITS Aperture Photometry Tool
Performs aperture photometry on astronomical FITS images with multiple aperture strategies.
"""

import numpy as np
import sep
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy import units as u
from photutils.aperture import CircularAperture, EllipticalAperture, aperture_photometry
from photutils.aperture import CircularAnnulus
import matplotlib.pyplot as plt
import logging
import argparse
from pathlib import Path
import pandas as pd
from scipy import ndimage
import sys

class AperturePhotometry:
    def __init__(self, gain=1.0, readnoise=5.0):
        self.gain = gain
        self.readnoise = readnoise
        self.logger = logging.getLogger(__name__)
        
    def load_fits_image(self, filepath):
        """Load FITS image and extract metadata"""
        with fits.open(filepath) as hdul:
            raw_data = hdul[0].data
            
            # Handle dtype and byte order for SEP compatibility
            if raw_data.dtype.byteorder in ['>', '|']:
                data = raw_data.astype('<f8')  # Little endian float64
            else:
                data = raw_data.astype(np.float64)
            
            data = np.ascontiguousarray(data)
            header = hdul[0].header
            
            exptime = header.get('EXPTIME', 1.0)
            filter_name = header.get('FILTER', 'unknown')
            gain = header.get('GAIN', self.gain)
            readnoise = header.get('RDNOISE', self.readnoise)
            
            wcs = WCS(header)
            
            return data, header, exptime, filter_name, gain, readnoise, wcs
    
    def create_bad_pixel_mask(self, data, sigma_clip=5.0, morphology_filter=True):
        """Create bad pixel mask from image statistics"""
        median_val = np.median(data)
        std_val = np.std(data)
        
        bad_mask = np.abs(data - median_val) > sigma_clip * std_val
        
        if morphology_filter:
            structure = np.ones((3,3))
            bad_mask = ndimage.binary_dilation(bad_mask, structure=structure)
        
        self.logger.info(f"Created bad pixel mask: {np.sum(bad_mask)} bad pixels "
                        f"({100*np.sum(bad_mask)/bad_mask.size:.2f}%)")
        
        return bad_mask
    
    def load_star_catalog(self, catalog_file):
        """Load star catalog from CSV file"""
        catalog = pd.read_csv(catalog_file)
        
        required_cols = ['star_id', 'ra', 'dec', 'star_type']
        missing_cols = [col for col in required_cols if col not in catalog.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        return catalog
    
    def coords_to_pixels(self, ra_deg, dec_deg, wcs):
        """Convert RA/Dec coordinates to pixel coordinates"""
        coords = SkyCoord(ra=ra_deg*u.degree, dec=dec_deg*u.degree, frame='icrs')
        pixel_coords = wcs.world_to_pixel(coords)
        
        if np.isscalar(ra_deg):
            return np.array([float(pixel_coords[0])]), np.array([float(pixel_coords[1])])
        else:
            return np.array(pixel_coords[0]), np.array(pixel_coords[1])
    
    def filter_stars_in_image(self, catalog, wcs, image_shape):
        """Filter catalog to only include stars within image boundaries"""
        x_coords, y_coords = self.coords_to_pixels(catalog['ra'].values, 
                                                  catalog['dec'].values, wcs)
        
        height, width = image_shape
        valid_mask = ((x_coords >= 0) & (x_coords < width) & 
                     (y_coords >= 0) & (y_coords < height))
        
        filtered_catalog = catalog[valid_mask].copy()
        filtered_catalog['x_pixel'] = x_coords[valid_mask]
        filtered_catalog['y_pixel'] = y_coords[valid_mask]
        
        self.logger.info(f"Found {len(filtered_catalog)} stars within image bounds")
        return filtered_catalog
    
    def detect_sources(self, data, threshold=3.0):
        """Detect sources using SEP for FWHM estimation"""
        if data.dtype != np.float64 and data.dtype != np.float32:
            data = data.astype(np.float64)
        
        bkg = sep.Background(data)
        data_sub = data - bkg
        
        objects = sep.extract(data_sub, threshold * bkg.globalrms)
        
        if len(objects) > 0:
            fwhm_estimates = 2.0 * np.sqrt(objects['a'] * objects['b'])
            median_fwhm = np.median(fwhm_estimates[fwhm_estimates > 0])
        else:
            self.logger.warning("No sources detected, using default FWHM=3.0")
            median_fwhm = 3.0
        
        return objects, median_fwhm, bkg
    
    def calculate_photometric_errors(self, flux, sky_mean, aperture_area, sky_area, 
                                   gain, readnoise, exptime):
        """Calculate photometric errors including all noise sources"""
        flux_electrons = flux * gain
        sky_electrons = sky_mean * aperture_area * gain
        
        # Poisson noise from source
        source_noise = np.sqrt(np.abs(flux_electrons))
        
        # Sky noise
        sky_noise = np.sqrt(sky_electrons * (1 + aperture_area/sky_area))
        
        # Readout noise
        readout_noise = readnoise * np.sqrt(aperture_area)
        
        # Total noise in electrons
        total_noise_electrons = np.sqrt(source_noise**2 + sky_noise**2 + readout_noise**2)
        
        # Convert back to ADU
        total_noise_adu = total_noise_electrons / gain
        
        # Magnitude error
        if flux > 0:
            mag_error = 1.0857 * total_noise_adu / flux  # 1.0857 = 2.5/ln(10)
        else:
            mag_error = np.nan
        
        return mag_error, total_noise_adu
    
    def perform_photometry(self, data, positions, aperture_type='fixed', 
                          radius=5.0, fwhm=None, sky_inner=10.0, sky_outer=15.0,
                          mask=None, gain=1.0, readnoise=5.0, exptime=1.0):
        """Perform aperture photometry with error calculation"""
        
        # Ensure positions are in correct format: list of (x, y) tuples
        if isinstance(positions, tuple) and len(positions) == 2:
            # 从 (x_array, y_array) 转为 [(x1,y1), (x2,y2), ...]
            x_arr, y_arr = np.asarray(positions[0]), np.asarray(positions[1])
            positions = np.column_stack([x_arr, y_arr])
        elif isinstance(positions, list):
            positions = np.array(positions)
        
        # Create apertures
        if aperture_type == 'fixed':
            apertures = CircularAperture(positions, r=radius)
        elif aperture_type == 'fwhm_adaptive':
            if fwhm is None:
                raise ValueError("FWHM required for adaptive apertures")
            adaptive_radius = 1.5 * fwhm
            apertures = CircularAperture(positions, r=adaptive_radius)
        elif aperture_type == 'elliptical':
            apertures = EllipticalAperture(positions, a=radius*1.2, b=radius*0.8, theta=0)
        else:
            raise ValueError(f"Unknown aperture type: {aperture_type}")
        
        sky_apertures = CircularAnnulus(positions, r_in=sky_inner, r_out=sky_outer)
        
        # Perform photometry
        phot_table = aperture_photometry(data, apertures, mask=mask)
        sky_phot = aperture_photometry(data, sky_apertures, mask=mask)
        
        # Sky subtraction
        sky_mean = sky_phot['aperture_sum'] / sky_apertures.area
        sky_sum = sky_mean * apertures.area
        final_sum = phot_table['aperture_sum'] - sky_sum
        
        # Calculate errors and magnitudes
        mag_errors = []
        instrumental_mags = []
        
        for i, flux in enumerate(final_sum):
            mag_error, noise_adu = self.calculate_photometric_errors(
                flux, sky_mean[i], apertures.area, sky_apertures.area,
                gain, readnoise, exptime)
            
            if flux > 0:
                instrumental_mag = -2.5 * np.log10(flux / exptime)
            else:
                instrumental_mag = np.nan
            
            mag_errors.append(mag_error)
            instrumental_mags.append(instrumental_mag)
        
        # Add results to table
        phot_table['sky_mean'] = sky_mean
        phot_table['sky_sum'] = sky_sum
        phot_table['aperture_sum_bkgsub'] = final_sum
        phot_table['instrumental_mag'] = instrumental_mags
        phot_table['mag_error'] = mag_errors
        
        return phot_table
    
    def process_single_image(self, fits_file, catalog, aperture_types=['fixed'], 
                           radii=[5.0], sky_inner=10.0, sky_outer=15.0, 
                           create_mask=True):
        """Process a single FITS image with given star catalog"""
        
        # Load image
        data, header, exptime, filt, gain, rn, wcs = self.load_fits_image(fits_file)
        
        # Create bad pixel mask if requested
        mask = None
        if create_mask:
            mask = self.create_bad_pixel_mask(data)
        
        # Filter stars within image
        stars_in_image = self.filter_stars_in_image(catalog, wcs, data.shape)
        
        if len(stars_in_image) == 0:
            self.logger.warning(f"No catalog stars found in {fits_file}")
            return None
        
        # Detect sources for FWHM estimation
        objects, fwhm, bkg = self.detect_sources(data)
        
        results = []
        positions = (stars_in_image['x_pixel'].values, stars_in_image['y_pixel'].values)
        
        # Process each aperture type
        for aperture_type in aperture_types:
            if aperture_type == 'fixed':
                for radius in radii:
                    phot_table = self.perform_photometry(
                        data, positions, aperture_type, radius, 
                        fwhm, sky_inner, sky_outer, mask, gain, rn, exptime)
                    
                    result_df = stars_in_image.copy()
                    result_df['aperture_type'] = aperture_type
                    result_df['aperture_radius'] = radius
                    result_df['fwhm'] = fwhm
                    result_df['exptime'] = exptime
                    result_df['filter'] = filt
                    result_df['filename'] = Path(fits_file).name

                    # 将 astropy Quantity 列转为普通数值，避免 pandas to_csv 时报错
                    for col in phot_table.colnames:
                        col_data = phot_table[col]
                        if hasattr(col_data, 'value'):
                            result_df[col] = col_data.value
                        else:
                            result_df[col] = np.array(col_data)
                    
                    results.append(result_df)
            
            elif aperture_type == 'fwhm_adaptive':
                phot_table = self.perform_photometry(
                    data, positions, aperture_type, None, 
                    fwhm, sky_inner, sky_outer, mask, gain, rn, exptime)
                
                result_df = stars_in_image.copy()
                result_df['aperture_type'] = aperture_type
                result_df['aperture_radius'] = 1.5 * fwhm
                result_df['fwhm'] = fwhm
                result_df['exptime'] = exptime
                result_df['filter'] = filt
                result_df['filename'] = Path(fits_file).name
                
                for col in phot_table.colnames:
                    col_data = phot_table[col]
                    if hasattr(col_data, 'value'):
                        result_df[col] = col_data.value
                    else:
                        result_df[col] = np.array(col_data)

                results.append(result_df)
        
        return pd.concat(results, ignore_index=True) if results else None

def main():
    parser = argparse.ArgumentParser(description='FITS Aperture Photometry Tool')
    parser.add_argument('--input', '-i', required=True, help='Input FITS file')
    parser.add_argument('--catalog', '-c', required=True, help='Star catalog CSV file')
    parser.add_argument('--output', '-o', help='Output CSV file (default: auto-generated)')
    parser.add_argument('--aperture-types', nargs='+', default=['fixed'], 
                       choices=['fixed', 'fwhm_adaptive', 'elliptical'],
                       help='Aperture types to use')
    parser.add_argument('--radii', nargs='+', type=float, default=[3.0, 5.0, 7.0],
                       help='Fixed aperture radii in pixels')
    parser.add_argument('--sky-inner', type=float, default=10.0,
                       help='Inner radius of sky annulus')
    parser.add_argument('--sky-outer', type=float, default=15.0,
                       help='Outer radius of sky annulus')
    parser.add_argument('--no-mask', action='store_true',
                       help='Disable bad pixel masking')
    parser.add_argument('--gain', type=float, default=1.0,
                       help='CCD gain (e-/ADU)')
    parser.add_argument('--readnoise', type=float, default=5.0,
                       help='CCD readout noise (e-)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize photometry system
    photometry = AperturePhotometry(gain=args.gain, readnoise=args.readnoise)
    
    try:
        # Load star catalog
        catalog = photometry.load_star_catalog(args.catalog)
        logging.info(f"Loaded {len(catalog)} stars from catalog")
        
        # Process image
        results = photometry.process_single_image(
            args.input, catalog, 
            aperture_types=args.aperture_types,
            radii=args.radii,
            sky_inner=args.sky_inner,
            sky_outer=args.sky_outer,
            create_mask=not args.no_mask
        )
        
        if results is not None:
            # Generate output filename if not provided
            if args.output is None:
                input_path = Path(args.input)
                args.output = input_path.stem + '_photometry.csv'
            
            # Save results
            results.to_csv(args.output, index=False)
            logging.info(f"Saved {len(results)} measurements to {args.output}")
            
            # Print summary
            print(f"Processed {len(results)} measurements")
            print(f"Target stars: {len(results[results['star_type'] == 'target'])}")
            print(f"Comparison stars: {len(results[results['star_type'] == 'comparison'])}")
            print(f"Check stars: {len(results[results['star_type'] == 'check'])}")
            
        else:
            print("No measurements obtained")
            sys.exit(1)
            
    except Exception as e:
        import traceback
        logging.error(f"Error processing image: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
