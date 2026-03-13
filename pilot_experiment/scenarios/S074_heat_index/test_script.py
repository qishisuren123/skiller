import subprocess
import tempfile
import os
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import sys

def create_data(temp_dir):
    """Generate synthetic temperature and humidity data"""
    # Generate 40 years of daily data for robust climatology
    start_date = datetime(1980, 1, 1)
    end_date = datetime(2020, 12, 31)
    dates = pd.date_range(start_date, end_date, freq='D')
    
    np.random.seed(42)
    n_days = len(dates)
    
    # Generate realistic temperature data with seasonal cycle
    day_of_year = dates.dayofyear
    temp_seasonal = 20 + 15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
    temp_noise = np.random.normal(0, 5, n_days)
    
    # Add some warming trend and heat wave events
    year_trend = 0.02 * (dates.year - 1980)
    
    # Insert some extreme heat events
    extreme_days = np.random.choice(n_days, size=200, replace=False)
    temp_extremes = np.zeros(n_days)
    temp_extremes[extreme_days] = np.random.exponential(8, 200)
    
    temperatures = temp_seasonal + temp_noise + year_trend + temp_extremes
    temperatures = np.clip(temperatures, -10, 50)  # Realistic bounds
    
    # Generate humidity data (correlated with temperature)
    humidity_base = 60 + 20 * np.sin(2 * np.pi * (day_of_year - 120) / 365)
    humidity_noise = np.random.normal(0, 10, n_days)
    # Inverse correlation with temperature for realism
    humidity_temp_effect = -0.5 * (temperatures - np.mean(temperatures))
    humidity = humidity_base + humidity_noise + humidity_temp_effect
    humidity = np.clip(humidity, 20, 95)  # Realistic humidity bounds
    
    # Create temperature data file
    temp_df = pd.DataFrame({
        'datetime': dates,
        'temperature': temperatures
    })
    temp_file = os.path.join(temp_dir, 'temperature.csv')
    temp_df.to_csv(temp_file, index=False)
    
    # Create humidity data file
    humidity_df = pd.DataFrame({
        'datetime': dates,
        'humidity': humidity
    })
    humidity_file = os.path.join(temp_dir, 'humidity.csv')
    humidity_df.to_csv(humidity_file, index=False)
    
    return temp_file, humidity_file

def heat_index_reference(temp_c, humidity):
    """Reference implementation of heat index calculation"""
    # Convert to Fahrenheit for NWS formula
    temp_f = temp_c * 9/5 + 32
    
    # Simple formula for initial estimate
    hi = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (humidity * 0.094))
    
    # Use complex formula if conditions warrant
    if hi >= 80:
        hi = (-42.379 + 2.04901523 * temp_f + 10.14333127 * humidity
              - 0.22475541 * temp_f * humidity - 6.83783e-3 * temp_f**2
              - 5.481717e-2 * humidity**2 + 1.22874e-3 * temp_f**2 * humidity
              + 8.5282e-4 * temp_f * humidity**2 - 1.99e-6 * temp_f**2 * humidity**2)
        
        # Adjustments
        if humidity < 13 and 80 <= temp_f <= 112:
            adjustment = ((13 - humidity) / 4) * np.sqrt((17 - abs(temp_f - 95)) / 17)
            hi -= adjustment
        elif humidity > 85 and 80 <= temp_f <= 87:
            adjustment = ((humidity - 85) / 10) * ((87 - temp_f) / 5)
            hi += adjustment
    
    # Convert back to Celsius
    return (hi - 32) * 5/9

