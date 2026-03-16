#!/usr/bin/env python3
"""
CMB Angular Power Spectrum Analysis Tool
Computes angular power spectrum from CMB temperature maps using spherical harmonic analysis.
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import argparse
import logging
import sys

try:
    import healpy as hp
except ImportError:
    print("Error: healpy is required for efficient spherical harmonic transforms.")
    print("Install with: pip install healpy")
    sys.exit(1)

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_cmb_map(filepath):
    """Load CMB temperature map from numpy file."""
    logging.info(f"Loading CMB map from {filepath}")
    try:
        temp_map = np.load(filepath)
        logging.info(f"Loaded map with {len(temp_map)} pixels")
        
        # Validate HEALPix format
        npix = len(temp_map)
        nside = hp.npix2nside(npix)
        logging.info(f"Detected NSIDE = {nside}")
        
        return temp_map, nside
    except Exception as e:
        logging.error(f"Error loading file: {e}")
        sys.exit(1)

def compute_power_spectrum_healpy(temp_map, nside, lmax=None):
    """Compute angular power spectrum using healpy's optimized transforms."""
    if lmax is None:
        lmax = 3 * nside - 1  # Standard HEALPix limit
    
    logging.info(f"Computing spherical harmonics up to l_max = {lmax}")
    
    # Remove monopole and dipole (l=0,1) by default in cosmological analysis
    temp_map_processed = hp.remove_monopole(temp_map, fitval=True)
    
    # Compute spherical harmonic coefficients using healpy's fast transform
    alm = hp.map2alm(temp_map_processed, lmax=lmax, iter=3)
    
    # Convert alm to power spectrum
    # hp.alm2cl returns C_l for l = 0, 1, 2, ..., lmax
    cl_full = hp.alm2cl(alm)
    
    logging.info(f"Full C_l array has {len(cl_full)} elements (l=0 to l={len(cl_full)-1})")
    logging.info(f"C_l[0] (monopole) = {cl_full[0]:.2e}")
    logging.info(f"C_l[1] (dipole) = {cl_full[1]:.2e}")
    
    # Extract only l >= 2 and corresponding C_l values
    # cl_full[l] corresponds to multipole l
    l_start = 2
    l_end = min(lmax + 1, len(cl_full))
    
    l_values = np.arange(l_start, l_end)
    cl_output = cl_full[l_start:l_end]
    
    logging.info(f"Extracted C_l for l = {l_values[0]} to {l_values[-1]}")
    logging.info(f"Non-zero C_l values: {np.sum(cl_output > 0)} out of {len(cl_output)}")
    
    return l_values, cl_output

def compute_statistics(cl, l_values):
    """Compute basic statistics from power spectrum."""
    # Filter out any NaN or infinite values, but keep small positive values
    valid_mask = np.isfinite(cl) & (cl >= 0)  # Allow zero values for now
    cl_valid = cl[valid_mask]
    l_valid = l_values[valid_mask]
    
    if len(cl_valid) == 0:
        logging.warning("No valid power spectrum values found")
        return {
            'total_power': 0.0,
            'peak_multipole': 0,
            'rms_temperature': 0.0,
            'zero_fraction': 1.0
        }
    
    # Calculate statistics
    total_power = np.sum(cl_valid)
    zero_fraction = np.sum(cl_valid == 0) / len(cl_valid)
    
    # Find peak among non-zero values
    nonzero_mask = cl_valid > 0
    if np.any(nonzero_mask):
        peak_idx = np.argmax(cl_valid[nonzero_mask])
        peak_l = l_valid[nonzero_mask][peak_idx]
    else:
        peak_l = l_valid[0]
    
    rms_temp = np.sqrt(total_power)
    
    logging.info(f"Power spectrum statistics: {zero_fraction:.1%} zeros, peak at l={peak_l}")
    
    return {
        'total_power': float(total_power),
        'peak_multipole': int(peak_l),
        'rms_temperature': float(rms_temp),
        'zero_fraction': float(zero_fraction)
    }

