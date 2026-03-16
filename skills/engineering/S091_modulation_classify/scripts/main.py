#!/usr/bin/env python3
"""
Digital Modulation Classification from IQ Samples
"""

import argparse
import json
import logging
import os
import numpy as np
import h5py
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from scipy import signal, stats
from scipy.ndimage import median_filter
import warnings
warnings.filterwarnings('ignore')

class ModulationClassifier:
    def __init__(self):
        self.modulation_types = ['BPSK', 'QPSK', '8PSK', '16QAM', '64QAM']
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.clusterer = KMeans(n_clusters=5, random_state=42)
        self.scaler = StandardScaler()
        self.logger = logging.getLogger(__name__)
        
    def preprocess_signal(self, iq_samples, apply_noise_reduction=True):
        """Apply signal preprocessing including DC removal, normalization, and noise reduction"""
        # Remove DC component
        iq_samples = iq_samples - np.mean(iq_samples)
        
        # Noise reduction using median filtering on amplitude
        if apply_noise_reduction:
            amplitude = np.abs(iq_samples)
            phase = np.angle(iq_samples)
            
            # Apply median filter to amplitude to reduce impulse noise
            filtered_amplitude = median_filter(amplitude, size=3)
            
            # Reconstruct signal
            iq_samples = filtered_amplitude * np.exp(1j * phase)
            
            # Additional smoothing using moving average
            window_size = min(5, len(iq_samples) // 100)
            if window_size > 1:
                kernel = np.ones(window_size) / window_size
                real_smooth = np.convolve(iq_samples.real, kernel, mode='same')
                imag_smooth = np.convolve(iq_samples.imag, kernel, mode='same')
                iq_samples = real_smooth + 1j * imag_smooth
        
        # Automatic gain control - normalize by RMS power
        rms_power = np.sqrt(np.mean(np.abs(iq_samples)**2))
        if rms_power > 0:
            iq_samples = iq_samples / rms_power
            
        return iq_samples
    
    def extract_features(self, iq_samples):
        """Extract signal features for classification"""
        features = {}
        
        # Instantaneous amplitude and phase
        amplitude = np.abs(iq_samples)
        phase = np.angle(iq_samples)
        
        # Unwrap phase to handle discontinuities
        phase_unwrapped = np.unwrap(phase)
        
        # 1. Instantaneous amplitude statistics
        features['amp_mean'] = np.mean(amplitude)
        features['amp_std'] = np.std(amplitude)
        features['amp_skew'] = stats.skew(amplitude)
        features['amp_kurtosis'] = stats.kurtosis(amplitude)
        
        # 2. Instantaneous phase statistics
        phase_diff = np.diff(phase_unwrapped)
        features['phase_mean'] = np.mean(phase_diff)
        features['phase_std'] = np.std(phase_diff)
        features['phase_skew'] = stats.skew(phase_diff)
        features['phase_kurtosis'] = stats.kurtosis(phase_diff)
        
        # 3. Constellation diagram features
        features['constellation_radius_std'] = np.std(amplitude)
        features['constellation_phase_std'] = np.std(phase)
        
        # Error Vector Magnitude (EVM) estimation
        # Estimate ideal constellation points by clustering
        constellation_points = iq_samples[::max(1, len(iq_samples)//1000)]  # Subsample for speed
        
        if len(constellation_points) > 20:  # Need sufficient samples for clustering
            try:
                # Determine appropriate number of clusters based on sample size
                max_clusters = min(8, len(constellation_points) // 3)  # At least 3 samples per cluster
                n_clusters = max(2, max_clusters)  # At least 2 clusters
                
                kmeans_temp = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                cluster_data = np.column_stack([constellation_points.real, constellation_points.imag])
                kmeans_temp.fit(cluster_data)
                centers = kmeans_temp.cluster_centers_[:, 0] + 1j * kmeans_temp.cluster_centers_[:, 1]
                
                # Calculate EVM as average distance to nearest center
                evm_values = []
                for sample in constellation_points:
                    distances = np.abs(sample - centers)
                    evm_values.append(np.min(distances))
                features['evm'] = np.mean(evm_values)
                
            except Exception as e:
                self.logger.debug(f"EVM clustering failed: {e}, using fallback")
                features['evm'] = np.std(amplitude)  # Fallback
        else:
            # Too few samples for clustering, use amplitude std as proxy
            features['evm'] = np.std(amplitude)
        
        # 4. Spectral characteristics
        freqs, psd = signal.periodogram(iq_samples, fs=1.0)
        features['spectral_centroid'] = np.sum(freqs * psd) / np.sum(psd)
        features['spectral_bandwidth'] = np.sqrt(np.sum(((freqs - features['spectral_centroid'])**2) * psd) / np.sum(psd))
        
        # 5. Higher-order moments
        features['moment_4'] = stats.moment(iq_samples.real, moment=4) + stats.moment(iq_samples.imag, moment=4)
        features['moment_6'] = stats.moment(iq_samples.real, moment=6) + stats.moment(iq_samples.imag, moment=6)
        
        # 6. Zero-crossing rate
        real_crossings = np.sum(np.diff(np.sign(iq_samples.real)) != 0)
        imag_crossings = np.sum(np.diff(np.sign(iq_samples.imag)) != 0)
        features['zero_crossing_rate'] = (real_crossings + imag_crossings) / (2 * len(iq_samples))
        
        return features
    
    def classify_modulations(self, all_features):
        """Classify modulations using unsupervised clustering"""
        # Convert features to matrix
        feature_names = list(next(iter(all_features.values())).keys())
        signal_names = list(all_features.keys())
        
        feature_matrix = []
        for signal_name in signal_names:
            feature_vector = [all_features[signal_name][fname] for fname in feature_names]
            feature_matrix.append(feature_vector)
        
        feature_matrix = np.array(feature_matrix)
        
        # Handle NaN values
        feature_matrix = np.nan_to_num(feature_matrix, nan=0.0, posinf=1e6, neginf=-1e6)
        
        # Standardize features
        feature_matrix_scaled = self.scaler.fit_transform(feature_matrix)
        
        # Perform clustering
        cluster_labels = self.clusterer.fit_predict(feature_matrix_scaled)
        
        # Calculate silhouette score for clustering quality
        if len(np.unique(cluster_labels)) > 1:
            silhouette_avg = silhouette_score(feature_matrix_scaled, cluster_labels)
        else:
            silhouette_avg = 0.0
        
        # Map clusters to modulation types (heuristic approach)
        cluster_to_modulation = {}
        for i in range(len(self.modulation_types)):
            if i < len(np.unique(cluster_labels)):
                cluster_to_modulation[i] = self.modulation_types[i]
            else:
                cluster_to_modulation[i] = f'UNKNOWN_{i}'
        
        # Generate results
        results = {}
        for i, signal_name in enumerate(signal_names):
            cluster_id = cluster_labels[i]
            predicted_mod = cluster_to_modulation.get(cluster_id, 'UNKNOWN')
            
            # Calculate confidence based on distance to cluster center
            center = self.clusterer.cluster_centers_[cluster_id]
            distance = np.linalg.norm(feature_matrix_scaled[i] - center)
            confidence = max(0.0, 1.0 - distance / 5.0)  # Normalize distance to confidence
            
            results[signal_name] = {
                'predicted_modulation': predicted_mod,
                'confidence': float(confidence),
                'cluster_id': int(cluster_id)
            }
        
        return results, silhouette_avg
    
    def generate_constellation(self, iq_samples, output_path, signal_name):
        """Generate and save constellation diagram"""
        plt.figure(figsize=(8, 8))
        
        # Subsample for plotting if too many points
        if len(iq_samples) > 5000:
            indices = np.random.choice(len(iq_samples), 5000, replace=False)
            plot_samples = iq_samples[indices]
        else:
            plot_samples = iq_samples
            
        plt.scatter(plot_samples.real, plot_samples.imag, alpha=0.6, s=1)
        plt.xlabel('In-phase')
        plt.ylabel('Quadrature')
        plt.title(f'Constellation Diagram - {signal_name}')
        plt.grid(True)
        plt.axis('equal')
        
        constellation_file = os.path.join(output_path, f'{signal_name}_constellation.png')
        plt.savefig(constellation_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        return constellation_file

def main():
    parser = argparse.ArgumentParser(description='Digital Modulation Classification from IQ Samples')
    parser.add_argument('--input-file', required=True, help='Input HDF5 file containing IQ samples')
    parser.add_argument('--output-file', required=True, help='Output JSON file for classification results')
    parser.add_argument('--features-file', required=True, help='Output JSON file for extracted features')
    parser.add_argument('--constellation-dir', required=True, help='Directory to save constellation diagrams')
    parser.add_argument('--no-noise-reduction', action='store_true', help='Disable noise reduction preprocessing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Create output directory for constellations
    os.makedirs(args.constellation_dir, exist_ok=True)
    
    # Initialize classifier
    classifier = ModulationClassifier()
    
    # Load IQ data from HDF5 file
    logger.info(f"Loading IQ data from {args.input_file}")
    
    try:
        with h5py.File(args.input_file, 'r') as f:
            signal_names = [key for key in f.keys() if key.startswith('signal_')]
            logger.info(f"Found {len(signal_names)} signals in input file")
            
            all_features = {}
            constellation_files = {}
            
            for signal_name in signal_names:
                logger.info(f"Processing {signal_name}")
                
                # Load IQ samples
                iq_data = f[signal_name][:]
                logger.debug(f"Loaded {signal_name}: shape={iq_data.shape}, dtype={iq_data.dtype}")
                
                # Handle different data formats
                if np.iscomplexobj(iq_data):
                    iq_samples = iq_data
                elif iq_data.ndim == 2 and iq_data.shape[1] == 2:
                    iq_samples = iq_data[:, 0] + 1j * iq_data[:, 1]
                elif iq_data.ndim == 1:
                    if len(iq_data) % 2 == 0:
                        iq_samples = iq_data[::2] + 1j * iq_data[1::2]
                    else:
                        raise ValueError(f"Cannot interpret 1D real data format for {signal_name}")
                else:
                    raise ValueError(f"Cannot interpret data format for {signal_name}: shape={iq_data.shape}")
                
                logger.debug(f"Converted to complex samples: {len(iq_samples)} samples")
                
                # Preprocess signal
                apply_nr = not args.no_noise_reduction
                iq_samples = classifier.preprocess_signal(iq_samples, apply_noise_reduction=apply_nr)
                
                # Extract features
                features = classifier.extract_features(iq_samples)
                all_features[signal_name] = features
                
                # Generate constellation diagram
                constellation_file = classifier.generate_constellation(
                    iq_samples, args.constellation_dir, signal_name
                )
                constellation_files[signal_name] = constellation_file
        
        # Perform clustering-based classification
        logger.info("Performing modulation classification using clustering...")
        classification_results, silhouette_avg = classifier.classify_modulations(all_features)
        logger.info(f"Clustering silhouette score: {silhouette_avg:.3f}")
        
        # Add constellation file paths to results
        for signal_name in classification_results:
            classification_results[signal_name]['constellation_file'] = constellation_files[signal_name]
        
        # Add overall metrics
        classification_results['_metadata'] = {
            'silhouette_score': silhouette_avg,
            'num_signals': len(signal_names),
            'noise_reduction_applied': not args.no_noise_reduction
        }
    
    except Exception as e:
        logger.error(f"Error processing input file: {e}")
        return 1
    
    # Save features
    logger.info(f"Saving features to {args.features_file}")
    with open(args.features_file, 'w') as f:
        json.dump(all_features, f, indent=2)
    
    # Save results
    logger.info(f"Saving results to {args.output_file}")
    with open(args.output_file, 'w') as f:
        json.dump(classification_results, f, indent=2)
    
    logger.info("Processing complete!")
    return 0

if __name__ == '__main__':
    exit(main())
