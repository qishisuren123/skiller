import subprocess
import tempfile
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import sys

def create_data():
    """Generate synthetic ECG data parameters for testing"""
    return {
        'sampling_rates': [250, 500, 1000],
        'durations': [30, 60, 120],
        'noise_levels': [0.05, 0.1, 0.2],
        'expected_hr_range': (60, 100)  # Expected heart rate range in BPM
    }

def run_test():
    test_data = create_data()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Test case parameters
        sampling_rate = 500
        duration = 60
        noise_level = 0.1
        
        # Run the script with various argument name variations
        possible_args = [
            ['--sampling_rate', str(sampling_rate), '--duration', str(duration), 
             '--noise_level', str(noise_level), '--output_peaks', 'peaks.csv', 
             '--output_hrv', 'hrv.json', '--plot', 'ecg_plot.png'],
            ['--fs', str(sampling_rate), '--time', str(duration), 
             '--noise', str(noise_level), '--peaks_file', 'peaks.csv', 
             '--hrv_file', 'hrv.json', '--plot_file', 'ecg_plot.png']
        ]
        
        success = False
        for args in possible_args:
            try:
                result = subprocess.run([sys.executable, 'generated.py'] + args, 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed")
            return
        
        # Test 1: Check if peaks CSV file exists and has correct structure
        if os.path.exists('peaks.csv'):
            try:
                peaks_df = pd.read_csv('peaks.csv')
                required_cols = any(col in peaks_df.columns for col in ['timestamp', 'time', 'sample'])
                has_amplitude = any(col in peaks_df.columns for col in ['amplitude', 'value', 'peak'])
                print(f"PASS: Peaks CSV file created with proper structure" if required_cols and has_amplitude else "FAIL: Peaks CSV missing required columns")
            except:
                print("FAIL: Peaks CSV file corrupted or unreadable")
        else:
            print("FAIL: Peaks CSV file not created")
        
        # Test 2: Check if HRV JSON file exists and contains required metrics
        hrv_valid = False
        if os.path.exists('hrv.json'):
            try:
                with open('hrv.json', 'r') as f:
                    hrv_data = json.load(f)
                has_rmssd = any(key.lower() in ['rmssd'] for key in hrv_data.keys())
                has_sdnn = any(key.lower() in ['sdnn'] for key in hrv_data.keys())
                has_pnn50 = any(key.lower() in ['pnn50'] for key in hrv_data.keys())
                hrv_valid = has_rmssd and has_sdnn and has_pnn50
                print(f"PASS: HRV JSON contains required metrics" if hrv_valid else "FAIL: HRV JSON missing required metrics")
            except:
                print("FAIL: HRV JSON file corrupted or unreadable")
        else:
            print("FAIL: HRV JSON file not created")
        
        # Test 3: Check if plot file is created
        plot_exists = os.path.exists('ecg_plot.png')
        print(f"PASS: ECG plot file created" if plot_exists else "FAIL: ECG plot file not created")
        
        # Test 4: Validate number of detected peaks is reasonable
        peak_count_valid = False
        if os.path.exists('peaks.csv'):
            try:
                peaks_df = pd.read_csv('peaks.csv')
                num_peaks = len(peaks_df)
                expected_min_peaks = int(duration * 60 / 60 * 0.7)  # 70% of expected at 60 BPM
                expected_max_peaks = int(duration * 100 / 60 * 1.3)  # 130% of expected at 100 BPM
                peak_count_valid = expected_min_peaks <= num_peaks <= expected_max_peaks
                print(f"PASS: Reasonable number of peaks detected ({num_peaks})" if peak_count_valid else f"FAIL: Unreasonable peak count ({num_peaks})")
            except:
                print("FAIL: Could not validate peak count")
        
        # Test 5: Check HRV metric ranges are physiologically plausible
        hrv_ranges_valid = False
        if hrv_valid:
            try:
                with open('hrv.json', 'r') as f:
                    hrv_data = json.load(f)
                
                # Get values with flexible key matching
                rmssd = next((v for k, v in hrv_data.items() if 'rmssd' in k.lower()), None)
                sdnn = next((v for k, v in hrv_data.items() if 'sdnn' in k.lower()), None)
                pnn50 = next((v for k, v in hrv_data.items() if 'pnn50' in k.lower()), None)
                
                rmssd_valid = rmssd is not None and 10 <= rmssd <= 200
                sdnn_valid = sdnn is not None and 20 <= sdnn <= 300
                pnn50_valid = pnn50 is not None and 0 <= pnn50 <= 100
                
                hrv_ranges_valid = rmssd_valid and sdnn_valid and pnn50_valid
                print(f"PASS: HRV metrics within physiological ranges" if hrv_ranges_valid else "FAIL: HRV metrics outside expected ranges")
            except:
                print("FAIL: Could not validate HRV metric ranges")
        
        # Test 6: Check if peaks are temporally ordered
        peaks_ordered = False
        if os.path.exists('peaks.csv'):
            try:
                peaks_df = pd.read_csv('peaks.csv')
                time_col = next((col for col in peaks_df.columns if col.lower() in ['timestamp', 'time', 'sample']), None)
                if time_col:
                    peaks_ordered = peaks_df[time_col].is_monotonic_increasing
                print(f"PASS: Peaks are temporally ordered" if peaks_ordered else "FAIL: Peaks not in temporal order")
            except:
                print("FAIL: Could not validate peak ordering")
        
        # Test 7: Verify minimum distance between peaks
        min_distance_valid = False
        if os.path.exists('peaks.csv'):
            try:
                peaks_df = pd.read_csv('peaks.csv')
                time_col = next((col for col in peaks_df.columns if col.lower() in ['timestamp', 'time', 'sample']), None)
                if time_col and len(peaks_df) > 1:
                    time_diffs = np.diff(peaks_df[time_col].values)
                    if 'sample' in time_col.lower():
                        time_diffs = time_diffs / sampling_rate * 1000  # Convert to ms
                    min_distance_valid = np.all(time_diffs >= 250)  # Minimum 250ms between peaks
                print(f"PASS: Minimum distance between peaks maintained" if min_distance_valid else "FAIL: Peaks too close together")
            except:
                print("FAIL: Could not validate minimum peak distance")
        
        # Test 8: Check if R-R intervals are calculated correctly
        rr_calculation_valid = False
        if os.path.exists('peaks.csv') and hrv_valid:
            try:
                peaks_df = pd.read_csv('peaks.csv')
                time_col = next((col for col in peaks_df.columns if col.lower() in ['timestamp', 'time', 'sample']), None)
                if time_col and len(peaks_df) > 1:
                    times = peaks_df[time_col].values
                    if 'sample' in time_col.lower():
                        times = times / sampling_rate
                    rr_intervals = np.diff(times) * 1000  # Convert to ms
                    
                    # Check if calculated SDNN matches expected from R-R intervals
                    calculated_sdnn = np.std(rr_intervals)
                    with open('hrv.json', 'r') as f:
                        hrv_data = json.load(f)
                    reported_sdnn = next((v for k, v in hrv_data.items() if 'sdnn' in k.lower()), None)
                    
                    if reported_sdnn:
                        rr_calculation_valid = abs(calculated_sdnn - reported_sdnn) < 5  # 5ms tolerance
                print(f"PASS: R-R interval calculations are correct" if rr_calculation_valid else "FAIL: R-R interval calculations incorrect")
            except:
                print("FAIL: Could not validate R-R interval calculations")
        
        # Test 9: Verify artifact removal (no extremely short/long intervals)
        artifact_removal_valid = False
        if os.path.exists('peaks.csv'):
            try:
                peaks_df = pd.read_csv('peaks.csv')
                time_col = next((col for col in peaks_df.columns if col.lower() in ['timestamp', 'time', 'sample']), None)
                if time_col and len(peaks_df) > 1:
                    times = peaks_df[time_col].values
                    if 'sample' in time_col.lower():
                        times = times / sampling_rate
                    rr_intervals = np.diff(times) * 1000
                    
                    # Check no intervals < 300ms or > 2000ms
                    artifact_removal_valid = np.all((rr_intervals >= 300) & (rr_intervals <= 2000))
                print(f"PASS: Artifact removal implemented correctly" if artifact_removal_valid else "FAIL: Artifacts not properly removed")
            except:
                print("FAIL: Could not validate artifact removal")
        
        # Test 10: Check pNN50 calculation
        pnn50_valid = False
        if os.path.exists('peaks.csv') and hrv_valid:
            try:
                peaks_df = pd.read_csv('peaks.csv')
                time_col = next((col for col in peaks_df.columns if col.lower() in ['timestamp', 'time', 'sample']), None)
                if time_col and len(peaks_df) > 2:
                    times = peaks_df[time_col].values
                    if 'sample' in time_col.lower():
                        times = times / sampling_rate
                    rr_intervals = np.diff(times) * 1000
                    
                    # Calculate pNN50
                    successive_diffs = np.abs(np.diff(rr_intervals))
                    calculated_pnn50 = np.sum(successive_diffs > 50) / len(successive_diffs) * 100
                    
                    with open('hrv.json', 'r') as f:
                        hrv_data = json.load(f)
                    reported_pnn50 = next((v for k, v in hrv_data.items() if 'pnn50' in k.lower()), None)
                    
                    if reported_pnn50 is not None:
                        pnn50_valid = abs(calculated_pnn50 - reported_pnn50) < 2  # 2% tolerance
                print(f"PASS: pNN50 calculation is correct" if pnn50_valid else "FAIL: pNN50 calculation incorrect")
            except:
                print("FAIL: Could not validate pNN50 calculation")
        
        # Test 11: Verify different sampling rates work
        different_fs_valid = False
        try:
            result = subprocess.run([sys.executable, 'generated.py', '--sampling_rate', '250', 
                                   '--duration', '30', '--noise_level', '0.05', 
                                   '--output_peaks', 'peaks_250.csv', '--output_hrv', 'hrv_250.json', 
                                   '--plot', 'plot_250.png'], 
                                  capture_output=True, text=True, timeout=30)
            different_fs_valid = result.returncode == 0 and os.path.exists('peaks_250.csv')
            print(f"PASS: Different sampling rates supported" if different_fs_valid else "FAIL: Different sampling rates not supported")
        except:
            print("FAIL: Could not test different sampling rates")
        
        # Test 12: Check if noise level affects detection appropriately
        noise_handling_valid = False
        try:
            # Test with high noise
            result = subprocess.run([sys.executable, 'generated.py', '--sampling_rate', '500', 
                                   '--duration', '30', '--noise_level', '0.3', 
                                   '--output_peaks', 'peaks_noisy.csv', '--output_hrv', 'hrv_noisy.json', 
                                   '--plot', 'plot_noisy.png'], 
                                  capture_output=True, text=True, timeout=30)
            noise_handling_valid = result.returncode == 0
            print(f"PASS: High noise levels handled appropriately" if noise_handling_valid else "FAIL: High noise levels cause failure")
        except:
            print("FAIL: Could not test noise handling")
        
        # SCORE 1: Detection accuracy score based on peak count and HRV validity
        detection_score = 0.0
        if peak_count_valid:
            detection_score += 0.3
        if hrv_ranges_valid:
            detection_score += 0.3
        if min_distance_valid:
            detection_score += 0.2
        if artifact_removal_valid:
            detection_score += 0.2
        print(f"SCORE: Detection accuracy: {detection_score:.2f}")
        
        # SCORE 2: Implementation completeness score
        completeness_score = 0.0
        if os.path.exists('peaks.csv'):
            completeness_score += 0.2
        if hrv_valid:
            completeness_score += 0.2
        if plot_exists:
            completeness_score += 0.1
        if rr_calculation_valid:
            completeness_score += 0.2
        if pnn50_valid:
            completeness_score += 0.15
        if different_fs_valid:
            completeness_score += 0.1
        if noise_handling_valid:
            completeness_score += 0.05
        print(f"SCORE: Implementation completeness: {completeness_score:.2f}")

if __name__ == "__main__":
    run_test()
