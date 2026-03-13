import numpy as np
import matplotlib.pyplot as plt
import argparse
import json
from pathlib import Path

def validate_healpix_map(temp_map):
    """Validate that input is a proper HEALPix map."""
    npix = len(temp_map)
    nside = int(np.sqrt(npix / 12))
    if 12 * nside**2 != npix:
        raise ValueError(f"Invalid HEALPix map: {npix} pixels doesn't match 12*NSIDE^2")
    return nside

def pixel_to_angles(ipix, nside):
    """Convert HEALPix pixel index to theta, phi angles (RING scheme)."""
    npix = 12 * nside**2
    if ipix >= npix:
        raise ValueError("Pixel index out of range")
    
    # Simplified RING scheme conversion
    ncap = 2 * nside * (nside - 1)
    
    if ipix < ncap:  # North polar cap
        ih = ipix // 2 + 1
        ith = ih
        iph = (ipix % 2) * ih + 1
        theta = np.arccos(1.0 - ith**2 / (3.0 * nside**2))
        phi = (iph - 0.5) * np.pi / (2.0 * ih)
    elif ipix < npix - ncap:  # Equatorial region
        ip = ipix - ncap
        iring = ip // (4 * nside) + nside
        iphi = ip % (4 * nside) + 1
        theta = np.arccos((2 * nside - iring) / (1.5 * nside))
        phi = (iphi - 0.5) * np.pi / (2.0 * nside)
    else:  # South polar cap
        ip = npix - ipix
        ih = ip // 2 + 1
        ith = ih
        theta = np.arccos(-1.0 + ith**2 / (3.0 * nside**2))
        phi = (ip % 2) * ih * np.pi / (2.0 * ih)
    
    return theta, phi

def simplified_spherical_harmonic(l, m, theta, phi):
    """Simplified spherical harmonic calculation for small maps."""
    from scipy.special import sph_harm
    return sph_harm(m, l, phi, theta)

def compute_angular_power_spectrum(temp_map, lmax=None):
    """Compute angular power spectrum from CMB temperature map."""
    nside = validate_healpix_map(temp_map)
    npix = len(temp_map)
    
    if lmax is None:
        lmax = min(3 * nside - 1, int(np.sqrt(npix / 12)))
    
    # Remove monopole and dipole
    temp_map = temp_map - np.mean(temp_map)
    
    # Pre-compute pixel angles
    theta_phi = np.array([pixel_to_angles(i, nside) for i in range(npix)])
    theta = theta_phi[:, 0]
    phi = theta_phi[:, 1]
    
    # Compute power spectrum
    cl = np.zeros(lmax + 1)
    multipoles = np.arange(lmax + 1)
    
    print(f"Computing power spectrum for l = 2 to {lmax}...")
    
    for l in range(2, lmax + 1):
        if l % 10 == 0:
            print(f"Processing l = {l}")
            
        alm_power = 0.0
        for m in range(-l, l + 1):
            # Compute spherical harmonic coefficients
            ylm = simplified_spherical_harmonic(l, m, theta, phi)
            alm = np.sum(temp_map * np.conj(ylm)) * 4 * np.pi / npix
            alm_power += np.abs(alm)**2
        
        # Average over m modes
        cl[l] = alm_power / (2 * l + 1)
    
    return multipoles[2:], cl[2:]

def compute_statistics(multipoles, cl):
    """Compute basic statistical measures."""
    total_power = np.sum(cl)
    peak_idx = np.argmax(cl)
    peak_multipole = multipoles[peak_idx]
    rms_temp = np.sqrt(total_power)
    
    return {
        'total_power': float(total_power),
        'peak_multipole': int(peak_multipole),
        'peak_power': float(cl[peak_idx]),
        'rms_temperature': float(rms_temp)
    }

def plot_power_spectrum(multipoles, cl, output_file):
    """Generate CMB power spectrum plot."""
    # Convert to standard CMB units: l(l+1)Cl/(2π)
    dl = multipoles * (multipoles + 1) * cl / (2 * np.pi)
    
    plt.figure(figsize=(10, 6))
    plt.loglog(multipoles, dl, 'b-', linewidth=1.5)
    plt.xlabel('Multipole l')
    plt.ylabel(r'$\ell(\ell+1)C_\ell/(2\pi)$ [$\mu K^2$]')
    plt.title('CMB Angular Power Spectrum')
    plt.grid(True, alpha=0.3)
    plt.xlim(2, max(multipoles))
    
    # Add cosmological scale annotations
    plt.axvline(x=220, color='r', linestyle='--', alpha=0.7, label='First acoustic peak')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Compute CMB angular power spectrum')
    parser.add_argument('input_file', help='Input NumPy array file (.npy)')
    parser.add_argument('--output-json', default='power_spectrum.json', 
                       help='Output JSON file')
    parser.add_argument('--output-plot', default='power_spectrum.png',
                       help='Output plot file')
    parser.add_argument('--lmax', type=int, help='Maximum multipole')
    
    args = parser.parse_args()
    
    try:
        # Load temperature map
        print(f"Loading CMB temperature map from {args.input_file}")
        temp_map = np.load(args.input_file)
        
        if temp_map.ndim != 1:
            raise ValueError("Input must be 1D HEALPix temperature array")
        
        print(f"Map loaded: {len(temp_map)} pixels")
        
        # Compute power spectrum
        multipoles, cl = compute_angular_power_spectrum(temp_map, args.lmax)
        
        # Compute statistics
        stats = compute_statistics(multipoles, cl)
        print(f"Analysis complete:")
        print(f"  Total power: {stats['total_power']:.2e} μK²")
        print(f"  Peak at l = {stats['peak_multipole']}")
        print(f"  RMS temperature: {stats['rms_temperature']:.2f} μK")
        
        # Save results
        results = {
            'multipoles': multipoles.tolist(),
            'power_spectrum': cl.tolist(),
            'units': 'microkelvin^2',
            'statistics': stats
        }
        
        with open(args.output_json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output_json}")
        
        # Generate plot
        plot_power_spectrum(multipoles, cl, args.output_plot)
        print(f"Plot saved to {args.output_plot}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
