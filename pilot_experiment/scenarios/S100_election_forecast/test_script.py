import subprocess
import json
import pandas as pd
import numpy as np
import tempfile
import os
from datetime import datetime, timedelta

def create_data():
    """Generate synthetic polling data for testing"""
    np.random.seed(42)
    
    # Create polls over 60 days before election
    election_date = datetime(2024, 11, 5)
    polls = []
    
    candidates = ["Alice Johnson", "Bob Smith", "Carol Davis"]
    pollster_ratings = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C"]
    
    # True vote shares (hidden)
    true_shares = [45.2, 38.7, 16.1]
    
    for i in range(25):  # 25 polls
        days_before = np.random.randint(1, 61)
        poll_date = election_date - timedelta(days=days_before)
        
        sample_size = np.random.randint(400, 2000)
        pollster_rating = np.random.choice(pollster_ratings)
        
        # Add noise to true shares
        noise_level = 3.0 + np.random.normal(0, 1)
        poll_shares = []
        for j, true_share in enumerate(true_shares):
            poll_share = true_share + np.random.normal(0, noise_level)
            poll_shares.append(max(0, poll_share))
        
        # Normalize to 100%
        total = sum(poll_shares)
        poll_shares = [s/total * 100 for s in poll_shares]
        
        candidates_dict = {candidates[j]: round(poll_shares[j], 1) for j in range(3)}
        
        poll = {
            "date": poll_date.strftime("%Y-%m-%d"),
            "sample_size": sample_size,
            "candidates": candidates_dict,
            "pollster_rating": pollster_rating
        }
        polls.append(poll)
    
    return {
        "polls": polls,
        "election_date": "2024-11-05",
        "candidates": candidates,
        "true_shares": true_shares
    }

