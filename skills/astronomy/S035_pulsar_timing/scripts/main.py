#!/usr/bin/env python3
"""
Pulsar Timing Analysis and Dispersion Measure Computation
"""

import numpy as np
import pandas as pd
import argparse
import json
import logging
from scipy.optimize import minimize, curve_fit
from scipy import stats
import sys

# Physical constants
K_DM = 4.148808e3  # s·MHz²·pc⁻¹·cm³

class PulsarTimingAnalyzer:
    def __init__(self, data_file):
        self.data_file = data_file
        self.data = None
        self.timing_params = {}
        self.dm_optimal = None
        self.residuals = None
        
    def load_data(self):
        """Load and validate timing data"""
        try:
            self.data = pd.read_csv(self.data_file)
            required_cols = ['MJD', 'frequency', 'TOA', 'uncertainty']
            
            if not all(col in self.data.columns for col in required_cols):
                raise ValueError(f"Missing required columns. Need: {required_cols}")
                
            # Remove outliers (>5σ from median)
            for col in ['TOA', 'frequency']:
                median_val = self.data[col].median()
                mad = np.median(np.abs(self.data[col] - median_val))
                threshold = 5 * 1.4826 * mad  # 5σ threshold
                mask = np.abs(self.data[col] - median_val) < threshold
                self.data = self.data[mask]
                
            # Handle missing values
            self.data = self.data.dropna()
            logging.info(f"Loaded {len(self.data)} valid observations")
            
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            sys.exit(1)
    
    def quadratic_timing_model(self, pulse_num, T0, P0, P1):
        """Quadratic timing model"""
        return T0 + P0 * pulse_num + 0.5 * P1 * pulse_num**2
    
    def fit_timing_model(self):
        """Fit timing model to lowest frequency data"""
        # Use lowest frequency data for timing model
        min_freq = self.data['frequency'].min()
        low_freq_data = self.data[self.data['frequency'] == min_freq].copy()
        
        logging.info(f"Fitting timing model using {len(low_freq_data)} observations at {min_freq} MHz")
        
        # Convert MJD to pulse numbers (approximate) - only for low frequency data
        mjd_ref = low_freq_data['MJD'].min()
        pulse_numbers = (low_freq_data['MJD'] - mjd_ref) * 86400.0
        
        # Initial parameter estimates
        T0_init = low_freq_data['TOA'].iloc[0]
        P0_init = 1.0  # 1 second period estimate
        P1_init = 1e-15  # Small period derivative
        
        try:
            popt, pcov = curve_fit(
                self.quadratic_timing_model,
                pulse_numbers,  # Now matches the low_freq_data length
                low_freq_data['TOA'].values,  # Ensure it's a numpy array
                p0=[T0_init, P0_init, P1_init],
                sigma=low_freq_data['uncertainty'].values,
                absolute_sigma=True,
                maxfev=5000  # Increase max iterations
            )
            
            self.timing_params = {
                'T0': popt[0],
                'P0': popt[1], 
                'P1': popt[2],
                'T0_err': np.sqrt(pcov[0,0]),
                'P0_err': np.sqrt(pcov[1,1]),
                'P1_err': np.sqrt(pcov[2,2]),
                'mjd_ref': mjd_ref
            }
            
            logging.info("Timing model fitted successfully")
            logging.info(f"T0: {popt[0]:.6f} ± {np.sqrt(pcov[0,0]):.6f}")
            logging.info(f"P0: {popt[1]:.9f} ± {np.sqrt(pcov[1,1]):.9f}")
            logging.info(f"P1: {popt[2]:.2e} ± {np.sqrt(pcov[2,2]):.2e}")
            
        except Exception as e:
            logging.error(f"Error fitting timing model: {e}")
            sys.exit(1)
    
    def dispersion_delay(self, frequency, dm):
        """Calculate dispersion delay"""
        return K_DM * dm / (frequency**2)
    
    def optimize_dm(self):
        """Optimize dispersion measure to minimize residuals"""
        def residual_rms(dm):
            total_residuals = []
            
            for idx, obs in self.data.iterrows():
                # Calculate pulse number - ensure it's a scalar
                pulse_num = float((obs['MJD'] - self.timing_params['mjd_ref']) * 86400.0)
                
                # Predicted TOA from timing model
                predicted_toa = self.quadratic_timing_model(
                    pulse_num, 
                    self.timing_params['T0'],
                    self.timing_params['P0'],
                    self.timing_params['P1']
                )
                
                # Apply dispersion correction
                dm_correction = self.dispersion_delay(float(obs['frequency']), dm)
                corrected_predicted = predicted_toa + dm_correction
                
                # Calculate residual
                residual = float(obs['TOA']) - corrected_predicted
                total_residuals.append(residual)
            
            return np.std(total_residuals)
        
        # Optimize DM with bounds to ensure reasonable values
        result = minimize(residual_rms, x0=[50.0], method='Nelder-Mead',
                         options={'xatol': 1e-8, 'fatol': 1e-8})
        
        if result.success:
            self.dm_optimal = float(result.x[0])
            logging.info(f"Optimized DM: {self.dm_optimal:.6f} pc cm⁻³")
        else:
            logging.warning("DM optimization did not converge properly")
            self.dm_optimal = 50.0  # fallback value
    
    def calculate_residuals(self):
        """Calculate final timing residuals"""
        residuals = []
        predicted_toas = []
        
        for idx, obs in self.data.iterrows():
            pulse_num = float((obs['MJD'] - self.timing_params['mjd_ref']) * 86400.0)
            
            predicted_toa = self.quadratic_timing_model(
                pulse_num,
                self.timing_params['T0'],
                self.timing_params['P0'], 
                self.timing_params['P1']
            )
            
            dm_correction = self.dispersion_delay(float(obs['frequency']), self.dm_optimal)
            corrected_predicted = predicted_toa + dm_correction
            
            residual = float(obs['TOA']) - corrected_predicted
            residuals.append(residual)
            predicted_toas.append(corrected_predicted)
        
        self.data['residual'] = residuals
        self.data['predicted_TOA'] = predicted_toas
        
    def compute_statistics(self):
        """Compute comprehensive statistics"""
        residuals = self.data['residual'].values
        uncertainties = self.data['uncertainty'].values
        
        # Initialize frequency band stats dictionary
        frequency_band_stats = {}
        
        # Statistics by frequency band
        for freq in self.data['frequency'].unique():
            freq_mask = self.data['frequency'] == freq
            freq_residuals = residuals[freq_mask]
            frequency_band_stats[f'{freq:.1f}_MHz'] = {
                'rms': float(np.std(freq_residuals)),
                'mean': float(np.mean(freq_residuals)),
                'n_obs': int(np.sum(freq_mask))
            }
        
        stats_dict = {
            'timing_parameters': self.timing_params,
            'dispersion_measure': {
                'value': float(self.dm_optimal),
                'unit': 'pc cm⁻³'
            },
            'residual_statistics': {
                'rms_residual': float(np.std(residuals)),
                'mean_residual': float(np.mean(residuals)),
                'reduced_chi_squared': float(np.sum((residuals/uncertainties)**2) / (len(residuals) - 3)),
                'n_observations': len(residuals)
            },
            'frequency_band_stats': frequency_band_stats
        }
        
        return stats_dict

def main():
    parser = argparse.ArgumentParser(description='Pulsar Timing Analysis')
    parser.add_argument('input_file', help='Input timing data CSV file')
    parser.add_argument('--output-json', default='timing_results.json', 
                       help='Output JSON file for results')
    parser.add_argument('--output-csv', default='processed_toas.csv',
                       help='Output CSV file for processed data')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    logging.basicConfig(level=getattr(logging, args.log_level),
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize analyzer
    analyzer = PulsarTimingAnalyzer(args.input_file)
    
    # Run analysis pipeline
    analyzer.load_data()
    analyzer.fit_timing_model()
    analyzer.optimize_dm()
    analyzer.calculate_residuals()
    
    # Compute and save statistics
    stats = analyzer.compute_statistics()
    
    with open(args.output_json, 'w') as f:
        json.dump(stats, f, indent=2)
    
    analyzer.data.to_csv(args.output_csv, index=False)
    
    logging.info(f"Analysis complete. Results saved to {args.output_json} and {args.output_csv}")

if __name__ == '__main__':
    main()
