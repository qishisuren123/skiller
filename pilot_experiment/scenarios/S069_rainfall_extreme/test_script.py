import subprocess
import json
import tempfile
import os
import numpy as np
import sys

def create_data():
    """Generate synthetic daily precipitation data"""
    np.random.seed(42)
    
    # Generate 8 years of daily data (2920 days)
    n_days = 8 * 365
    
    # Base precipitation: mostly low values with occasional high values
    precip = np.random.exponential(scale=2.0, size=n_days)
    
    # Add some extreme events
    extreme_indices = np.random.choice(n_days, size=20, replace=False)
    precip[extreme_indices] = np.random.uniform(25, 80, size=20)
    
    # Add some missing data (negative values)
    missing_indices = np.random.choice(n_days, size=10, replace=False)
    precip[missing_indices] = -1.0
    
    # Round to 1 decimal place
    precip = np.round(precip, 1)
    
    return precip.tolist()

def run_test():
    test_data = create_data()
    data_str = ','.join(map(str, test_data))
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Test the script
        cmd = [
            sys.executable, 'generated.py',
            '--input-data', data_str,
            '--start-year', '2000',
            '--output', 'results.json'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
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
        
        # Check if output file exists
        if not os.path.exists('results.json'):
            print("FAIL: Output JSON file not created")
            return
        print("PASS: Output JSON file created")
        
        # Load and validate JSON
        try:
            with open('results.json', 'r') as f:
                results = json.load(f)
        except json.JSONDecodeError:
            print("FAIL: Invalid JSON format")
            return
        print("PASS: Valid JSON format")
        
        # Check required keys
        required_keys = ['annual_maxima', 'return_periods', 'extreme_events', 'statistics']
        for key in required_keys:
            if key not in results:
                print(f"FAIL: Missing key '{key}' in JSON output")
                return
        print("PASS: All required JSON keys present")
        
        # Validate annual maxima
        annual_maxima = results['annual_maxima']
        if not isinstance(annual_maxima, list) or len(annual_maxima) == 0:
            print("FAIL: Annual maxima should be non-empty list")
            return
        print("PASS: Annual maxima is non-empty list")
        
        # Should have 8 complete years
        if len(annual_maxima) != 8:
            print(f"FAIL: Expected 8 annual maxima, got {len(annual_maxima)}")
            return
        print("PASS: Correct number of annual maxima (8 years)")
        
        # Check return periods
        return_periods = results['return_periods']
        if not isinstance(return_periods, list) or len(return_periods) != len(annual_maxima):
            print("FAIL: Return periods should match annual maxima length")
            return
        print("PASS: Return periods match annual maxima length")
        
        # Validate return period calculation (Weibull formula)
        sorted_maxima = sorted(annual_maxima, reverse=True)
        expected_return_periods = [(8+1)/(i+1) for i in range(8)]
        
        # Check if return periods are reasonable (within 10% tolerance)
        actual_sorted_periods = [return_periods[annual_maxima.index(val)] for val in sorted_maxima]
        period_errors = [abs(a - e) / e for a, e in zip(actual_sorted_periods, expected_return_periods)]
        if max(period_errors) > 0.1:
            print("FAIL: Return periods don't follow Weibull formula")
            return
        print("PASS: Return periods follow Weibull formula")
        
        # Check extreme events
        extreme_events = results['extreme_events']
        if not isinstance(extreme_events, list):
            print("FAIL: Extreme events should be a list")
            return
        print("PASS: Extreme events is a list")
        
        # Find 10-year return period threshold
        ten_year_threshold = None
        for i, period in enumerate(return_periods):
            if abs(period - 10.0) < 1.0:  # Close to 10 years
                ten_year_threshold = annual_maxima[i]
                break
        
        if ten_year_threshold is None:
            # Use interpolation to estimate
            sorted_pairs = sorted(zip(annual_maxima, return_periods), key=lambda x: x[1], reverse=True)
            for i in range(len(sorted_pairs)-1):
                if sorted_pairs[i][1] >= 10.0 >= sorted_pairs[i+1][1]:
                    # Linear interpolation
                    t1, v1 = sorted_pairs[i][1], sorted_pairs[i][0]
                    t2, v2 = sorted_pairs[i+1][1], sorted_pairs[i+1][0]
                    ten_year_threshold = v1 + (v2 - v1) * (10.0 - t1) / (t2 - t1)
                    break
        
        # Check statistics
        statistics = results['statistics']
        required_stats = ['mean_annual_maximum', 'std_annual_maximum', 'percentile_95']
        for stat in required_stats:
            if stat not in statistics:
                print(f"FAIL: Missing statistic '{stat}'")
                return
        print("PASS: All required statistics present")
        
        # Validate statistics values
        mean_calc = np.mean(annual_maxima)
        if abs(statistics['mean_annual_maximum'] - mean_calc) > 0.1:
            print("FAIL: Incorrect mean annual maximum calculation")
            return
        print("PASS: Correct mean annual maximum")
        
        std_calc = np.std(annual_maxima, ddof=1)
        if abs(statistics['std_annual_maximum'] - std_calc) > 0.1:
            print("FAIL: Incorrect standard deviation calculation")
            return
        print("PASS: Correct standard deviation")
        
        # Check 95th percentile of all daily data (excluding missing)
        clean_data = [x for x in test_data if x >= 0]
        percentile_95_calc = np.percentile(clean_data, 95)
        if abs(statistics['percentile_95'] - percentile_95_calc) > 1.0:
            print("FAIL: Incorrect 95th percentile calculation")
            return
        print("PASS: Correct 95th percentile")
        
        # Check that missing data was handled (negative values excluded)
        if any(val < 0 for val in annual_maxima):
            print("FAIL: Missing data not properly excluded")
            return
        print("PASS: Missing data properly excluded")
        
        # Scoring metrics
        
        # Score 1: Accuracy of return period calculations
        period_accuracy = 1.0 - max(period_errors)
        print(f"SCORE: Return period accuracy: {period_accuracy:.3f}")
        
        # Score 2: Statistical accuracy
        mean_error = abs(statistics['mean_annual_maximum'] - mean_calc) / mean_calc
        std_error = abs(statistics['std_annual_maximum'] - std_calc) / std_calc if std_calc > 0 else 0
        percentile_error = abs(statistics['percentile_95'] - percentile_95_calc) / percentile_95_calc if percentile_95_calc > 0 else 0
        
        avg_stat_error = (mean_error + std_error + percentile_error) / 3
        statistical_accuracy = max(0, 1.0 - avg_stat_error)
        print(f"SCORE: Statistical accuracy: {statistical_accuracy:.3f}")

if __name__ == "__main__":
    run_test()