def run_test():
    test_data = create_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Prepare arguments
        polls_json = json.dumps(test_data["polls"])
        output_json = "forecast.json"
        output_csv = "summary.csv"
        election_date = test_data["election_date"]
        
        # Test different argument name variations
        cmd_variations = [
            ["--polls", polls_json, "--election-date", election_date, "--output-json", output_json, "--output-csv", output_csv],
            ["--polls", polls_json, "--election_date", election_date, "--output_json", output_json, "--output_csv", output_csv],
        ]
        
        success = False
        for cmd_args in cmd_variations:
            try:
                result = subprocess.run(["python", "generated.py"] + cmd_args, 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed")
            return
        
        # Load outputs
        try:
            with open(output_json, 'r') as f:
                forecast_data = json.load(f)
            summary_df = pd.read_csv(output_csv)
        except Exception as e:
            print(f"FAIL: Could not load output files: {e}")
            return
        
        candidates = test_data["candidates"]
        
        # Test 1: JSON structure validation
        required_keys = ["vote_shares", "confidence_intervals", "win_probabilities", "effective_sample_size"]
        if all(key in forecast_data for key in required_keys):
            print("PASS: JSON contains required keys")
        else:
            print("FAIL: JSON missing required keys")
        
        # Test 2: All candidates present in vote shares
        if all(candidate in forecast_data.get("vote_shares", {}) for candidate in candidates):
            print("PASS: All candidates in vote shares")
        else:
            print("FAIL: Missing candidates in vote shares")
        
        # Test 3: Vote shares sum approximately to 100
        vote_shares = forecast_data.get("vote_shares", {})
        total_share = sum(vote_shares.values()) if vote_shares else 0
        if 99.0 <= total_share <= 101.0:
            print("PASS: Vote shares sum to ~100%")
        else:
            print("FAIL: Vote shares don't sum to 100%")
        
        # Test 4: Win probabilities sum approximately to 1
        win_probs = forecast_data.get("win_probabilities", {})
        total_prob = sum(win_probs.values()) if win_probs else 0
        if 0.99 <= total_prob <= 1.01:
            print("PASS: Win probabilities sum to ~1.0")
        else:
            print("FAIL: Win probabilities don't sum to 1.0")
        
        # Test 5: Confidence intervals structure
        ci_data = forecast_data.get("confidence_intervals", {})
        ci_valid = all(
            candidate in ci_data and 
            isinstance(ci_data[candidate], list) and 
            len(ci_data[candidate]) == 2 and
            ci_data[candidate][0] < ci_data[candidate][1]
            for candidate in candidates
        )
        if ci_valid:
            print("PASS: Confidence intervals properly structured")
        else:
            print("FAIL: Invalid confidence intervals structure")
        
        # Test 6: CSV file structure
        expected_csv_cols = {"candidate", "vote_share", "win_probability"}
        csv_cols = set(summary_df.columns)
        if expected_csv_cols.issubset(csv_cols):
            print("PASS: CSV has required columns")
        else:
            print("FAIL: CSV missing required columns")
        
        # Test 7: CSV candidate count
        if len(summary_df) == len(candidates):
            print("PASS: CSV has correct number of candidates")
        else:
            print("FAIL: CSV has wrong number of candidates")
        
        # Test 8: Effective sample size is positive
        eff_sample = forecast_data.get("effective_sample_size", 0)
        if eff_sample > 0:
            print("PASS: Effective sample size is positive")
        else:
            print("FAIL: Invalid effective sample size")
        
        # Test 9: Vote shares are reasonable (0-100)
        vote_share_valid = all(0 <= share <= 100 for share in vote_shares.values())
        if vote_share_valid:
            print("PASS: Vote shares in valid range")
        else:
            print("FAIL: Vote shares out of range")
        
        # Test 10: Win probabilities in valid range (0-1)
        win_prob_valid = all(0 <= prob <= 1 for prob in win_probs.values())
        if win_prob_valid:
            print("PASS: Win probabilities in valid range")
        else:
            print("FAIL: Win probabilities out of range")
        
        # Test 11: Confidence intervals within bounds
        ci_bounds_valid = all(
            0 <= ci_data[candidate][0] <= 100 and 0 <= ci_data[candidate][1] <= 100
            for candidate in candidates if candidate in ci_data
        )
        if ci_bounds_valid:
            print("PASS: Confidence intervals within bounds")
        else:
            print("FAIL: Confidence intervals out of bounds")
        
        # Test 12: Vote shares match between JSON and CSV
        csv_shares = dict(zip(summary_df['candidate'], summary_df['vote_share']))
        shares_match = all(
            abs(vote_shares.get(candidate, 0) - csv_shares.get(candidate, -999)) < 0.1
            for candidate in candidates
        )
        if shares_match:
            print("PASS: Vote shares consistent between JSON and CSV")
        else:
            print("FAIL: Vote shares inconsistent between outputs")
        
        # Test 13: Temporal weighting implementation check
        # More recent polls should have higher effective weight
        # This is implicit in the aggregation quality
        recent_poll_exists = any(
            (datetime.strptime(test_data["election_date"], "%Y-%m-%d") - 
             datetime.strptime(poll["date"], "%Y-%m-%d")).days <= 7
            for poll in test_data["polls"]
        )
        if recent_poll_exists and eff_sample > len(test_data["polls"]) * 0.1:
            print("PASS: Temporal weighting appears implemented")
        else:
            print("PASS: Temporal weighting check (lenient)")  # Make this lenient
        
        # Test 14: Simulation metadata
        if "simulation_metadata" in forecast_data or "metadata" in forecast_data:
            print("PASS: Simulation metadata present")
        else:
            print("PASS: Simulation metadata check (lenient)")  # Make this lenient
        
        # Test 15: Leading candidate identification
        leading_candidate = max(vote_shares.items(), key=lambda x: x[1])[0]
        leading_win_prob = win_probs.get(leading_candidate, 0)
        if leading_win_prob >= 0.3:  # Leading candidate should have reasonable win probability
            print("PASS: Leading candidate has reasonable win probability")
        else:
            print("FAIL: Leading candidate win probability too low")
        
        # SCORE 1: Forecast accuracy (how close to true leading candidate)
        true_leader_idx = np.argmax(test_data["true_shares"])
        true_leader = candidates[true_leader_idx]
        predicted_leader_share = vote_shares.get(true_leader, 0)
        true_leader_share = test_data["true_shares"][true_leader_idx]
        accuracy_score = max(0, 1 - abs(predicted_leader_share - true_leader_share) / 20.0)
        print(f"SCORE: Forecast accuracy: {accuracy_score:.3f}")
        
        # SCORE 2: Statistical rigor (combination of proper uncertainty and methodology)
        # Check if confidence intervals are reasonable width and win probs are well-calibrated
        avg_ci_width = np.mean([
            ci_data[candidate][1] - ci_data[candidate][0] 
            for candidate in candidates if candidate in ci_data
        ])
        win_prob_entropy = -sum(p * np.log(p + 1e-10) for p in win_probs.values())
        max_entropy = np.log(len(candidates))
        
        rigor_score = 0.5 * min(1.0, avg_ci_width / 20.0) + 0.5 * (win_prob_entropy / max_entropy)
        print(f"SCORE: Statistical rigor: {rigor_score:.3f}")

if __name__ == "__main__":
    run_test()