def test_script():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test data
        temp_file, humidity_file = create_data(temp_dir)
        
        # Define output files
        output_timeseries = os.path.join(temp_dir, 'heat_index_timeseries.csv')
        output_heatwaves = os.path.join(temp_dir, 'heatwaves.json')
        
        # Test different argument name variations
        possible_args = [
            ['--temp-data', '--humidity-data', '--output-timeseries', '--output-heatwaves'],
            ['--temp_data', '--humidity_data', '--output_timeseries', '--output_heatwaves'],
            ['--temperature', '--humidity', '--timeseries', '--heatwaves'],
            ['--temp', '--humid', '--output-ts', '--output-hw']
        ]
        
        success = False
        for args in possible_args:
            try:
                cmd = [
                    'python', 'generated.py',
                    args[0], temp_file,
                    args[1], humidity_file,
                    args[2], output_timeseries,
                    args[3], output_heatwaves,
                    '--baseline-years', '30',
                    '--heatwave-threshold', '90',
                    '--min-duration', '3'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed")
            return
        
        # Load input data for validation
        temp_df = pd.read_csv(temp_file)
        humidity_df = pd.read_csv(humidity_file)
        temp_df['datetime'] = pd.to_datetime(temp_df['datetime'])
        humidity_df['datetime'] = pd.to_datetime(humidity_df['datetime'])
        
        # Merge data
        data = pd.merge(temp_df, humidity_df, on='datetime')
        
        # Calculate reference heat index
        reference_hi = [heat_index_reference(t, h) for t, h in zip(data['temperature'], data['humidity'])]
        
        # Test 1: Output files exist
        if os.path.exists(output_timeseries) and os.path.exists(output_heatwaves):
            print("PASS: Output files created")
        else:
            print("FAIL: Output files not created")
            return
        
        # Load outputs
        try:
            timeseries_df = pd.read_csv(output_timeseries)
            with open(output_heatwaves, 'r') as f:
                heatwaves_data = json.load(f)
        except:
            print("FAIL: Could not load output files")
            return
        
        print("PASS: Output files readable")
        
        # Test 2: Timeseries has correct structure
        required_cols = ['datetime', 'heat_index']
        if all(col in timeseries_df.columns for col in required_cols):
            print("PASS: Timeseries has required columns")
        else:
            print("FAIL: Timeseries missing required columns")
        
        # Test 3: Correct number of records
        if len(timeseries_df) == len(data):
            print("PASS: Correct number of timeseries records")
        else:
            print("FAIL: Incorrect number of timeseries records")
        
        # Test 4: Heat index calculation accuracy
        if 'heat_index' in timeseries_df.columns:
            calculated_hi = timeseries_df['heat_index'].values
            # Allow for reasonable tolerance in heat index calculation
            hi_accuracy = np.mean(np.abs(calculated_hi - reference_hi) < 2.0)
            if hi_accuracy > 0.95:
                print("PASS: Heat index calculation accurate")
            else:
                print("FAIL: Heat index calculation inaccurate")
        else:
            print("FAIL: Heat index column missing")
            hi_accuracy = 0.0
        
        # Test 5: Heat wave events structure
        required_hw_fields = ['events', 'parameters', 'statistics']
        if all(field in heatwaves_data for field in required_hw_fields):
            print("PASS: Heat wave data has required structure")
        else:
            print("FAIL: Heat wave data missing required fields")
        
        # Test 6: Heat wave events have required properties
        if 'events' in heatwaves_data and len(heatwaves_data['events']) > 0:
            event = heatwaves_data['events'][0]
            required_event_fields = ['start_date', 'end_date', 'duration', 'max_heat_index']
            if all(field in event for field in required_event_fields):
                print("PASS: Heat wave events have required properties")
            else:
                print("FAIL: Heat wave events missing required properties")
        else:
            print("FAIL: No heat wave events detected")
        
        # Test 7: Minimum duration constraint
        if 'events' in heatwaves_data:
            min_duration_satisfied = True
            for event in heatwaves_data['events']:
                if 'duration' in event and event['duration'] < 3:
                    min_duration_satisfied = False
                    break
            if min_duration_satisfied:
                print("PASS: Minimum duration constraint satisfied")
            else:
                print("FAIL: Minimum duration constraint violated")
        else:
            print("FAIL: Cannot check duration constraint")
        
        # Test 8: Statistical analysis present
        if 'statistics' in heatwaves_data:
            stats = heatwaves_data['statistics']
            required_stats = ['total_events', 'mean_duration']
            if all(stat in stats for stat in required_stats):
                print("PASS: Statistical analysis present")
            else:
                print("FAIL: Statistical analysis incomplete")
        else:
            print("FAIL: Statistical analysis missing")
        
        # Test 9: Temporal trends analysis
        trend_present = False
        if 'statistics' in heatwaves_data:
            stats = heatwaves_data['statistics']
            trend_fields = ['frequency_trend', 'duration_trend', 'intensity_trend']
            if any(field in stats for field in trend_fields):
                trend_present = True
        
        if trend_present:
            print("PASS: Temporal trends analysis present")
        else:
            print("FAIL: Temporal trends analysis missing")
        
        # Test 10: Parameters recorded
        if 'parameters' in heatwaves_data:
            params = heatwaves_data['parameters']
            if 'baseline_years' in params and 'heatwave_threshold' in params:
                print("PASS: Analysis parameters recorded")
            else:
                print("FAIL: Analysis parameters incomplete")
        else:
            print("FAIL: Analysis parameters missing")
        
        # Test 11: Reasonable number of heat waves detected
        if 'events' in heatwaves_data:
            n_events = len(heatwaves_data['events'])
            if 5 <= n_events <= 200:  # Reasonable range for 40 years
                print("PASS: Reasonable number of heat waves detected")
            else:
                print("FAIL: Unreasonable number of heat waves detected")
        else:
            print("FAIL: Cannot assess heat wave count")
        
        # Test 12: Heat index values are reasonable
        if 'heat_index' in timeseries_df.columns:
            hi_values = timeseries_df['heat_index'].values
            if np.all(hi_values >= -20) and np.all(hi_values <= 60):
                print("PASS: Heat index values in reasonable range")
            else:
                print("FAIL: Heat index values out of reasonable range")
        else:
            print("FAIL: Cannot assess heat index range")
        
        # Test 13: Datetime handling
        try:
            timeseries_df['datetime'] = pd.to_datetime(timeseries_df['datetime'])
            date_range_correct = (timeseries_df['datetime'].min().year >= 1980 and 
                                timeseries_df['datetime'].max().year <= 2020)
            if date_range_correct:
                print("PASS: Datetime handling correct")
            else:
                print("FAIL: Datetime range incorrect")
        except:
            print("FAIL: Datetime parsing failed")
        
        # Test 14: Heat wave intensity metrics
        intensity_metrics_present = False
        if 'events' in heatwaves_data and len(heatwaves_data['events']) > 0:
            event = heatwaves_data['events'][0]
            intensity_fields = ['mean_heat_index', 'max_heat_index', 'cumulative_excess']
            if any(field in event for field in intensity_fields):
                intensity_metrics_present = True
        
        if intensity_metrics_present:
            print("PASS: Heat wave intensity metrics present")
        else:
            print("FAIL: Heat wave intensity metrics missing")
        
        # Test 15: Confidence intervals or significance testing
        significance_testing = False
        if 'statistics' in heatwaves_data:
            stats = heatwaves_data['statistics']
            sig_fields = ['confidence_interval', 'p_value', 'significance', 'trend_significance']
            if any(field in stats for field in sig_fields):
                significance_testing = True
        
        if significance_testing:
            print("PASS: Statistical significance testing present")
        else:
            print("FAIL: Statistical significance testing missing")
        
        # SCORE 1: Heat index calculation accuracy
        print(f"SCORE: Heat index accuracy: {hi_accuracy:.3f}")
        
        # SCORE 2: Analysis completeness
        completeness_score = 0.0
        total_components = 6
        
        # Component scores
        if os.path.exists(output_timeseries) and os.path.exists(output_heatwaves):
            completeness_score += 1.0
        if 'events' in heatwaves_data and len(heatwaves_data['events']) > 0:
            completeness_score += 1.0
        if 'statistics' in heatwaves_data:
            completeness_score += 1.0
        if trend_present:
            completeness_score += 1.0
        if intensity_metrics_present:
            completeness_score += 1.0
        if significance_testing:
            completeness_score += 1.0
        
        completeness_score /= total_components
        print(f"SCORE: Analysis completeness: {completeness_score:.3f}")

if __name__ == "__main__":
    test_script()
