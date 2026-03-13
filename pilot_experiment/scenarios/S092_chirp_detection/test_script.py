import numpy as np
import json
import subprocess
import tempfile
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
import sys

def create_data():
    """Generate synthetic spectrogram data with embedded chirp signals"""
    np.random.seed(42)
    
    # Create time and frequency arrays
    duration = 4.0  # seconds
    fs = 1000  # sampling frequency
    t = np.linspace(0, duration, int(fs * duration))
    freqs = np.linspace(0, fs/2, 200)
    
    # Generate base noise
    noise_level = 0.1
    spectrogram = noise_level * np.random.rand(len(freqs), len(t))
    
    # Add chirp signals
    chirps_info = []
    
    # Chirp 1: Low to high frequency
    t1_start, t1_end = 0.5, 1.5
    f1_start, f1_end = 50, 200
    start_idx = int(t1_start * fs)
    end_idx = int(t1_end * fs)
    f1_start_idx = int(f1_start * len(freqs) / (fs/2))
    f1_end_idx = int(f1_end * len(freqs) / (fs/2))
    
    for i, t_idx in enumerate(range(start_idx, end_idx)):
        f_idx = int(f1_start_idx + (f1_end_idx - f1_start_idx) * i / (end_idx - start_idx))
        if 0 <= f_idx < len(freqs):
            spectrogram[f_idx:f_idx+3, t_idx] += 0.8
    
    chirps_info.append({
        'start_time': t1_start, 'end_time': t1_end,
        'start_freq': f1_start, 'end_freq': f1_end
    })
    
    # Chirp 2: High to low frequency
    t2_start, t2_end = 2.0, 3.0
    f2_start, f2_end = 300, 100
    start_idx = int(t2_start * fs)
    end_idx = int(t2_end * fs)
    f2_start_idx = int(f2_start * len(freqs) / (fs/2))
    f2_end_idx = int(f2_end * len(freqs) / (fs/2))
    
    for i, t_idx in enumerate(range(start_idx, end_idx)):
        f_idx = int(f2_start_idx + (f2_end_idx - f2_start_idx) * i / (end_idx - start_idx))
        if 0 <= f_idx < len(freqs):
            spectrogram[f_idx:f_idx+3, t_idx] += 0.9
    
    chirps_info.append({
        'start_time': t2_start, 'end_time': t2_end,
        'start_freq': f2_start, 'end_freq': f2_end
    })
    
    # Chirp 3: Weak chirp
    t3_start, t3_end = 3.2, 3.8
    f3_start, f3_end = 150, 250
    start_idx = int(t3_start * fs)
    end_idx = int(t3_end * fs)
    f3_start_idx = int(f3_start * len(freqs) / (fs/2))
    f3_end_idx = int(f3_end * len(freqs) / (fs/2))
    
    for i, t_idx in enumerate(range(start_idx, end_idx)):
        f_idx = int(f3_start_idx + (f3_end_idx - f3_start_idx) * i / (end_idx - start_idx))
        if 0 <= f_idx < len(freqs):
            spectrogram[f_idx:f_idx+2, t_idx] += 0.4
    
    chirps_info.append({
        'start_time': t3_start, 'end_time': t3_end,
        'start_freq': f3_start, 'end_freq': f3_end
    })
    
    return spectrogram, chirps_info

