import subprocess
import tempfile
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

def create_data():
    """Create synthetic test parameters"""
    return {
        'days': 30,
        'seed': 42,
        'expected_fog_categories': ['Dense Fog', 'Moderate Fog', 'Light Fog', 'Mist', 'Clear'],
        'expected_time_periods': ['night', 'morning', 'afternoon', 'evening']
    }

def run_test():
    test_data = create_data()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Test file paths
        json_file = "visibility_analysis.json"
        csv_file = "visibility_data.csv"
        
        # Run the script with various argument name possibilities
        cmd_variants = [
            ["python", "generated.py", "--days", str(test_data['days']), "--output-json", json_file, "--output-csv", csv_file, "--seed", str(test_data['seed'])],
            ["python", "generated.py", "--days", str(test_data['days']), "--output_json", json_file, "--output_csv", csv_file, "--seed", str(test_data['seed'])],
            ["python", "generated.py", "-d", str(test_data['days']), "--output-json", json_file, "--output-csv", csv_file, "-s", str(test_data['seed'])]
        ]
        
        success = False
        for cmd in cmd_variants:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd="/tmp")
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed")
            return
        
        # Load and validate outputs
        try:
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            df = pd.read_csv(csv_file)
        except Exception as e:
            print(f"FAIL: Could not load output files: {e}")
            return
        
        # Test 1: Basic file creation
        print("PASS: Output files created successfully" if os.path.exists(json_file) and os.path.exists(csv_file) else "FAIL: Output files not created")
        
        # Test 2: CSV data structure
        required_csv_cols = ['visibility_m', 'humidity_pct', 'temperature_c', 'wind_speed_ms', 'fog_category']
        csv_cols_present = all(col in df.columns or any(req in col.lower() for req in ['visibility', 'humidity', 'temperature', 'wind', 'fog']) for col in required_csv_cols)
        print("PASS: CSV contains required columns" if csv_cols_present else "FAIL: CSV missing required columns")
        
        # Test 3: Data volume
        expected_hours = test_data['days'] * 24
        data_volume_correct = len(df) == expected_hours
        print(f"PASS: Correct number of hourly records ({len(df)})" if data_volume_correct else f"FAIL: Expected {expected_hours} records, got {len(df)}")
        
        # Test 4: Fog categories present
        fog_categories_present = 'fog_statistics' in json_data and isinstance(json_data['fog_statistics'], dict)
        print("PASS: Fog statistics section present" if fog_categories_present else "FAIL: Fog statistics section missing")
        
        # Test 5: Visibility categories
        if fog_categories_present:
            fog_stats = json_data['fog_statistics']
            has_categories = len(fog_stats) >= 3  # At least some fog categories
            print("PASS: Multiple fog categories analyzed" if has_categories else "FAIL: Insufficient fog categories")
        else:
            print("FAIL: Cannot verify fog categories")
        
        # Test 6: Correlation analysis
        correlation_present = 'correlation_analysis' in json_data and isinstance(json_data['correlation_analysis'], dict)
        print("PASS: Correlation analysis present" if correlation_present else "FAIL: Correlation analysis missing")
        
        # Test 7: Diurnal analysis
        diurnal_present = 'diurnal_analysis' in json_data and isinstance(json_data['diurnal_analysis'], dict)
        print("PASS: Diurnal analysis present" if diurnal_present else "FAIL: Diurnal analysis missing")
        
        # Test 8: Time period analysis
        if diurnal_present:
            time_periods = json_data['diurnal_analysis']
            has_time_periods = any(period in str(time_periods).lower() for period in ['night', 'morning', 'afternoon', 'evening'])
            print("PASS: Time period analysis included" if has_time_periods else "FAIL: Time period analysis missing")
        else:
            print("FAIL: Cannot verify time period analysis")
        
        # Test 9: Trend analysis
        trend_present = 'trend_analysis' in json_data and isinstance(json_data['trend_analysis'], dict)
        print("PASS: Trend analysis present" if trend_present else "FAIL: Trend analysis missing")
        
        # Test 10: Visibility range validation
        visibility_col = None
        for col in df.columns:
            if 'visibility' in col.lower():
                visibility_col = col
                break
        
        if visibility_col:
            vis_range_valid = df[visibility_col].min() >= 0 and df[visibility_col].max() <= 50000
            print("PASS: Visibility values in realistic range" if vis_range_valid else "FAIL: Visibility values unrealistic")
        else:
            print("FAIL: Visibility column not found")
        
        # Test 11: Fog event detection
        fog_col = None
        for col in df.columns:
            if 'fog' in col.lower() or 'category' in col.lower():
                fog_col = col
                break
        
        if fog_col:
            has_fog_events = df[fog_col].nunique() > 1
            print("PASS: Multiple visibility categories detected" if has_fog_events else "FAIL: No category variation detected")
        else:
            print("FAIL: Fog category column not found")
        
        # Test 12: Meteorological parameters
        met_params = ['humidity', 'temperature', 'wind']
        met_cols_present = sum(1 for param in met_params if any(param in col.lower() for col in df.columns)) >= 2
        print("PASS: Meteorological parameters present" if met_cols_present else "FAIL: Insufficient meteorological parameters")
        
        # Test 13: JSON structure completeness
        required_sections = ['fog_statistics', 'correlation_analysis', 'diurnal_analysis', 'trend_analysis']
        sections_present = sum(1 for section in required_sections if section in json_data) >= 3
        print("PASS: JSON contains required analysis sections" if sections_present else "FAIL: JSON missing required sections")
        
        # Test 14: Numerical validity
        if correlation_present:
            corr_data = json_data['correlation_analysis']
            correlations_valid = True
            for key, value in corr_data.items():
                if isinstance(value, (int, float)) and (value < -1 or value > 1):
                    correlations_valid = False
                    break
            print("PASS: Correlation values in valid range" if correlations_valid else "FAIL: Invalid correlation values")
        else:
            print("FAIL: Cannot validate correlation values")
        
        # Test 15: Data consistency
        if visibility_col and fog_col:
            # Check if fog classification is consistent with visibility thresholds
            fog_data = df[[visibility_col, fog_col]].dropna()
            if len(fog_data) > 0:
                consistency_check = True
                # Basic consistency: very low visibility should be classified as fog
                low_vis_data = fog_data[fog_data[visibility_col] < 500]
                if len(low_vis_data) > 0:
                    fog_classifications = low_vis_data[fog_col].astype(str).str.lower()
                    has_fog_label = fog_classifications.str.contains('fog|dense|moderate').any()
                    consistency_check = has_fog_label
                print("PASS: Fog classification consistent with visibility" if consistency_check else "FAIL: Inconsistent fog classification")
            else:
                print("FAIL: No valid data for consistency check")
        else:
            print("FAIL: Cannot perform consistency check")
        
        # SCORE 1: Data completeness and structure quality
        structure_score = 0.0
        if os.path.exists(json_file) and os.path.exists(csv_file):
            structure_score += 0.3
        if csv_cols_present:
            structure_score += 0.2
        if data_volume_correct:
            structure_score += 0.2
        if sections_present:
            structure_score += 0.3
        
        print(f"SCORE: Data structure quality: {structure_score:.2f}")
        
        # SCORE 2: Analysis depth and accuracy
        analysis_score = 0.0
        if fog_categories_present and has_categories:
            analysis_score += 0.25
        if correlation_present:
            analysis_score += 0.25
        if diurnal_present and has_time_periods:
            analysis_score += 0.25
        if trend_present:
            analysis_score += 0.25
        
        print(f"SCORE: Analysis completeness: {analysis_score:.2f}")

if __name__ == "__main__":
    run_test()
