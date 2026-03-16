#!/usr/bin/env python3
"""
Stellar Spectra Classification and Normalization Tool
"""

import numpy as np
import argparse
import logging
import json
import h5py
from pathlib import Path
from scipy import optimize, signal, interpolate
from scipy.stats import norm
import matplotlib.pyplot as plt
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SpectralFeatures:
    """Container for extracted spectral features"""
    h_alpha_ew: float
    h_beta_ew: float
    ca_hk_ew: float
    mg_ew: float
    continuum_slope: float
    snr: float
    line_depths: Dict[str, float]
    uncertainties: Dict[str, float]

@dataclass
class ClassificationResult:
    """Container for classification results"""
    spectral_type: str
    confidence: float
    features: SpectralFeatures
    quality_flags: List[str]
    type_probabilities: Dict[str, float]

class StellarSpectraProcessor:
    def __init__(self):
        # Define key spectral lines (in Angstroms)
        self.spectral_lines = {
            'H_alpha': 6562.8,
            'H_beta': 4861.3,
            'Ca_H': 3968.5,
            'Ca_K': 3933.7,
            'Mg_I': 5183.6
        }
        
        # Spectral type templates (equivalent widths in Angstroms)
        self.spectral_templates = {
            'O': {'H_alpha': 0.5, 'H_beta': 0.8, 'Ca_HK': 0.1, 'Mg_I': 0.1, 'temp_range': (28000, 50000)},
            'B': {'H_alpha': 1.2, 'H_beta': 1.5, 'Ca_HK': 0.2, 'Mg_I': 0.2, 'temp_range': (10000, 28000)},
            'A': {'H_alpha': 2.0, 'H_beta': 2.5, 'Ca_HK': 0.5, 'Mg_I': 0.3, 'temp_range': (7500, 10000)},
            'F': {'H_alpha': 1.5, 'H_beta': 1.8, 'Ca_HK': 1.0, 'Mg_I': 0.8, 'temp_range': (6000, 7500)},
            'G': {'H_alpha': 1.0, 'H_beta': 1.2, 'Ca_HK': 2.0, 'Mg_I': 1.5, 'temp_range': (5200, 6000)},
            'K': {'H_alpha': 0.8, 'H_beta': 0.9, 'Ca_HK': 3.0, 'Mg_I': 2.5, 'temp_range': (3700, 5200)},
            'M': {'H_alpha': 0.6, 'H_beta': 0.5, 'Ca_HK': 2.5, 'Mg_I': 3.0, 'temp_range': (2400, 3700)}
        }
        
        # Classification weights for different features
        self.feature_weights = {
            'balmer_ratio': 0.3,
            'ca_strength': 0.25,
            'mg_strength': 0.2,
            'h_alpha_ew': 0.15,
            'continuum_slope': 0.1
        }

    def generate_synthetic_spectrum(self, wavelength: np.ndarray, spectral_type: str, 
                                  snr: float = 50.0) -> np.ndarray:
        """Generate synthetic stellar spectrum with absorption lines"""
        temp_map = {'O': 30000, 'B': 15000, 'A': 8500, 'F': 6500, 
                   'G': 5500, 'K': 4000, 'M': 3000}
        temp = temp_map.get(spectral_type, 5500)
        
        continuum = np.exp(-6000/temp * (1/wavelength - 1/5500))
        continuum /= np.median(continuum)
        flux = continuum.copy()
        
        template = self.spectral_templates[spectral_type]
        for line_name, line_wave in self.spectral_lines.items():
            if line_wave < wavelength.min() or line_wave > wavelength.max():
                continue
                
            if 'H_' in line_name:
                strength = template['H_alpha'] if 'alpha' in line_name else template['H_beta']
            elif 'Ca_' in line_name:
                strength = template['Ca_HK']
            else:
                strength = template['Mg_I']
            
            line_width = 2.0
            line_profile = strength * np.exp(-0.5 * ((wavelength - line_wave) / line_width)**2)
            flux -= line_profile * continuum
        
        noise_level = np.median(flux) / snr
        noise = np.random.normal(0, noise_level, len(flux))
        flux += noise
        
        return flux

    def fit_continuum(self, wavelength: np.ndarray, flux: np.ndarray, 
                     poly_order: int = 4, sigma_clip: float = 3.0) -> np.ndarray:
        """Fit polynomial continuum avoiding absorption lines"""
        wave_mean = np.mean(wavelength)
        wave_std = np.std(wavelength)
        wavelength_scaled = (wavelength - wave_mean) / wave_std
        
        continuum = flux.copy()
        
        for iteration in range(5):
            try:
                coeffs = np.polyfit(wavelength_scaled, continuum, poly_order)
                fit_continuum = np.polyval(coeffs, wavelength_scaled)
            except (np.linalg.LinAlgError, np.linalg.linalg.LinAlgError) as e:
                logger.warning(f"Polynomial fit failed (iteration {iteration}): {e}")
                if poly_order > 1:
                    poly_order -= 1
                    logger.info(f"Trying lower polynomial order: {poly_order}")
                    try:
                        coeffs = np.polyfit(wavelength_scaled, continuum, poly_order)
                        fit_continuum = np.polyval(coeffs, wavelength_scaled)
                    except:
                        logger.warning("All polynomial fits failed, using median continuum")
                        fit_continuum = np.full_like(continuum, np.median(continuum))
                        break
                else:
                    logger.warning("Using median continuum as fallback")
                    fit_continuum = np.full_like(continuum, np.median(continuum))
                    break
            
            residuals = continuum - fit_continuum
            sigma = np.std(residuals)
            
            if sigma < 1e-10:
                logger.warning("Very small residual sigma, stopping continuum iteration")
                break
            
            mask = residuals > -sigma_clip * sigma
            if np.sum(mask) < len(wavelength) * 0.1:
                logger.warning("Too few points after sigma clipping, stopping")
                break
                
            continuum = flux.copy()
            continuum[~mask] = fit_continuum[~mask]
        
        return fit_continuum

    def normalize_spectrum(self, wavelength: np.ndarray, flux: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Normalize spectrum to continuum"""
        continuum = self.fit_continuum(wavelength, flux)
        continuum_safe = np.where(continuum <= 0, np.median(continuum), continuum)
        normalized_flux = flux / continuum_safe
        return normalized_flux, continuum

    def calculate_equivalent_width(self, wavelength: np.ndarray, normalized_flux: np.ndarray,
                                 line_center: float, window_width: float = 20.0) -> Tuple[float, float]:
        """Calculate equivalent width of absorption line"""
        mask = np.abs(wavelength - line_center) <= window_width
        if np.sum(mask) < 5:
            return 0.0, 0.0
        
        wave_region = wavelength[mask]
        flux_region = normalized_flux[mask]
        
        valid_mask = np.isfinite(flux_region)
        if np.sum(valid_mask) < 3:
            return 0.0, 0.0
            
        wave_region = wave_region[valid_mask]
        flux_region = flux_region[valid_mask]
        
        ew = np.trapz(1.0 - flux_region, wave_region)
        noise_level = np.std(flux_region - np.median(flux_region))
        ew_uncertainty = noise_level * np.sqrt(len(wave_region)) * np.mean(np.diff(wave_region))
        
        return ew, ew_uncertainty

    def calculate_continuum_slope(self, wavelength: np.ndarray, continuum: np.ndarray) -> float:
        """Calculate continuum slope as temperature indicator"""
        try:
            log_continuum = np.log(continuum)
            coeffs = np.polyfit(wavelength, log_continuum, 1)
            slope = coeffs[0]
        except:
            slope = 0.0
        return slope

    def extract_features(self, wavelength: np.ndarray, normalized_flux: np.ndarray, 
                        continuum: np.ndarray, snr: float) -> SpectralFeatures:
        """Extract all spectral features for classification"""
        ew_results = {}
        ew_uncertainties = {}
        line_depths = {}
        
        for line_name, line_wave in self.spectral_lines.items():
            ew, ew_err = self.calculate_equivalent_width(wavelength, normalized_flux, line_wave)
            ew_results[line_name] = ew
            ew_uncertainties[line_name] = ew_err
            
            line_mask = np.abs(wavelength - line_wave) <= 5.0
            if np.sum(line_mask) > 0:
                line_depths[line_name] = 1.0 - np.min(normalized_flux[line_mask])
            else:
                line_depths[line_name] = 0.0
        
        continuum_slope = self.calculate_continuum_slope(wavelength, continuum)
        ca_hk_ew = ew_results.get('Ca_H', 0.0) + ew_results.get('Ca_K', 0.0)
        
        features = SpectralFeatures(
            h_alpha_ew=ew_results.get('H_alpha', 0.0),
            h_beta_ew=ew_results.get('H_beta', 0.0),
            ca_hk_ew=ca_hk_ew,
            mg_ew=ew_results.get('Mg_I', 0.0),
            continuum_slope=continuum_slope,
            snr=snr,
            line_depths=line_depths,
            uncertainties=ew_uncertainties
        )
        
        return features

    def classify_spectrum(self, features: SpectralFeatures) -> ClassificationResult:
        """Classify spectrum based on extracted features"""
        spectral_types = list(self.spectral_templates.keys())
        type_scores = {}
        quality_flags = []
        
        if features.snr < 10:
            quality_flags.append("LOW_SNR")
        if features.h_alpha_ew < 0 or features.h_beta_ew < 0:
            quality_flags.append("NEGATIVE_EW")
        
        for spec_type in spectral_types:
            template = self.spectral_templates[spec_type]
            score = 0.0
            
            if features.h_beta_ew > 0.1:
                balmer_ratio = features.h_alpha_ew / features.h_beta_ew
                template_ratio = template['H_alpha'] / template['H_beta']
                balmer_score = np.exp(-0.5 * ((balmer_ratio - template_ratio) / 0.5)**2)
                score += self.feature_weights['balmer_ratio'] * balmer_score
            
            ca_score = np.exp(-0.5 * ((features.ca_hk_ew - template['Ca_HK']) / 1.0)**2)
            score += self.feature_weights['ca_strength'] * ca_score
            
            mg_score = np.exp(-0.5 * ((features.mg_ew - template['Mg_I']) / 0.8)**2)
            score += self.feature_weights['mg_strength'] * mg_score
            
            h_alpha_score = np.exp(-0.5 * ((features.h_alpha_ew - template['H_alpha']) / 0.6)**2)
            score += self.feature_weights['h_alpha_ew'] * h_alpha_score
            
            expected_slope = -2000.0 / np.mean(template['temp_range'])
            slope_score = np.exp(-0.5 * ((features.continuum_slope - expected_slope) / 0.001)**2)
            score += self.feature_weights['continuum_slope'] * slope_score
            
            type_scores[spec_type] = score
        
        total_score = sum(type_scores.values())
        if total_score > 0:
            type_probabilities = {k: v/total_score for k, v in type_scores.items()}
        else:
            type_probabilities = {k: 1.0/len(spectral_types) for k in spectral_types}
        
        best_type = max(type_probabilities, key=type_probabilities.get)
        confidence = type_probabilities[best_type]
        
        if confidence < 0.3:
            quality_flags.append("LOW_CONFIDENCE")
        
        result = ClassificationResult(
            spectral_type=best_type,
            confidence=confidence,
            features=features,
            quality_flags=quality_flags,
            type_probabilities=type_probabilities
        )
        
        return result

    def estimate_snr(self, flux: np.ndarray) -> float:
        """Estimate signal-to-noise ratio of spectrum"""
        median_flux = np.median(flux)
        mad = np.median(np.abs(flux - median_flux))
        noise_estimate = 1.4826 * mad
        
        if noise_estimate == 0:
            return float('inf')
        
        snr = median_flux / noise_estimate
        return max(snr, 0.1)

def main():
    parser = argparse.ArgumentParser(description='Stellar Spectra Classification and Normalization')
    parser.add_argument('--output-dir', '-o', type=str, default='./output',
                       help='Output directory for results')
    parser.add_argument('--wave-min', type=float, default=3500.0,
                       help='Minimum wavelength (Angstroms)')
    parser.add_argument('--wave-max', type=float, default=7000.0,
                       help='Maximum wavelength (Angstroms)')
    parser.add_argument('--n-spectra', type=int, default=5,
                       help='Number of synthetic spectra to generate')
    parser.add_argument('--snr', type=float, default=50.0,
                       help='Signal-to-noise ratio for synthetic spectra')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    processor = StellarSpectraProcessor()
    wavelength = np.linspace(args.wave_min, args.wave_max, 2000)
    
    results = []
    spectral_types = ['O', 'B', 'A', 'F', 'G', 'K', 'M']
    
    logger.info(f"Generating and processing {args.n_spectra} synthetic spectra...")
    
    for i in range(args.n_spectra):
        spec_type = np.random.choice(spectral_types)
        logger.info(f"Processing spectrum {i+1}: {spec_type} type")
        
        try:
            flux = processor.generate_synthetic_spectrum(wavelength, spec_type, args.snr)
            normalized_flux, continuum = processor.normalize_spectrum(wavelength, flux)
            estimated_snr = processor.estimate_snr(flux)
            
            features = processor.extract_features(wavelength, normalized_flux, continuum, estimated_snr)
            classification = processor.classify_spectrum(features)
            
            output_file = output_dir / f'spectrum_{i+1:03d}_normalized.h5'
            with h5py.File(output_file, 'w') as f:
                f.create_dataset('wavelength', data=wavelength)
                f.create_dataset('normalized_flux', data=normalized_flux)
                f.create_dataset('original_flux', data=flux)
                f.create_dataset('continuum', data=continuum)
                f.attrs['spectral_type'] = spec_type
                f.attrs['input_snr'] = args.snr
                f.attrs['estimated_snr'] = estimated_snr
                f.attrs['classified_type'] = classification.spectral_type
                f.attrs['confidence'] = classification.confidence
            
            result = {
                'spectrum_id': i+1,
                'true_spectral_type': spec_type,
                'classified_type': classification.spectral_type,
                'confidence': classification.confidence,
                'type_probabilities': classification.type_probabilities,
                'equivalent_widths': {
                    'H_alpha': features.h_alpha_ew,
                    'H_beta': features.h_beta_ew,
                    'Ca_HK': features.ca_hk_ew,
                    'Mg_I': features.mg_ew
                },
                'quality_flags': classification.quality_flags,
                'input_snr': args.snr,
                'estimated_snr': estimated_snr
            }
            results.append(result)
            
            logger.info(f"Classified as {classification.spectral_type} (confidence: {classification.confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to process spectrum {i+1}: {e}")
            continue
    
    results_file = output_dir / 'classification_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Processing complete. Results saved to {output_dir}")

if __name__ == '__main__':
    main()
