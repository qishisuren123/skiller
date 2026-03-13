import subprocess
import json
import tempfile
import os
import numpy as np
from pathlib import Path

def create_data():
    """Generate synthetic mark-recapture data"""
    np.random.seed(42)
    
    # Simulate 8 capture sessions with realistic mark-recapture scenarios
    sessions = []
    true_population = 150  # Hidden true population for validation
    
    for i in range(8):
        # Simulate marking 20-40 animals initially
        marked = np.random.randint(20, 41)
        
        # Second capture gets 25-50 animals
        total_captured = np.random.randint(25, 51)
        
        # Recaptures follow hypergeometric distribution
        # but we'll simulate with realistic recapture rates
        recapture_prob = marked / true_population
        expected_recaptures = total_captured * recapture_prob
        recaptured = max(1, int(np.random.poisson(expected_recaptures)))
        recaptured = min(recaptured, marked, total_captured)
        
        sessions.append({
            "session_id": f"session_{i+1}",
            "marked_count": marked,
            "total_captured": total_captured,
            "recaptured_count": recaptured
        })
    
    # Add some edge cases
    sessions.append({
        "session_id": "session_edge_1",
        "marked_count": 30,
        "total_captured": 25,
        "recaptured_count": 0  # No recaptures
    })
    
    sessions.append({
        "session_id": "session_edge_2", 
        "marked_count": 15,
        "total_captured": 20,
        "recaptured_count": 2  # Small sample
    })
    
    return {"sessions": sessions}

def test_mark_recapture_estimation():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test data
        data = create_data()
        input_file = tmpdir / "input.json"
        output_file = tmpdir / "output.json"
        
        with open(input_file, 'w') as f:
            json.dump(data, f)
        
        # Test basic functionality
        cmd = ["python", "generated.py", "--input", str(input_file), "--output", str(output_file)]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=tmpdir)
        
        print("PASS" if result.returncode == 0 else "FAIL", "- Script runs without errors")
        print("PASS" if output_file.exists() else "FAIL", "- Output file created")
        
        if not output_file.exists():
            return
            
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        # Test output structure
        print("PASS" if "population_estimates" in results else "FAIL", "- Contains population estimates")
        print("PASS" if "summary_statistics" in results else "FAIL", "- Contains summary statistics")
        print("PASS" if "metadata" in results else "FAIL", "- Contains metadata")
        
        estimates = results.get("population_estimates", [])
        print("PASS" if len(estimates) >= 8 else "FAIL", "- Processes multiple sessions")
        
        # Test estimate calculations
        valid_estimates = [e for e in estimates if e.get("population_estimate") is not None]
        print("PASS" if len(valid_estimates) >= 6 else "FAIL", "- Generates valid estimates for most sessions")
        
        # Test confidence intervals
        has_intervals = any("confidence_interval" in e for e in valid_estimates)
        print("PASS" if has_intervals else "FAIL", "- Includes confidence intervals")
        
        # Test edge case handling (zero recaptures)
        zero_recapture_handled = any(e.get("recaptured_count") == 0 and e.get("population_estimate") is None 
                                   for e in estimates)
        print("PASS" if zero_recapture_handled else "FAIL", "- Handles zero recaptures appropriately")
        
        # Test Chapman method
        chapman_file = tmpdir / "chapman_output.json"
        cmd_chapman = ["python", "generated.py", "--input", str(input_file), 
                      "--output", str(chapman_file), "--method", "chapman"]
        result_chapman = subprocess.run(cmd_chapman, capture_output=True, text=True, cwd=tmpdir)
        
        print("PASS" if result_chapman.returncode == 0 else "FAIL", "- Chapman method works")
        
        # Test confidence level parameter
        conf_file = tmpdir / "conf_output.json"
        cmd_conf = ["python", "generated.py", "--input", str(input_file), 
                   "--output", str(conf_file), "--confidence", "0.90"]
        result_conf = subprocess.run(cmd_conf, capture_output=True, text=True, cwd=tmpdir)
        
        print("PASS" if result_conf.returncode == 0 else "FAIL", "- Custom confidence level works")
        
        # Test summary statistics
        summary = results.get("summary_statistics", {})
        print("PASS" if "mean_population_estimate" in summary else "FAIL", "- Includes mean population estimate")
        print("PASS" if "coefficient_of_variation" in summary else "FAIL", "- Includes coefficient of variation")
        print("PASS" if "valid_sessions" in summary else "FAIL", "- Reports valid sessions count")
        
        # Calculate accuracy score
        if valid_estimates:
            true_pop = 150
            estimates_values = [e["population_estimate"] for e in valid_estimates]
            mean_estimate = np.mean(estimates_values)
            accuracy = max(0, 1 - abs(mean_estimate - true_pop) / true_pop)
        else:
            accuracy = 0
        
        print(f"SCORE: {accuracy:.3f} - Population estimation accuracy")
        
        # Calculate completeness score
        total_sessions = len(data["sessions"])
        processable_sessions = len([s for s in data["sessions"] if s["recaptured_count"] > 0])
        if processable_sessions > 0:
            completeness = len(valid_estimates) / processable_sessions
        else:
            completeness = 0
        
        print(f"SCORE: {completeness:.3f} - Data processing completeness")

if __name__ == "__main__":
    test_mark_recapture_estimation()
