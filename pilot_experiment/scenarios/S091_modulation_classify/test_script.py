import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import h5py
import json
import subprocess
import tempfile
import os
import shutil
from scipy import signal, stats
from scipy.fft import fft, fftfreq
import warnings
warnings.filterwarnings('ignore')

def create_data(temp_dir):
    """Generate synthetic IQ data for different modulation schemes"""
    np.random.seed(42)
    
    # Parameters
    fs = 1000  # Sample rate
    fc = 100   # Carrier frequency
    n_samples = 2048
    n_signals_per_mod = 10
    
    modulations = ['BPSK', 'QPSK', '8PSK', '16QAM', '64QAM']
    
    input_file = os.path.join(temp_dir, 'iq_signals.h5')
    
    with h5py.File(input_file, 'w') as f:
        signal_idx = 0
        ground_truth = {}
        
        for mod_type in modulations:
            for i in range(n_signals_per_mod):
                # Generate random data bits
                n_bits = 1024
                data_bits = np.random.randint(0, 2, n_bits)
                
                # Generate modulated signal based on type
                if mod_type == 'BPSK':
                    symbols = 2 * data_bits - 1  # Map to -1, 1
                    iq_signal = symbols.repeat(n_samples // len(symbols))
                elif mod_type == 'QPSK':
                    # Group bits into pairs
                    symbol_map = {0: 1+1j, 1: -1+1j, 2: -1-1j, 3: 1-1j}
                    symbols = []
                    for j in range(0, len(data_bits)-1, 2):
                        sym_idx = data_bits[j] * 2 + data_bits[j+1]
                        symbols.append(symbol_map[sym_idx])
                    symbols = np.array(symbols)
                    iq_signal = np.repeat(symbols, n_samples // len(symbols))
                elif mod_type == '8PSK':
                    # 8 phase positions
                    phases = np.linspace(0, 2*np.pi, 8, endpoint=False)
                    symbols = []
                    for j in range(0, len(data_bits)-2, 3):
                        if j+2 < len(data_bits):
                            sym_idx = data_bits[j] * 4 + data_bits[j+1] * 2 + data_bits[j+2]
                            symbols.append(np.exp(1j * phases[sym_idx]))
                    symbols = np.array(symbols)
                    iq_signal = np.repeat(symbols, n_samples // len(symbols))
                elif mod_type == '16QAM':
                    # 16QAM constellation
                    constellation = []
                    for real in [-3, -1, 1, 3]:
                        for imag in [-3, -1, 1, 3]:
                            constellation.append(real + 1j * imag)
                    symbols = []
                    for j in range(0, len(data_bits)-3, 4):
                        if j+3 < len(data_bits):
                            sym_idx = (data_bits[j] * 8 + data_bits[j+1] * 4 + 
                                     data_bits[j+2] * 2 + data_bits[j+3])
                            symbols.append(constellation[sym_idx])
                    symbols = np.array(symbols)
                    iq_signal = np.repeat(symbols, n_samples // len(symbols))
                else:  # 64QAM
                    # Simplified 64QAM
                    constellation = []
                    for real in range(-7, 8, 2):
                        for imag in range(-7, 8, 2):
                            constellation.append(real + 1j * imag)
                    symbols = []
                    for j in range(0, len(data_bits)-5, 6):
                        if j+5 < len(data_bits):
                            sym_idx = sum(data_bits[j+k] * (2**(5-k)) for k in range(6))
                            if sym_idx < len(constellation):
                                symbols.append(constellation[sym_idx])
                    symbols = np.array(symbols)
                    iq_signal = np.repeat(symbols, n_samples // len(symbols))
                
                # Ensure correct length
                if len(iq_signal) > n_samples:
                    iq_signal = iq_signal[:n_samples]
                elif len(iq_signal) < n_samples:
                    iq_signal = np.pad(iq_signal, (0, n_samples - len(iq_signal)), 'wrap')
                
                # Add noise and impairments
                snr_db = np.random.uniform(10, 25)
                noise_power = 10**(-snr_db/10)
                noise = np.sqrt(noise_power/2) * (np.random.randn(len(iq_signal)) + 
                                                 1j * np.random.randn(len(iq_signal)))
                
                # Add frequency offset
                freq_offset = np.random.uniform(-5, 5)
                t = np.arange(len(iq_signal)) / fs
                freq_shift = np.exp(1j * 2 * np.pi * freq_offset * t)
                
                iq_signal = iq_signal * freq_shift + noise
                
                # Store signal
                dataset_name = f'signal_{signal_idx}'
                f.create_dataset(dataset_name, data=iq_signal)
                ground_truth[dataset_name] = mod_type
                signal_idx += 1
    
    # Save ground truth for testing
    with open(os.path.join(temp_dir, 'ground_truth.json'), 'w') as f:
        json.dump(ground_truth, f)
    
    return input_file

def test_script():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test data
        input_file = create_data(temp_dir)
        output_file = os.path.join(temp_dir, 'classifications.json')
        features_file = os.path.join(temp_dir, 'features.json')
        constellation_dir = os.path.join(temp_dir, 'constellations')
        
        # Test different argument name variations
        arg_variations = [
            ['--input-file', '--output-file', '--features-file', '--constellation-dir'],
            ['--input_file', '--output_file', '--features_file', '--constellation_dir'],
            ['-i', '-o', '-f', '-c']
        ]
        
        success = False
        for args in arg_variations:
            try:
                cmd = ['python', 'generated.py', 
                       args[0], input_file,
                       args[1], output_file,
                       args[2], features_file,
                       args[3], constellation_dir]
                result = subprocess.run(cmd, cwd=temp_dir, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        print(f"PASS: Script execution successful: {success}")
        
        if not success:
            print("FAIL: All argument variations failed")
            return
        
        # Test output files exist
        output_exists = os.path.exists(output_file)
        features_exists = os.path.exists(features_file)
        constellation_dir_exists = os.path.exists(constellation_dir)
        
        print(f"PASS: Output file created: {output_exists}")
        print(f"PASS: Features file created: {features_exists}")
        print(f"PASS: Constellation directory created: {constellation_dir_exists}")
        
        if not (output_exists and features_exists):
            print("FAIL: Required output files missing")
            return
        
        # Load and validate outputs
        try:
            with open(output_file, 'r') as f:
                classifications = json.load(f)
            with open(features_file, 'r') as f:
                features = json.load(f)
            with open(os.path.join(temp_dir, 'ground_truth.json'), 'r') as f:
                ground_truth = json.load(f)
        except:
            print("FAIL: Could not load output JSON files")
            return
        
        # Test classification completeness
        all_signals_classified = all(sig in classifications for sig in ground_truth.keys())
        print(f"PASS: All signals classified: {all_signals_classified}")
        
        # Test modulation types coverage
        expected_mods = {'BPSK', 'QPSK', '8PSK', '16QAM', '64QAM'}
        predicted_mods = set()
        for pred in classifications.values():
            if isinstance(pred, dict) and 'modulation' in pred:
                predicted_mods.add(pred['modulation'])
            elif isinstance(pred, str):
                predicted_mods.add(pred)
        
        mod_coverage = len(predicted_mods.intersection(expected_mods)) >= 3
        print(f"PASS: Adequate modulation type coverage: {mod_coverage}")
        
        # Test features extraction
        feature_completeness = len(features) >= len(ground_truth) * 0.8
        print(f"PASS: Feature extraction completeness: {feature_completeness}")
        
        # Test feature dimensionality
        if features:
            sample_features = list(features.values())[0]
            if isinstance(sample_features, dict):
                feature_count = len(sample_features)
            else:
                feature_count = len(sample_features) if isinstance(sample_features, list) else 0
            adequate_features = feature_count >= 6
        else:
            adequate_features = False
        print(f"PASS: Adequate feature count (>=6): {adequate_features}")
        
        # Test constellation plots
        if constellation_dir_exists:
            constellation_files = [f for f in os.listdir(constellation_dir) 
                                 if f.endswith(('.png', '.jpg', '.pdf'))]
            constellation_plots = len(constellation_files) >= 10
        else:
            constellation_plots = False
        print(f"PASS: Constellation plots generated: {constellation_plots}")
        
        # Test confidence scores
        has_confidence = False
        for pred in classifications.values():
            if isinstance(pred, dict) and ('confidence' in pred or 'score' in pred):
                has_confidence = True
                break
        print(f"PASS: Confidence scores provided: {has_confidence}")
        
        # Test performance metrics
        has_metrics = False
        metrics_keys = ['accuracy', 'confusion_matrix', 'precision', 'recall']
        for pred in classifications.values():
            if isinstance(pred, dict):
                if any(key in pred for key in metrics_keys):
                    has_metrics = True
                    break
        
        # Check if metrics are in separate key
        if 'metrics' in classifications or 'performance' in classifications:
            has_metrics = True
        
        print(f"PASS: Performance metrics included: {has_metrics}")
        
        # Calculate accuracy score
        correct_predictions = 0
        total_predictions = 0
        
        for signal_name, true_mod in ground_truth.items():
            if signal_name in classifications:
                pred = classifications[signal_name]
                pred_mod = None
                
                if isinstance(pred, dict):
                    pred_mod = pred.get('modulation', pred.get('prediction', ''))
                elif isinstance(pred, str):
                    pred_mod = pred
                
                if pred_mod == true_mod:
                    correct_predictions += 1
                total_predictions += 1
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        print(f"SCORE: Classification accuracy: {accuracy:.3f}")
        
        # Calculate feature quality score
        feature_quality = 0.0
        if features and adequate_features:
            # Check for reasonable feature values (not all zeros/NaN)
            valid_features = 0
            total_feature_sets = 0
            
            for signal_features in features.values():
                if isinstance(signal_features, dict):
                    feature_vals = list(signal_features.values())
                elif isinstance(signal_features, list):
                    feature_vals = signal_features
                else:
                    continue
                
                total_feature_sets += 1
                if any(isinstance(v, (int, float)) and not np.isnan(v) and v != 0 
                       for v in feature_vals):
                    valid_features += 1
            
            feature_quality = valid_features / total_feature_sets if total_feature_sets > 0 else 0
        
        print(f"SCORE: Feature extraction quality: {feature_quality:.3f}")
        
        # Additional validation tests
        json_format_valid = True
        try:
            # Verify JSON structure
            assert isinstance(classifications, dict)
            assert isinstance(features, dict)
        except:
            json_format_valid = False
        
        print(f"PASS: Valid JSON format: {json_format_valid}")
        
        # Test signal preprocessing evidence
        preprocessing_applied = False
        if features:
            # Look for evidence of normalization/preprocessing in feature statistics
            for signal_features in features.values():
                if isinstance(signal_features, dict):
                    # Check if features suggest normalized signals
                    if any('norm' in str(k).lower() or 'power' in str(k).lower() 
                           for k in signal_features.keys()):
                        preprocessing_applied = True
                        break
        
        print(f"PASS: Signal preprocessing evidence: {preprocessing_applied}")

if __name__ == "__main__":
    test_script()
