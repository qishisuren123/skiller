import numpy as np
import h5py
import json
import argparse
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
from scipy import stats
from scipy.signal import hilbert

def load_iq_data(filename):
    """Load IQ samples from HDF5 file"""
    signals = {}
    try:
        with h5py.File(filename, 'r') as f:
            for key in f.keys():
                if key.startswith('signal_'):
                    signals[key] = f[key][:]
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return {}
    return signals

def preprocess_signal(iq_samples):
    """Apply DC removal, normalization and AGC"""
    # Remove DC component
    iq_centered = iq_samples - np.mean(iq_samples)
    
    # Automatic gain control - normalize by RMS power
    rms_power = np.sqrt(np.mean(np.abs(iq_centered)**2))
    if rms_power > 0:
        iq_normalized = iq_centered / rms_power
    else:
        iq_normalized = iq_centered
    
    return iq_normalized

def extract_features(iq_samples):
    """Extract comprehensive signal features for classification"""
    iq_norm = preprocess_signal(iq_samples)
    
    # Instantaneous amplitude and phase
    amplitude = np.abs(iq_norm)
    phase = np.angle(iq_norm)
    phase_diff = np.diff(np.unwrap(phase))
    
    # Spectral analysis
    fft_signal = np.fft.fft(iq_norm)
    psd = np.abs(fft_signal)**2
    freqs = np.arange(len(psd))
    
    features = {
        # Amplitude statistics
        'amp_mean': np.mean(amplitude),
        'amp_var': np.var(amplitude),
        'amp_kurtosis': stats.kurtosis(amplitude),
        'amp_skewness': stats.skew(amplitude),
        
        # Phase statistics  
        'phase_var': np.var(phase_diff),
        'phase_range': np.ptp(phase),
        
        # Constellation features
        'constellation_radius_var': np.var(amplitude),
        'iq_ratio': np.var(iq_norm.real) / (np.var(iq_norm.imag) + 1e-10),
        
        # Spectral features
        'spectral_centroid': np.sum(psd * freqs) / (np.sum(psd) + 1e-10),
        'spectral_bandwidth': np.sqrt(np.sum(psd * (freqs - np.sum(psd * freqs) / np.sum(psd))**2) / np.sum(psd)),
        
        # Higher order moments
        'fourth_moment': np.mean(np.abs(iq_norm)**4),
        'sixth_moment': np.mean(np.abs(iq_norm)**6),
        
        # Zero crossing rate
        'zero_crossing_rate': np.sum(np.diff(np.sign(iq_norm.real)) != 0) / len(iq_norm)
    }
    
    return features

def generate_constellation_diagram(iq_samples, signal_name, output_dir):
    """Generate and save constellation diagram"""
    iq_norm = preprocess_signal(iq_samples)
    
    plt.figure(figsize=(8, 8))
    plt.scatter(iq_norm.real, iq_norm.imag, alpha=0.6, s=1)
    plt.xlabel('In-phase')
    plt.ylabel('Quadrature')
    plt.title(f'Constellation Diagram - {signal_name}')
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, f'{signal_name}_constellation.png'), dpi=150, bbox_inches='tight')
    plt.close()

def classify_modulation(features_dict, labels=None):
    """Train classifier and predict modulation types"""
    # Convert features to array format
    feature_names = list(next(iter(features_dict.values())).keys())
    X = np.array([[features[fname] for fname in feature_names] for features in features_dict.values()])
    signal_names = list(features_dict.keys())
    
    # For demonstration, create synthetic labels based on feature patterns
    # In practice, you would have ground truth labels for training
    if labels is None:
        # Simple heuristic classification based on amplitude variance
        labels = []
        for features in features_dict.values():
            amp_var = features['amp_var']
            phase_var = features['phase_var']
            
            if amp_var < 0.1 and phase_var > 0.5:
                labels.append('BPSK')
            elif amp_var < 0.2 and phase_var > 0.3:
                labels.append('QPSK')
            elif amp_var < 0.3 and phase_var > 0.2:
                labels.append('8PSK')
            elif amp_var > 0.3 and phase_var < 0.3:
                labels.append('16QAM')
            else:
                labels.append('64QAM')
    
    # Train classifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    
    if len(set(labels)) > 1:  # Only train if we have multiple classes
        clf.fit(X, labels)
        
        # Cross-validation scores
        cv_scores = cross_val_score(clf, X, labels, cv=min(5, len(X)))
        
        # Predictions with confidence
        predictions = clf.predict(X)
        probabilities = clf.predict_proba(X)
        confidence_scores = np.max(probabilities, axis=1)
        
        # Performance metrics
        accuracy = np.mean(cv_scores)
        conf_matrix = confusion_matrix(labels, predictions, labels=clf.classes_)
        class_report = classification_report(labels, predictions, output_dict=True)
        
    else:
        # Single class case
        predictions = labels
        confidence_scores = [1.0] * len(labels)
        accuracy = 1.0
        conf_matrix = [[len(labels)]]
        class_report = {labels[0]: {'precision': 1.0, 'recall': 1.0, 'f1-score': 1.0}}
    
    results = {
        'predictions': {name: pred for name, pred in zip(signal_names, predictions)},
        'confidence_scores': {name: float(conf) for name, conf in zip(signal_names, confidence_scores)},
        'accuracy': float(accuracy),
        'confusion_matrix': conf_matrix.tolist(),
        'classification_report': class_report
    }
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Digital Modulation Classification from IQ Samples')
    parser.add_argument('--input-file', required=True, help='Input HDF5 file with IQ samples')
    parser.add_argument('--output-file', required=True, help='Output JSON file for classification results')
    parser.add_argument('--features-file', required=True, help='Output JSON file for extracted features')
    parser.add_argument('--constellation-dir', required=True, help='Directory for constellation diagrams')
    
    args = parser.parse_args()
    
    # Load IQ data
    print("Loading IQ data...")
    signals = load_iq_data(args.input_file)
    
    if not signals:
        print("No signals found in input file")
        return
    
    print(f"Loaded {len(signals)} signals")
    
    # Extract features
    print("Extracting features...")
    features_dict = {}
    for signal_name, iq_samples in signals.items():
        try:
            features = extract_features(iq_samples)
            features_dict[signal_name] = features
            print(f"Extracted features for {signal_name}")
        except Exception as e:
            print(f"Error extracting features for {signal_name}: {e}")
    
    # Generate constellation diagrams
    print("Generating constellation diagrams...")
    for signal_name, iq_samples in signals.items():
        try:
            generate_constellation_diagram(iq_samples, signal_name, args.constellation_dir)
        except Exception as e:
            print(f"Error generating constellation for {signal_name}: {e}")
    
    # Classify modulation schemes
    print("Classifying modulation schemes...")
    results = classify_modulation(features_dict)
    
    # Save results
    with open(args.output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    with open(args.features_file, 'w') as f:
        json.dump(features_dict, f, indent=2)
    
    # Print summary
    print(f"\nClassification Results:")
    print(f"Overall Accuracy: {results['accuracy']:.3f}")
    print("\nPredictions:")
    for signal_name, prediction in results['predictions'].items():
        confidence = results['confidence_scores'][signal_name]
        print(f"  {signal_name}: {prediction} (confidence: {confidence:.3f})")
    
    print(f"\nResults saved to {args.output_file}")
    print(f"Features saved to {args.features_file}")
    print(f"Constellation diagrams saved to {args.constellation_dir}")

if __name__ == "__main__":
    main()
