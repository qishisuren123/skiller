#!/usr/bin/env python3
"""
Spectral Leakage Analysis and Correction Tool
Analyzes spectral leakage effects and applies windowing functions to minimize artifacts.
"""

import numpy as np
import argparse
import logging
import h5py
import json
from scipy import signal
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any

class SpectralLeakageAnalyzer:
    def __init__(self, sample_rate: float = 1000.0, duration: float = 1.0):
        self.sample_rate = sample_rate
        self.duration = duration
        self.n_samples = int(sample_rate * duration)
        self.time = np.linspace(0, duration, self.n_samples, endpoint=False)
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def generate_composite_signal(self, frequencies: List[float], 
                                amplitudes: List[float], 
                                phases: List[float] = None,
                                noise_level: float = 0.0) -> np.ndarray:
        """Generate composite test signal with multiple sinusoidal components"""
        if phases is None:
            phases = [0.0] * len(frequencies)
            
        if len(frequencies) != len(amplitudes) or len(frequencies) != len(phases):
            raise ValueError("Frequencies, amplitudes, and phases must have same length")
        
        signal_data = np.zeros(self.n_samples, dtype=np.float64)
        
        for freq, amp, phase in zip(frequencies, amplitudes, phases):
            component = amp * np.sin(2 * np.pi * freq * self.time + phase)
            signal_data += component
            
        # Add white noise if specified
        if noise_level > 0:
            noise = np.random.normal(0, noise_level, self.n_samples)
            signal_data += noise
            
        self.logger.info(f"Generated signal with {len(frequencies)} components, "
                        f"noise level: {noise_level}")
        return signal_data
    
    def get_window_functions(self, window_length: int, kaiser_beta: float = 8.6) -> Dict[str, np.ndarray]:
        """Generate various windowing functions"""
        windows = {
            'rectangular': np.ones(window_length, dtype=np.float64),
            'hann': signal.windows.hann(window_length).astype(np.float64),
            'hamming': signal.windows.hamming(window_length).astype(np.float64),
            'blackman': signal.windows.blackman(window_length).astype(np.float64),
            'kaiser': signal.windows.kaiser(window_length, kaiser_beta).astype(np.float64)
        }
        return windows
    
    def analyze_window_characteristics(self, window: np.ndarray, 
                                     window_name: str) -> Dict[str, float]:
        """Analyze window characteristics including main lobe width and side lobe suppression"""
        # Compute window FFT for analysis
        window_fft = fft(window, n=len(window)*4)  # Zero-pad for better resolution
        window_magnitude = np.abs(window_fft)
        
        # Avoid division by zero and log of zero
        max_magnitude = np.max(window_magnitude)
        if max_magnitude == 0:
            max_magnitude = 1e-12
            
        normalized_magnitude = window_magnitude / max_magnitude
        # Clamp to avoid log(0)
        normalized_magnitude = np.maximum(normalized_magnitude, 1e-12)
        window_db = 20 * np.log10(normalized_magnitude)
        
        # Find main lobe width (first nulls on either side of peak)
        peak_idx = np.argmax(window_magnitude)
        
        # Find first null to the right - be more careful about bounds
        right_null = len(window_magnitude) // 2  # Default to end if no null found
        threshold = 0.01 * max_magnitude
        
        for i in range(peak_idx + 1, len(window_magnitude) // 2):
            if window_magnitude[i] < threshold:
                right_null = i
                break
                
        # Calculate main lobe width in normalized frequency units
        main_lobe_width = 2 * (right_null - peak_idx) / len(window_fft)
        
        # Find maximum side lobe level - handle empty region case
        half_length = len(window_db) // 2
        if right_null < half_length:
            side_lobe_region = window_db[right_null:half_length]
            max_side_lobe_db = np.max(side_lobe_region) if len(side_lobe_region) > 0 else -np.inf
        else:
            max_side_lobe_db = -np.inf  # No side lobes detected
        
        # Calculate processing gain and effective noise bandwidth
        coherent_gain = np.sum(window) / len(window)
        processing_gain = coherent_gain ** 2
        
        # Avoid division by zero in ENBW calculation
        window_sum = np.sum(window)
        if window_sum == 0:
            enbw = len(window)
        else:
            enbw = len(window) * np.sum(window**2) / (window_sum**2)
        
        return {
            'main_lobe_width': float(main_lobe_width),
            'max_side_lobe_db': float(max_side_lobe_db),
            'coherent_gain': float(coherent_gain),
            'processing_gain': float(processing_gain),
            'enbw': float(enbw)
        }
    
    def compute_power_spectral_density(self, signal_data: np.ndarray, 
                                     window: np.ndarray = None,
                                     fft_size: int = None) -> Tuple[np.ndarray, np.ndarray]:
        """Compute power spectral density using FFT"""
        # Ensure signal_data is 1D and proper dtype
        signal_data = np.asarray(signal_data, dtype=np.float64).flatten()
        
        if window is not None:
            window = np.asarray(window, dtype=np.float64).flatten()
            
            if len(signal_data) != len(window):
                raise ValueError(f"Signal length ({len(signal_data)}) != Window length ({len(window)})")
            
            windowed_signal = signal_data * window
        else:
            windowed_signal = signal_data.copy()
            
        if fft_size is None:
            fft_size = len(windowed_signal)
            
        # Compute FFT
        fft_result = fft(windowed_signal, n=fft_size)
        
        # Compute power spectral density
        psd = np.abs(fft_result) ** 2
        
        # Normalize by sampling rate and window power
        if window is not None:
            window_power = np.sum(window ** 2)
            if window_power > 0:
                psd = psd / (self.sample_rate * window_power)
            else:
                psd = psd / self.sample_rate
        else:
            psd = psd / (self.sample_rate * len(windowed_signal))
            
        # Generate frequency axis
        freqs = fftfreq(fft_size, 1/self.sample_rate)
        
        return freqs[:fft_size//2], psd[:fft_size//2]
    
    def quantify_spectral_leakage(self, freqs: np.ndarray, psd: np.ndarray, 
                                true_frequencies: List[float], 
                                leakage_bandwidth: float = None) -> Dict[str, Any]:
        """Quantify spectral leakage around true frequency components"""
        if leakage_bandwidth is None:
            freq_resolution = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
            leakage_bandwidth = freq_resolution * 10  # 10 bins around peak
            
        leakage_metrics = {}
        
        for i, true_freq in enumerate(true_frequencies):
            # Find the peak near the true frequency
            freq_mask = np.abs(freqs - true_freq) <= leakage_bandwidth
            if not np.any(freq_mask):
                continue
                
            local_freqs = freqs[freq_mask]
            local_psd = psd[freq_mask]
            
            if len(local_psd) == 0:
                continue
                
            # Find peak in the local region
            peak_idx = np.argmax(local_psd)
            peak_freq = local_freqs[peak_idx]
            peak_power = local_psd[peak_idx]
            
            # Define main lobe region (±3 bins around peak)
            freq_resolution = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
            main_lobe_mask = np.abs(local_freqs - peak_freq) <= 3 * freq_resolution
            
            # Calculate power in main lobe vs side lobes
            main_lobe_power = np.sum(local_psd[main_lobe_mask])
            total_power = np.sum(local_psd)
            side_lobe_power = total_power - main_lobe_power
            
            # Calculate spectral leakage ratio
            leakage_ratio = side_lobe_power / main_lobe_power if main_lobe_power > 0 else np.inf
            
            leakage_metrics[f'freq_{true_freq}Hz'] = {
                'true_frequency': true_freq,
                'peak_frequency': peak_freq,
                'frequency_error': peak_freq - true_freq,
                'peak_power': float(peak_power),
                'main_lobe_power': float(main_lobe_power),
                'side_lobe_power': float(side_lobe_power),
                'total_power': float(total_power),
                'leakage_ratio': float(leakage_ratio),
                'leakage_ratio_db': float(10 * np.log10(leakage_ratio)) if leakage_ratio > 0 else -np.inf
            }
            
        return leakage_metrics
    
    def analyze_spectral_leakage(self, signal_data: np.ndarray, 
                               true_frequencies: List[float],
                               fft_size: int = None,
                               kaiser_beta: float = 8.6) -> Dict[str, Any]:
        """Complete spectral leakage analysis with different windows"""
        results = {}
        
        # Get all window functions
        windows = self.get_window_functions(len(signal_data), kaiser_beta)
        
        for window_name, window in windows.items():
            self.logger.info(f"Analyzing {window_name} window...")
            
            # Compute PSD
            freqs, psd = self.compute_power_spectral_density(signal_data, window, fft_size)
            
            # Quantify leakage
            leakage_metrics = self.quantify_spectral_leakage(freqs, psd, true_frequencies)
            
            # Analyze window characteristics
            window_chars = self.analyze_window_characteristics(window, window_name)
            
            results[window_name] = {
                'frequencies': freqs,
                'psd': psd,
                'leakage_metrics': leakage_metrics,
                'window_characteristics': window_chars,
                'window_function': window
            }
            
        return results
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save analysis results to HDF5 file"""
        with h5py.File(output_path, 'w') as f:
            for window_name, data in results.items():
                grp = f.create_group(window_name)
                grp.create_dataset('frequencies', data=data['frequencies'])
                grp.create_dataset('psd', data=data['psd'])
                grp.create_dataset('window_function', data=data['window_function'])
                
                # Save window characteristics
                char_grp = grp.create_group('window_characteristics')
                for key, value in data['window_characteristics'].items():
                    char_grp.attrs[key] = value
                
                # Save leakage metrics
                leak_grp = grp.create_group('leakage_metrics')
                for freq_key, metrics in data['leakage_metrics'].items():
                    freq_grp = leak_grp.create_group(freq_key)
                    for key, value in metrics.items():
                        freq_grp.attrs[key] = value

def main():
    parser = argparse.ArgumentParser(description='Spectral Leakage Analysis Tool')
    parser.add_argument('--frequencies', nargs='+', type=float, default=[50.0, 120.0, 200.0],
                       help='Signal frequencies in Hz')
    parser.add_argument('--amplitudes', nargs='+', type=float, default=[1.0, 0.7, 0.5],
                       help='Signal amplitudes')
    parser.add_argument('--phases', nargs='+', type=float, default=None,
                       help='Signal phases in radians')
    parser.add_argument('--noise-level', type=float, default=0.1,
                       help='White noise level (standard deviation)')
    parser.add_argument('--sample-rate', type=float, default=1000.0,
                       help='Sample rate in Hz')
    parser.add_argument('--duration', type=float, default=2.0,
                       help='Signal duration in seconds')
    parser.add_argument('--fft-size', type=int, default=None,
                       help='FFT size (default: signal length)')
    parser.add_argument('--kaiser-beta', type=float, default=8.6,
                       help='Kaiser window beta parameter')
    parser.add_argument('--output', type=str, default='spectral_analysis.h5',
                       help='Output HDF5 file path')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = SpectralLeakageAnalyzer(args.sample_rate, args.duration)
    
    # Generate test signal
    test_signal = analyzer.generate_composite_signal(
        args.frequencies, args.amplitudes, args.phases, args.noise_level
    )
    
    # Perform complete spectral leakage analysis
    results = analyzer.analyze_spectral_leakage(
        test_signal, args.frequencies, args.fft_size, args.kaiser_beta
    )
    
    # Save results
    analyzer.save_results(results, args.output)
    
    # Print summary results
    print("\n" + "="*60)
    print("SPECTRAL LEAKAGE ANALYSIS SUMMARY")
    print("="*60)
    
    for window_name, data in results.items():
        print(f"\n{window_name.upper()} WINDOW:")
        print("-" * 40)
        
        leakage_metrics = data['leakage_metrics']
        for freq_key, metrics in leakage_metrics.items():
            print(f"  {freq_key}:")
            print(f"    Frequency Error: {metrics['frequency_error']:.3f} Hz")
            print(f"    Leakage Ratio: {metrics['leakage_ratio_db']:.2f} dB")
            print(f"    Peak Power: {10*np.log10(metrics['peak_power']):.2f} dB")

if __name__ == "__main__":
    main()
