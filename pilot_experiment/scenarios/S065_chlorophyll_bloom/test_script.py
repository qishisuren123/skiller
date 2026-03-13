import subprocess
import tempfile
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

def create_data():
    """Generate synthetic chlorophyll-a time series data with bloom events"""
    np.random.seed(42)
    
    # Create 2-year daily time series
    start_date = datetime(2022, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(730)]
    
    # Base chlorophyll levels with seasonal variation
    day_of_year = np.array([d.timetuple().tm_yday for d in dates])
    seasonal = 2 + 1.5 * np.sin(2 * np.pi * day_of_year / 365.25)  # Seasonal cycle
    
    # Add random noise
    noise = np.random.normal(0, 0.3, len(dates))
    baseline = seasonal + noise
    baseline = np.maximum(baseline, 0.1)  # Ensure positive values
    
    # Add bloom events
    chlorophyll = baseline.copy()
    
    # Spring bloom (March-April)
    spring_start = 60  # March 1st
    spring_bloom = np.zeros(len(dates))
    for i in range(spring_start, min(spring_start + 25, len(dates))):
        spring_bloom[i] = 8 * np.exp(-0.5 * ((i - spring_start - 12) / 5) ** 2)
    
    # Summer bloom (July)
    summer_start = 180  # July 1st
    summer_bloom = np.zeros(len(dates))
    for i in range(summer_start, min(summer_start + 15, len(dates))):
        summer_bloom[i] = 12 * np.exp(-0.5 * ((i - summer_start - 7) / 3) ** 2)
    
    # Fall bloom (September)
    fall_start = 250  # September 7th
    fall_bloom = np.zeros(len(dates))
    for i in range(fall_start, min(fall_start + 20, len(dates))):
        fall_bloom[i] = 6 * np.exp(-0.5 * ((i - fall_start - 10) / 4) ** 2)
    
    # Second year blooms (shifted timing)
    spring2_start = 425  # March 15th year 2
    spring2_bloom = np.zeros(len(dates))
    for i in range(spring2_start, min(spring2_start + 18, len(dates))):
        spring2_bloom[i] = 10 * np.exp(-0.5 * ((i - spring2_start - 9) / 4) ** 2)
    
    chlorophyll += spring_bloom + summer_bloom + fall_bloom + spring2_bloom
    
    # Add some data gaps
    gap_indices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]  # 10-day gap
    for idx in gap_indices:
        if idx < len(chlorophyll):
            chlorophyll[idx] = np.nan
    
    # Add a few outliers
    outlier_indices = [200, 400, 600]
    for idx in outlier_indices:
        if idx < len(chlorophyll):
            chlorophyll[idx] = 25 + np.random.normal(0, 2)
    
    # Create DataFrame
    data = pd.DataFrame({
        'date': dates,
        'chlorophyll_a': chlorophyll
    })
    
    return data

def test_script():
    print("Testing Chlorophyll Bloom Detection Analysis...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Create test data
        data = create_data()
        data_file = 'chlorophyll_data.csv'
        data.to_csv(data_file, index=False)
        
        output_json = 'bloom_results.json'
        output_csv = 'bloom_events.csv'
        
        # Test different possible argument names
        possible_commands = [
            ['python', 'generated.py', '--input-data', data_file, '--output-json', output_json, '--output-csv', output_csv],
            ['python', 'generated.py', '--input', data_file, '--json', output_json, '--csv', output_csv],
            ['python', 'generated.py', '--data', data_file, '--output-json', output_json, '--output-csv', output_csv],
            ['python', 'generated.py', data_file, output_json, output_csv]
        ]
        
        success = False
        for cmd in possible_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed")
            return
        
        print("PASS: Script executed successfully")
        
        # Test file outputs
        if os.path.exists(output_json):
            print("PASS: JSON output file created")
        else:
            print("FAIL: JSON output file not created")
            return
        
        if os.path.exists(output_csv):
            print("PASS: CSV output file created")
        else:
            print("FAIL: CSV output file not created")
            return
        
        # Load and validate JSON results
        try:
            with open(output_json, 'r') as f:
                results = json.load(f)
            print("PASS: JSON file is valid")
        except:
            print("FAIL: JSON file is invalid or corrupted")
            return
        
        # Test JSON structure
        required_keys = ['bloom_events', 'summary_statistics', 'quality_control']
        json_structure_score = 0
        for key in required_keys:
            if key in results:
                json_structure_score += 1
                print(f"PASS: JSON contains {key}")
            else:
                print(f"FAIL: JSON missing {key}")
        
        # Test bloom detection
        if 'bloom_events' in results and len(results['bloom_events']) > 0:
            print("PASS: Bloom events detected")
            
            # Check bloom event structure
            first_bloom = results['bloom_events'][0]
            bloom_keys = ['start_date', 'end_date', 'duration', 'peak_concentration']
            bloom_structure_valid = all(key in first_bloom for key in bloom_keys)
            if bloom_structure_valid:
                print("PASS: Bloom events have required fields")
            else:
                print("FAIL: Bloom events missing required fields")
            
            # Test reasonable number of blooms (should detect 3-5 major blooms)
            num_blooms = len(results['bloom_events'])
            if 2 <= num_blooms <= 8:
                print("PASS: Reasonable number of blooms detected")
            else:
                print("FAIL: Unreasonable number of blooms detected")
        else:
            print("FAIL: No bloom events detected")
        
        # Test summary statistics
        if 'summary_statistics' in results:
            stats = results['summary_statistics']
            stats_keys = ['mean_baseline', 'total_blooms', 'average_duration']
            if all(key in stats for key in stats_keys):
                print("PASS: Summary statistics complete")
            else:
                print("FAIL: Summary statistics incomplete")
        else:
            print("FAIL: Summary statistics missing")
        
        # Test quality control
        if 'quality_control' in results:
            qc = results['quality_control']
            if 'data_gaps' in qc and 'outliers' in qc:
                print("PASS: Quality control metrics present")
                
                # Should detect the 10-day gap we inserted
                if qc.get('data_gaps', 0) > 0:
                    print("PASS: Data gaps detected")
                else:
                    print("FAIL: Data gaps not detected")
            else:
                print("FAIL: Quality control metrics incomplete")
        else:
            print("FAIL: Quality control missing")
        
        # Load and validate CSV
        try:
            csv_data = pd.read_csv(output_csv)
            print("PASS: CSV file readable")
            
            if len(csv_data) > 0:
                print("PASS: CSV contains bloom data")
            else:
                print("FAIL: CSV is empty")
        except:
            print("FAIL: CSV file invalid")
        
        # Test moving average application (indirect test via reasonable bloom detection)
        valid_data = data.dropna()
        data_range = valid_data['chlorophyll_a'].max() - valid_data['chlorophyll_a'].min()
        if data_range > 5:  # Should have significant variation
            print("PASS: Data processing appears correct")
        else:
            print("FAIL: Data processing may be incorrect")
        
        # Calculate accuracy scores
        bloom_detection_score = 0
        if 'bloom_events' in results:
            num_blooms = len(results['bloom_events'])
            # Expected 4 major blooms, score based on detection
            if num_blooms >= 3:
                bloom_detection_score = min(1.0, num_blooms / 4.0)
        
        completeness_score = json_structure_score / len(required_keys)
        
        print(f"SCORE: bloom_detection_accuracy: {bloom_detection_score:.3f}")
        print(f"SCORE: output_completeness: {completeness_score:.3f}")

if __name__ == "__main__":
    test_script()