def save_results(l_values, cl, stats, output_file):
    """Save results to JSON file."""
    results = {
        'multipoles': l_values.tolist(),
        'power_spectrum': cl.tolist(),
        'statistics': stats,
        'units': 'microkelvin^2'
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Results saved to {output_file}")

def create_plot(l_values, cl, plot_file):
    """Create and save power spectrum plot."""
    logging.info(f"Creating plot with {len(l_values)} l-values and {len(cl)} C_l values")
    
    # Ensure arrays are numpy arrays with proper types
    l_values = np.asarray(l_values, dtype=np.float64)
    cl = np.asarray(cl, dtype=np.float64)
    
    # Debug information
    logging.info(f"l_values shape: {l_values.shape}, cl shape: {cl.shape}")
    logging.info(f"l_values range: {l_values.min():.1f} to {l_values.max():.1f}")
    logging.info(f"cl range: {cl.min():.2e} to {cl.max():.2e}")
    
    # Filter out invalid values for plotting (keep positive values only for log plot)
    valid_mask = np.isfinite(cl) & (cl > 0) & np.isfinite(l_values)
    l_plot = l_values[valid_mask]
    cl_plot = cl[valid_mask]
    
    logging.info(f"After filtering: {len(l_plot)} valid points for plotting")
    
    if len(l_plot) == 0:
        logging.error("No valid data points for plotting")
        return
    
    # Convert to standard CMB plot format: l(l+1)C_l/(2π)
    dl = l_plot * (l_plot + 1) * cl_plot / (2 * np.pi)
    
    plt.figure(figsize=(10, 6))
    
    # Use linear plot if not enough decades for log scale
    if l_plot.max() / l_plot.min() > 10 and dl.max() / dl.min() > 10:
        plt.loglog(l_plot, dl, 'b-', linewidth=2, marker='o', markersize=3)
    else:
        plt.plot(l_plot, dl, 'b-', linewidth=2, marker='o', markersize=3)
        plt.yscale('log')
    
    plt.xlabel('Multipole $\\ell$')
    plt.ylabel(r'$\ell(\ell+1)C_\ell/(2\pi)$ [$\mu K^2$]')
    plt.title('CMB Angular Power Spectrum')
    plt.grid(True, alpha=0.3)
    
    if len(l_plot) > 1:
        plt.xlim(l_plot[0] * 0.9, l_plot[-1] * 1.1)
    
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Plot saved to {plot_file}")

def main():
    parser = argparse.ArgumentParser(description='CMB Angular Power Spectrum Analysis')
    parser.add_argument('input_file', help='Input numpy file with CMB temperature map')
    parser.add_argument('--output-json', default='power_spectrum.json', 
                       help='Output JSON file for results')
    parser.add_argument('--output-plot', default='power_spectrum.png',
                       help='Output plot file')
    parser.add_argument('--lmax', type=int, help='Maximum multipole (auto if not specified)')
    
    args = parser.parse_args()
    
    setup_logging()
    
    # Load temperature map
    temp_map, nside = load_cmb_map(args.input_file)
    
    # Determine lmax
    lmax = args.lmax if args.lmax else min(3 * nside - 1, 100)  # Cap at 100 for reasonable performance
    logging.info(f"Using l_max = {lmax}")
    
    # Compute power spectrum using healpy
    l_values, cl = compute_power_spectrum_healpy(temp_map, nside, lmax)
    
    # Compute statistics
    stats = compute_statistics(cl, l_values)
    
    # Save results and create plot
    save_results(l_values, cl, stats, args.output_json)
    create_plot(l_values, cl, args.output_plot)
    
    logging.info("Analysis complete!")
    logging.info(f"Statistics: Total power = {stats['total_power']:.2e} μK², "
                f"Peak at l = {stats['peak_multipole']}, "
                f"RMS = {stats['rms_temperature']:.2f} μK")

if __name__ == "__main__":
    main()