def run_tests():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        spectrogram, true_chirps = create_data()
        input_file = "test_spectrogram.npy"
        output_file = "detected_chirps.json"
        
        np.save(input_file, spectrogram)
        
        # Test 1: Basic execution
        try:
            result = subprocess.run([
                sys.executable, "generated.py",
                "--input", input_file,
                "--output", output_file,
                "--threshold", "0.3"
            ], capture_output=True, text=True, timeout=30)
            print("PASS: Script executes without errors")
            execution_success = True
        except Exception as e:
            print(f"FAIL: Script execution failed: {e}")
            execution_success = False
            return
        
        # Test 2: Output file creation
        if os.path.exists(output_file):
            print("PASS: Output JSON file created")
        else:
            print("FAIL: Output JSON file not created")
            return
        
        # Test 3: JSON file validity
        try:
            with open(output_file, 'r') as f:
                detections = json.load(f)
            print("PASS: Output JSON file is valid")
            json_valid = True
        except:
            print("FAIL: Output JSON file is invalid")
            json_valid = False
            return
        
        # Test 4: JSON structure
        if isinstance(detections, list) and len(detections) > 0:
            print("PASS: JSON contains detection list")
        else:
            print("FAIL: JSON does not contain proper detection list")
            return
        
        # Test 5: Detection fields
        required_fields = ['start_time', 'end_time', 'start_frequency', 'end_frequency', 'confidence']
        first_detection = detections[0]
        has_all_fields = all(field in first_detection for field in required_fields)
        if has_all_fields:
            print("PASS: Detections contain required fields")
        else:
            print("FAIL: Detections missing required fields")
        
        # Test 6: Confidence values
        confidences = [d.get('confidence', 0) for d in detections]
        valid_confidences = all(0 <= c <= 1 for c in confidences)
        if valid_confidences:
            print("PASS: Confidence values in valid range [0,1]")
        else:
            print("FAIL: Confidence values outside valid range")
        
        # Test 7: Threshold filtering
        above_threshold = all(d.get('confidence', 0) >= 0.3 for d in detections)
        if above_threshold:
            print("PASS: All detections above threshold")
        else:
            print("FAIL: Some detections below threshold")
        
        # Test 8: Time ordering
        times_valid = all(d.get('start_time', 0) < d.get('end_time', 1) for d in detections)
        if times_valid:
            print("PASS: Start times before end times")
        else:
            print("FAIL: Invalid time ordering")
        
        # Test 9: Visualization file
        plot_file = output_file.replace('.json', '_detected.png')
        if os.path.exists(plot_file):
            print("PASS: Visualization PNG file created")
        else:
            print("FAIL: Visualization PNG file not created")
        
        # Test 10: Standard output
        stdout_output = result.stdout
        has_count = "detected" in stdout_output.lower() or "chirp" in stdout_output.lower()
        if has_count:
            print("PASS: Statistics printed to stdout")
        else:
            print("FAIL: No statistics in stdout")
        
        # Test 11: Detection count reasonable
        num_detections = len(detections)
        if 1 <= num_detections <= 10:
            print("PASS: Reasonable number of detections")
        else:
            print("FAIL: Unreasonable number of detections")
        
        # Test 12: Different threshold test
        try:
            result2 = subprocess.run([
                sys.executable, "generated.py",
                "--input", input_file,
                "--output", "high_thresh.json",
                "--threshold", "0.7"
            ], capture_output=True, text=True, timeout=30)
            
            with open("high_thresh.json", 'r') as f:
                high_thresh_detections = json.load(f)
            
            if len(high_thresh_detections) <= len(detections):
                print("PASS: Higher threshold reduces detections")
            else:
                print("FAIL: Higher threshold should reduce detections")
        except:
            print("FAIL: High threshold test failed")
        
        # Test 13: Frequency values reasonable
        freq_valid = all(
            0 <= d.get('start_frequency', -1) <= 500 and 
            0 <= d.get('end_frequency', -1) <= 500 
            for d in detections
        )
        if freq_valid:
            print("PASS: Frequency values in reasonable range")
        else:
            print("FAIL: Frequency values unreasonable")
        
        # Test 14: Time values reasonable
        time_valid = all(
            0 <= d.get('start_time', -1) <= 4 and 
            0 <= d.get('end_time', -1) <= 4 
            for d in detections
        )
        if time_valid:
            print("PASS: Time values in reasonable range")
        else:
            print("FAIL: Time values unreasonable")
        
        # Test 15: Error handling
        try:
            result_error = subprocess.run([
                sys.executable, "generated.py",
                "--input", "nonexistent.npy",
                "--output", "error_test.json"
            ], capture_output=True, text=True, timeout=30)
            
            if result_error.returncode != 0:
                print("PASS: Proper error handling for missing input")
            else:
                print("FAIL: Should handle missing input file error")
        except:
            print("PASS: Proper error handling for missing input")
        
        # SCORE 1: Detection accuracy
        detection_score = 0.0
        if json_valid and len(detections) > 0:
            # Simple overlap-based scoring
            matches = 0
            for true_chirp in true_chirps:
                for detection in detections:
                    time_overlap = (
                        detection.get('start_time', 0) < true_chirp['end_time'] and
                        detection.get('end_time', 0) > true_chirp['start_time']
                    )
                    if time_overlap:
                        matches += 1
                        break
            detection_score = min(matches / len(true_chirps), 1.0)
        
        print(f"SCORE: Detection accuracy: {detection_score:.3f}")
        
        # SCORE 2: Output quality
        quality_score = 0.0
        if execution_success and json_valid:
            quality_components = [
                has_all_fields,
                valid_confidences,
                above_threshold,
                times_valid,
                os.path.exists(plot_file),
                has_count
            ]
            quality_score = sum(quality_components) / len(quality_components)
        
        print(f"SCORE: Output quality: {quality_score:.3f}")

if __name__ == "__main__":
    run_tests()
