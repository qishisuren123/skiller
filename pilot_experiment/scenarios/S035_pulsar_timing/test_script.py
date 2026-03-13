import numpy as np
import pandas as pd
import json
import subprocess
import tempfile
import os
import sys
from scipy.optimize import minimize, curve_fit
from scipy import stats

def create_data(n_obs=500, n_freq=8, output_file="timing_data.csv"):
    """Generate synthetic pulsar timing data"""
    np.random.seed(42)
    
    # True parameters
    true_P0 = 0.033  # period in seconds
    true_P1 = 1e-15  # period derivative
    true_DM = 56.7   # dispersion measure
    true_T0 = 58000.0  # reference MJD
    
    # Frequency setup
    freqs = np.logspace(np.log10(300), np.log10(1400), n_freq)  # 300-1400 MHz
    
    # Generate observations
    data = []
    K_dm = 4.148808e3  # dispersion constant
    
    for i in range(n_obs):
        mjd = true_T0 + np.random.uniform(0, 100)  # 100 day span
        freq = np.random.choice(freqs)
        
        # Calculate pulse number
        pulse_num = int((mjd - true_T0) * 86400 / true_P0)
        
        # Predicted TOA from timing model
        predicted_toa = true_T0 * 86400 + true_P0 * pulse_num + 0.5 * true_P1 * pulse_num**2
        
        # Add dispersion delay
        dm_delay = K_dm * true_DM / (freq**2)
        
        # Observed TOA with noise
        toa_uncertainty = np.random.uniform(0.5e-6, 5e-6)  # 0.5-5 microseconds
        noise = np.random.normal(0, toa_uncertainty)
        observed_toa = predicted_toa + dm_delay + noise
        
        # Add some outliers
        if np.random.random() < 0.02:
            observed_toa += np.random.normal(0, 20e-6)
        
        data.append({
            'MJD': mjd,
            'frequency_MHz': freq,
            'TOA_seconds': observed_toa,
            'TOA_uncertainty': toa_uncertainty
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    return df

def test_pulsar_timing():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create test data
        test_data = create_data(n_obs=400, n_freq=6)
        
        # Run the generated script
        cmd = [
            sys.executable, "generated.py",
            "--input", "timing_data.csv",
            "--output-json", "results.json",
            "--output-csv", "processed_data.csv"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            print("FAIL: Script execution timed out")
            return
        except FileNotFoundError:
            print("FAIL: generated.py not found")
            return
        
        if result.returncode != 0:
            print(f"FAIL: Script failed with return code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return
        
        # Test 1: Check output files exist
        if os.path.exists("results.json") and os.path.exists("processed_data.csv"):
            print("PASS: Output files created")
        else:
            print("FAIL: Missing output files")
            return
        
        # Load results
        try:
            with open("results.json", 'r') as f:
                results = json.load(f)
            processed_df = pd.read_csv("processed_data.csv")
        except Exception as e:
            print(f"FAIL: Could not load output files: {e}")
            return
        
        print("PASS: Output files readable")
        
        # Test 2: Check JSON structure
        required_keys = ['timing_parameters', 'dispersion_measure', 'residual_statistics']
        if all(key in results for key in required_keys):
            print("PASS: JSON contains required sections")
        else:
            print("FAIL: JSON missing required sections")
        
        # Test 3: Check timing parameters
        timing_params = results.get('timing_parameters', {})
        if 'P0' in timing_params and 'P1' in timing_params and 'T0' in timing_params:
            print("PASS: Timing parameters present")
        else:
            print("FAIL: Missing timing parameters")
        
        # Test 4: Check dispersion measure
        dm_value = results.get('dispersion_measure', {}).get('value', 0)
        if 20 < dm_value < 100:  # Reasonable range
            print("PASS: Dispersion measure in reasonable range")
        else:
            print("FAIL: Dispersion measure out of range")
        
        # Test 5: Check residual statistics
        residual_stats = results.get('residual_statistics', {})
        if 'rms_residual' in residual_stats and 'reduced_chi_squared' in residual_stats:
            print("PASS: Residual statistics present")
        else:
            print("FAIL: Missing residual statistics")
        
        # Test 6: Check processed data columns
        required_cols = ['residual', 'predicted_TOA']
        if all(col in processed_df.columns for col in required_cols):
            print("PASS: Processed data has required columns")
        else:
            print("FAIL: Processed data missing required columns")
        
        # Test 7: Check data completeness
        if len(processed_df) > 300:  # Should have most original data
            print("PASS: Processed data completeness")
        else:
            print("FAIL: Too much data removed")
        
        # Test 8: Check residual values
        if 'residual' in processed_df.columns:
            residuals = processed_df['residual'].dropna()
            if len(residuals) > 0 and np.std(residuals) < 1e-4:  # Reasonable residual scale
                print("PASS: Residual values reasonable")
            else:
                print("FAIL: Residual values unreasonable")
        else:
            print("FAIL: No residual column")
        
        # Test 9: Check outlier removal
        original_count = len(test_data)
        processed_count = len(processed_df)
        removal_fraction = (original_count - processed_count) / original_count
        if 0 <= removal_fraction <= 0.2:  # Reasonable outlier removal
            print("PASS: Reasonable outlier removal")
        else:
            print("FAIL: Excessive or no outlier removal")
        
        # Test 10: Check frequency coverage
        if 'frequency_MHz' in processed_df.columns:
            freq_range = processed_df['frequency_MHz'].max() - processed_df['frequency_MHz'].min()
            if freq_range > 500:  # Should span significant frequency range
                print("PASS: Adequate frequency coverage")
            else:
                print("FAIL: Insufficient frequency coverage")
        else:
            print("FAIL: No frequency column in processed data")
        
        # Test 11: Check parameter uncertainties
        timing_params = results.get('timing_parameters', {})
        has_uncertainties = any('uncertainty' in str(key) for key in timing_params.keys())
        if has_uncertainties:
            print("PASS: Parameter uncertainties included")
        else:
            print("FAIL: No parameter uncertainties")
        
        # Test 12: Check chi-squared value
        chi_sq = residual_stats.get('reduced_chi_squared', 0)
        if 0.5 < chi_sq < 5.0:  # Reasonable chi-squared
            print("PASS: Reasonable reduced chi-squared")
        else:
            print("FAIL: Unreasonable reduced chi-squared")
        
        # SCORE 1: Parameter accuracy
        true_P0 = 0.033
        fitted_P0 = timing_params.get('P0', 0)
        p0_accuracy = max(0, 1 - abs(fitted_P0 - true_P0) / true_P0)
        
        true_DM = 56.7
        fitted_DM = dm_value
        dm_accuracy = max(0, 1 - abs(fitted_DM - true_DM) / true_DM)
        
        param_score = (p0_accuracy + dm_accuracy) / 2
        print(f"SCORE: Parameter accuracy: {param_score:.3f}")
        
        # SCORE 2: Analysis completeness
        completeness_factors = [
            1 if 'rms_residual' in residual_stats else 0,
            1 if 'reduced_chi_squared' in residual_stats else 0,
            1 if len(processed_df) > 300 else 0,
            1 if 'residual' in processed_df.columns else 0,
            1 if has_uncertainties else 0
        ]
        completeness_score = sum(completeness_factors) / len(completeness_factors)
        print(f"SCORE: Analysis completeness: {completeness_score:.3f}")

if __name__ == "__main__":
    test_pulsar_timing()
