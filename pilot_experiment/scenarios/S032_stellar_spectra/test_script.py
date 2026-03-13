import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import h5py
import subprocess
import tempfile
import os
import sys
from scipy import interpolate, optimize
from scipy.signal import find_peaks

def create_data():
    """Generate synthetic stellar spectra with realistic features"""
    np.random.seed(42)
    
    # Define spectral types and their characteristics
    spectral_types = ['O', 'B', 'A', 'F', 'G', 'K', 'M']
    n_spectra = 12
    
    # Wavelength grid (Angstroms)
    wavelength = np.linspace(3800, 7000, 2000)
    
    spectra_data = []
    true_types = []
    
    for i in range(n_spectra):
        spec_type = spectral_types[i % len(spectral_types)]
        if i >= len(spectral_types):  # Add some duplicates with different noise
            spec_type = spectral_types[(i - len(spectral_types)) % len(spectral_types)]
        
        # Generate synthetic spectrum based on spectral type
        spectrum = generate_stellar_spectrum(wavelength, spec_type)
        
        spectra_data.append({
            'wavelength': wavelength,
            'flux': spectrum,
            'spectrum_id': f'star_{i:03d}',
            'true_type': spec_type
        })
        true_types.append(spec_type)
    
    return spectra_data, true_types

def generate_stellar_spectrum(wavelength, spec_type):
    """Generate a synthetic stellar spectrum with absorption lines"""
    # Base continuum (blackbody-like)
    temp_map = {'O': 40000, 'B': 20000, 'A': 9000, 'F': 7000, 'G': 5500, 'K': 4000, 'M': 3000}
    temp = temp_map[spec_type]
    
    # Simplified blackbody continuum
    continuum = (wavelength / 5500) ** (-1.5) * np.exp(-1.44e8 / (wavelength * temp))
    continuum = continuum / np.max(continuum)
    
    # Add absorption lines characteristic of each spectral type
    spectrum = continuum.copy()
    
    # Hydrogen Balmer lines (stronger in A-F stars)
    h_alpha = 6563.0
    h_beta = 4861.0
    h_gamma = 4340.0
    
    balmer_strength = {'O': 0.1, 'B': 0.3, 'A': 0.8, 'F': 0.6, 'G': 0.3, 'K': 0.2, 'M': 0.1}
    
    spectrum *= add_absorption_line(wavelength, h_alpha, balmer_strength[spec_type] * 0.4, 2.0)
    spectrum *= add_absorption_line(wavelength, h_beta, balmer_strength[spec_type] * 0.6, 1.8)
    spectrum *= add_absorption_line(wavelength, h_gamma, balmer_strength[spec_type] * 0.5, 1.5)
    
    # Calcium H&K lines (stronger in cooler stars)
    ca_h = 3968.5
    ca_k = 3933.7
    ca_strength = {'O': 0.1, 'B': 0.2, 'A': 0.3, 'F': 0.5, 'G': 0.7, 'K': 0.8, 'M': 0.6}
    
    spectrum *= add_absorption_line(wavelength, ca_h, ca_strength[spec_type] * 0.5, 1.2)
    spectrum *= add_absorption_line(wavelength, ca_k, ca_strength[spec_type] * 0.6, 1.2)
    
    # Magnesium line (stronger in cooler stars)
    mg_line = 5175.0
    mg_strength = {'O': 0.05, 'B': 0.1, 'A': 0.2, 'F': 0.4, 'G': 0.6, 'K': 0.7, 'M': 0.5}
    spectrum *= add_absorption_line(wavelength, mg_line, mg_strength[spec_type] * 0.4, 1.0)
    
    # Add realistic noise
    snr = np.random.uniform(20, 100)
    noise = np.random.normal(0, 1.0/snr, len(spectrum))
    spectrum += noise
    
    # Ensure positive flux
    spectrum = np.maximum(spectrum, 0.01)
    
    return spectrum

