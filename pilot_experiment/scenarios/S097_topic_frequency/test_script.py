import subprocess
import json
import tempfile
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys

def create_data():
    """Create synthetic test data - not used as data is generated internally by the script"""
    pass

def run_test():
    results = {"passed": 0, "failed": 0, "tests": []}
    
    def test_condition(name, condition, error_msg=""):
        if condition:
            results["passed"] += 1
            results["tests"].append(f"PASS: {name}")
            return True
        else:
            results["failed"] += 1
            results["tests"].append(f"FAIL: {name} - {error_msg}")
            return False
    
    # Test 1: Basic script execution
    try:
        result = subprocess.run([
            sys.executable, "generated.py", 
            "--num_docs", "500", 
            "--period", "weekly",
            "--output", "test_results.json",
            "--plot", "test_plot.png"
        ], capture_output=True, text=True, timeout=30)
        
        script_runs = result.returncode == 0
        test_condition("Script executes without errors", script_runs, result.stderr)
        
        if not script_runs:
            # If script doesn't run, skip remaining tests
            for i in range(2, 16):
                results["failed"] += 1
                results["tests"].append(f"FAIL: Test {i} - Script execution failed")
            results["tests"].append("SCORE: 0.0")
            results["tests"].append("SCORE: 0.0")
            return results
            
    except Exception as e:
        test_condition("Script executes without errors", False, str(e))
        for i in range(2, 16):
            results["failed"] += 1
            results["tests"].append(f"FAIL: Test {i} - Script execution failed")
        results["tests"].append("SCORE: 0.0")
        results["tests"].append("SCORE: 0.0")
        return results
    
    # Test 2: JSON output file exists
    json_exists = os.path.exists("test_results.json")
    test_condition("JSON output file created", json_exists)
    
    # Test 3: Plot file exists
    plot_exists = os.path.exists("test_plot.png")
    test_condition("Plot file created", plot_exists)
    
    if not json_exists:
        for i in range(4, 16):
            results["failed"] += 1
            results["tests"].append(f"FAIL: Test {i} - No JSON output to analyze")
        results["tests"].append("SCORE: 0.0")
        results["tests"].append("SCORE: 0.0")
        return results
    
    # Load and analyze JSON output
    try:
        with open("test_results.json", 'r') as f:
            data = json.load(f)
    except Exception as e:
        test_condition("JSON file is valid", False, str(e))
        for i in range(5, 16):
            results["failed"] += 1
            results["tests"].append(f"FAIL: Test {i} - Invalid JSON")
        results["tests"].append("SCORE: 0.0")
        results["tests"].append("SCORE: 0.0")
        return results
    
    # Test 4: JSON contains required top-level keys
    required_keys = ["time_series", "trends", "summary"]
    has_required_keys = all(key in data for key in required_keys)
    test_condition("JSON contains required keys (time_series, trends, summary)", has_required_keys)
    
    # Test 5: Time series data exists and has multiple topics
    time_series_valid = False
    num_topics = 0
    if "time_series" in data and isinstance(data["time_series"], dict):
        num_topics = len(data["time_series"])
        time_series_valid = num_topics >= 3
    test_condition("Time series contains at least 3 topics", time_series_valid)
    
    # Test 6: Each topic has time-series data
    topics_have_data = False
    if time_series_valid:
        topics_have_data = all(
            isinstance(topic_data, dict) and len(topic_data) > 0 
            for topic_data in data["time_series"].values()
        )
    test_condition("Each topic has time-series frequency data", topics_have_data)
    
    # Test 7: Trends classification exists
    trends_valid = False
    if "trends" in data and isinstance(data["trends"], dict):
        trend_values = set(data["trends"].values())
        expected_trends = {"increasing", "decreasing", "stable"}
        trends_valid = len(trend_values.intersection(expected_trends)) > 0
    test_condition("Trends classification contains valid categories", trends_valid)
    
    # Test 8: Summary statistics exist
    summary_valid = False
    if "summary" in data and isinstance(data["summary"], dict):
        summary_keys = set(data["summary"].keys())
        expected_summary = {"most_frequent_topic", "highest_variance_topic", "avg_topics_per_period"}
        summary_valid = len(summary_keys.intersection(expected_summary)) >= 2
    test_condition("Summary contains expected statistics", summary_valid)
    
    # Test 9: Frequency values are reasonable
    freq_reasonable = False
    if time_series_valid:
        all_frequencies = []
        for topic_data in data["time_series"].values():
            all_frequencies.extend(topic_data.values())
        if all_frequencies:
            freq_reasonable = all(isinstance(f, (int, float)) and f >= 0 for f in all_frequencies)
    test_condition("All frequency values are non-negative numbers", freq_reasonable)
    
    # Test 10: Test different period parameter
    try:
        result2 = subprocess.run([
            sys.executable, "generated.py", 
            "--num_docs", "300", 
            "--period", "daily",
            "--output", "test_daily.json",
            "--plot", "test_daily.png"
        ], capture_output=True, text=True, timeout=30)
        
        daily_works = result2.returncode == 0 and os.path.exists("test_daily.json")
        test_condition("Script works with daily period", daily_works)
    except:
        test_condition("Script works with daily period", False)
    
    # Test 11: Test monthly period
    try:
        result3 = subprocess.run([
            sys.executable, "generated.py", 
            "--num_docs", "200", 
            "--period", "monthly",
            "--output", "test_monthly.json",
            "--plot", "test_monthly.png"
        ], capture_output=True, text=True, timeout=30)
        
        monthly_works = result3.returncode == 0 and os.path.exists("test_monthly.json")
        test_condition("Script works with monthly period", monthly_works)
    except:
        test_condition("Script works with monthly period", False)
    
    # Test 12: Different document counts produce different results
    different_results = False
    if os.path.exists("test_daily.json"):
        try:
            with open("test_daily.json", 'r') as f:
                daily_data = json.load(f)
            # Check if results are structurally different
            different_results = (
                len(daily_data.get("time_series", {})) > 0 and
                daily_data.get("summary", {}) != data.get("summary", {})
            )
        except:
            pass
    test_condition("Different parameters produce different results", different_results)
    
    # Test 13: Trend analysis produces multiple trend types
    multiple_trends = False
    if trends_valid:
        unique_trends = set(data["trends"].values())
        multiple_trends = len(unique_trends) >= 2
    test_condition("Trend analysis identifies multiple trend types", multiple_trends)
    
    # Test 14: Time periods are properly formatted
    time_format_valid = False
    if time_series_valid:
        sample_topic = list(data["time_series"].keys())[0]
        time_keys = list(data["time_series"][sample_topic].keys())
        if time_keys:
            # Check if time keys look like dates
            time_format_valid = all(
                isinstance(key, str) and len(key) >= 8 
                for key in time_keys[:3]  # Check first 3
            )
    test_condition("Time periods are properly formatted", time_format_valid)
    
    # Test 15: Plot file is valid image
    plot_valid = False
    if plot_exists:
        try:
            # Check file size is reasonable (> 1KB)
            plot_size = os.path.getsize("test_plot.png")
            plot_valid = plot_size > 1000
        except:
            pass
    test_condition("Plot file is valid (reasonable size)", plot_valid)
    
    # SCORE 1: Data completeness score
    completeness_score = 0.0
    if json_exists and time_series_valid:
        # Score based on number of topics and time periods
        max_score = 1.0
        topic_score = min(num_topics / 5.0, 0.5)  # Up to 0.5 for topics
        
        # Check time periods
        if time_series_valid:
            sample_topic = list(data["time_series"].keys())[0]
            num_periods = len(data["time_series"][sample_topic])
            period_score = min(num_periods / 10.0, 0.5)  # Up to 0.5 for periods
        else:
            period_score = 0.0
            
        completeness_score = topic_score + period_score
    
    results["tests"].append(f"SCORE: {completeness_score:.3f}")
    
    # SCORE 2: Analysis quality score
    analysis_score = 0.0
    quality_factors = [
        trends_valid,  # 0.25
        summary_valid,  # 0.25
        freq_reasonable,  # 0.25
        multiple_trends  # 0.25
    ]
    analysis_score = sum(quality_factors) * 0.25
    
    results["tests"].append(f"SCORE: {analysis_score:.3f}")
    
    return results

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Copy the generated script to temp directory
        import shutil
        if os.path.exists("../generated.py"):
            shutil.copy("../generated.py", "generated.py")
        elif os.path.exists("generated.py"):
            pass  # Already in the right place
        else:
            print("FAIL: generated.py not found")
            sys.exit(1)
        
        results = run_test()
        
        for test in results["tests"]:
            print(test)