def add_absorption_line(wavelength, center, depth, width):
    """Add a Gaussian absorption line"""
    return 1.0 - depth * np.exp(-0.5 * ((wavelength - center) / width) ** 2)

def run_test():
    print("Generating synthetic stellar spectra data...")
    spectra_data, true_types = create_data()
    
    # Save input data
    input_file = 'input_spectra.h5'
    with h5py.File(input_file, 'w') as f:
        for i, spec_data in enumerate(spectra_data):
            grp = f.create_group(f"spectrum_{i}")
            grp.create_dataset('wavelength', data=spec_data['wavelength'])
            grp.create_dataset('flux', data=spec_data['flux'])
            grp.attrs['spectrum_id'] = spec_data['spectrum_id']
    
    # Run the generated script
    output_spectra = 'normalized_spectra.h5'
    output_classification = 'classification_results.json'
    output_plots = 'diagnostic_plots'
    
    cmd = [
        sys.executable, 'generated.py',
        '--input', input_file,
        '--output-spectra', output_spectra,
        '--output-classification', output_classification,
        '--output-plots', output_plots,
        '--min-snr', '10',
        '--poly-order', '4'
    ]
    
    # Try alternative argument names
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        print("FAIL: Script execution timed out")
        return
    except FileNotFoundError:
        print("FAIL: generated.py not found")
        return
    
    if result.returncode != 0:
        # Try alternative argument names
        alt_cmd = [
            sys.executable, 'generated.py',
            '--input-file', input_file,
            '--normalized-output', output_spectra,
            '--classification-output', output_classification,
            '--plot-dir', output_plots
        ]
        try:
            result = subprocess.run(alt_cmd, capture_output=True, text=True, timeout=60)
        except:
            pass
    
    if result.returncode != 0:
        print(f"FAIL: Script execution failed with return code {result.returncode}")
        print(f"STDERR: {result.stderr}")
        return
    
    # Test outputs
    tests_passed = 0
    total_tests = 13
    
    # Test 1: Check if normalized spectra file exists
    if os.path.exists(output_spectra):
        print("PASS: Normalized spectra file created")
        tests_passed += 1
    else:
        print("FAIL: Normalized spectra file not created")
    
    # Test 2: Check if classification results file exists
    if os.path.exists(output_classification):
        print("PASS: Classification results file created")
        tests_passed += 1
    else:
        print("FAIL: Classification results file not created")
    
    # Test 3: Check if plots directory exists
    if os.path.exists(output_plots) and os.path.isdir(output_plots):
        print("PASS: Diagnostic plots directory created")
        tests_passed += 1
    else:
        print("FAIL: Diagnostic plots directory not created")
    
    # Load and validate outputs
    normalized_spectra = {}
    classification_results = {}
    
    # Test 4-6: Validate normalized spectra
    try:
        with h5py.File(output_spectra, 'r') as f:
            for key in f.keys():
                if 'wavelength' in f[key] and 'flux' in f[key]:
                    normalized_spectra[key] = {
                        'wavelength': f[key]['wavelength'][:],
                        'flux': f[key]['flux'][:]
                    }
        
        if len(normalized_spectra) >= 10:
            print("PASS: Sufficient number of normalized spectra")
            tests_passed += 1
        else:
            print("FAIL: Insufficient normalized spectra")
        
        # Check normalization quality
        normalization_scores = []
        for spec_key, spec_data in normalized_spectra.items():
            flux = spec_data['flux']
            # Check if continuum regions are close to 1.0
            continuum_regions = (flux > 0.8) & (flux < 1.2)
            if np.sum(continuum_regions) > 0:
                continuum_flux = flux[continuum_regions]
                norm_score = 1.0 - abs(np.median(continuum_flux) - 1.0)
                normalization_scores.append(max(0, norm_score))
        
        if len(normalization_scores) > 0 and np.mean(normalization_scores) > 0.7:
            print("PASS: Good continuum normalization quality")
            tests_passed += 1
        else:
            print("FAIL: Poor continuum normalization quality")
        
        # Check for positive flux values
        all_positive = True
        for spec_data in normalized_spectra.values():
            if np.any(spec_data['flux'] <= 0):
                all_positive = False
                break
        
        if all_positive:
            print("PASS: All normalized flux values are positive")
            tests_passed += 1
        else:
            print("FAIL: Some normalized flux values are non-positive")
            
    except Exception as e:
        print(f"FAIL: Error reading normalized spectra: {e}")
    
    # Test 7-10: Validate classification results
    try:
        with open(output_classification, 'r') as f:
            classification_results = json.load(f)
        
        if len(classification_results) >= 10:
            print("PASS: Sufficient classification results")
            tests_passed += 1
        else:
            print("FAIL: Insufficient classification results")
        
        # Check for required fields
        required_fields = ['spectral_type', 'confidence']
        has_required_fields = True
        for result in classification_results.values():
            for field in required_fields:
                if field not in result:
                    has_required_fields = False
                    break
        
        if has_required_fields:
            print("PASS: Classification results have required fields")
            tests_passed += 1
        else:
            print("FAIL: Classification results missing required fields")
        
        # Check spectral type validity
        valid_types = {'O', 'B', 'A', 'F', 'G', 'K', 'M'}
        valid_classifications = True
        for result in classification_results.values():
            if 'spectral_type' in result:
                if result['spectral_type'] not in valid_types:
                    valid_classifications = False
                    break
        
        if valid_classifications:
            print("PASS: All spectral type classifications are valid")
            tests_passed += 1
        else:
            print("FAIL: Some spectral type classifications are invalid")
        
        # Check confidence scores
        valid_confidence = True
        for result in classification_results.values():
            if 'confidence' in result:
                conf = result['confidence']
                if not (0 <= conf <= 1):
                    valid_confidence = False
                    break
        
        if valid_confidence:
            print("PASS: All confidence scores are in valid range [0,1]")
            tests_passed += 1
        else:
            print("FAIL: Some confidence scores are outside valid range")
            
    except Exception as e:
        print(f"FAIL: Error reading classification results: {e}")
    
    # Test 11-12: Check diagnostic plots
    plot_files = []
    if os.path.exists(output_plots):
        plot_files = [f for f in os.listdir(output_plots) if f.endswith('.png')]
    
    if len(plot_files) >= 5:
        print("PASS: Sufficient diagnostic plots generated")
        tests_passed += 1
    else:
        print("FAIL: Insufficient diagnostic plots generated")
    
    # Test 13: Check for feature extraction results
    has_features = False
    try:
        for result in classification_results.values():
            if 'features' in result or 'equivalent_widths' in result:
                has_features = True
                break
    except:
        pass
    
    if has_features:
        print("PASS: Feature extraction results included")
        tests_passed += 1
    else:
        print("FAIL: No feature extraction results found")
    
    # Calculate scores
    classification_accuracy = 0.0
    normalization_quality = 0.0
    
    try:
        # Calculate classification accuracy
        correct_classifications = 0
        total_classifications = 0
        
        for i, (spec_key, result) in enumerate(classification_results.items()):
            if i < len(true_types) and 'spectral_type' in result:
                if result['spectral_type'] == true_types[i]:
                    correct_classifications += 1
                total_classifications += 1
        
        if total_classifications > 0:
            classification_accuracy = correct_classifications / total_classifications
        
        # Calculate normalization quality
        if normalization_scores:
            normalization_quality = np.mean(normalization_scores)
            
    except Exception as e:
        print(f"Warning: Error calculating scores: {e}")
    
    print(f"\nSUMMARY: {tests_passed}/{total_tests} tests passed")
    print(f"SCORE: {tests_passed/total_tests:.3f}")
    print(f"SCORE: {(classification_accuracy + normalization_quality)/2:.3f}")

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        run_test()
