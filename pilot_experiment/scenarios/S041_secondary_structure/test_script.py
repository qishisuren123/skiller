import os
import sys
import tempfile
import subprocess
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def create_data():
    """Generate synthetic protein dihedral angle data"""
    np.random.seed(42)
    
    # Create a protein with 150 residues
    n_residues = 150
    residue_ids = [f"A{i+1}" for i in range(n_residues)]
    
    phi_angles = []
    psi_angles = []
    true_ss = []
    
    # Generate structured regions
    i = 0
    while i < n_residues:
        if i < 40:  # Alpha helix region
            phi = np.random.normal(-60, 15)
            psi = np.random.normal(-45, 15)
            ss = 'H'
        elif i < 50:  # Coil region
            phi = np.random.uniform(-180, 180)
            psi = np.random.uniform(-180, 180)
            ss = 'C'
        elif i < 90:  # Beta sheet region
            phi = np.random.normal(-120, 20)
            psi = np.random.normal(120, 20)
            ss = 'E'
        elif i < 110:  # Another coil region
            phi = np.random.uniform(-180, 180)
            psi = np.random.uniform(-180, 180)
            ss = 'C'
        else:  # Mixed region
            if np.random.random() < 0.4:
                phi = np.random.normal(-60, 15)
                psi = np.random.normal(-45, 15)
                ss = 'H'
            elif np.random.random() < 0.7:
                phi = np.random.normal(-120, 20)
                psi = np.random.normal(120, 20)
                ss = 'E'
            else:
                phi = np.random.uniform(-180, 180)
                psi = np.random.uniform(-180, 180)
                ss = 'C'
        
        # Ensure angles are in valid range
        phi = np.clip(phi, -180, 180)
        psi = np.clip(psi, -180, 180)
        
        phi_angles.append(phi)
        psi_angles.append(psi)
        true_ss.append(ss)
        i += 1
    
    # Add some NaN values
    nan_indices = np.random.choice(n_residues, size=5, replace=False)
    for idx in nan_indices:
        phi_angles[idx] = np.nan
        psi_angles[idx] = np.nan
    
    df = pd.DataFrame({
        'residue_id': residue_ids,
        'phi': phi_angles,
        'psi': psi_angles
    })
    
    return df, true_ss

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create test data
        test_df, true_ss = create_data()
        input_file = "test_angles.csv"
        test_df.to_csv(input_file, index=False)
        
        # Define output files
        output_json = "results.json"
        output_csv = "assignments.csv"
        plot_file = "ramachandran.png"
        
        # Try different argument name variations
        cmd_variations = [
            ["python", "generated.py", input_file, output_json, output_csv, plot_file],
            ["python", "generated.py", "--input", input_file, "--json", output_json, "--csv", output_csv, "--plot", plot_file],
            ["python", "generated.py", "-i", input_file, "-j", output_json, "-c", output_csv, "-p", plot_file],
            ["python", "generated.py", "--input_file", input_file, "--output_json", output_json, "--output_csv", output_csv, "--plot_path", plot_file]
        ]
        
        success = False
        for cmd in cmd_variations:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        print(f"PASS: Script execution successful: {success}")
        if not success:
            return
        
        # Test file outputs
        json_exists = os.path.exists(output_json)
        csv_exists = os.path.exists(output_csv)
        plot_exists = os.path.exists(plot_file)
        
        print(f"PASS: JSON output file created: {json_exists}")
        print(f"PASS: CSV output file created: {csv_exists}")
        print(f"PASS: Plot file created: {plot_exists}")
        
        if not (json_exists and csv_exists):
            return
        
        # Load and validate JSON output
        try:
            with open(output_json, 'r') as f:
                results = json.load(f)
            json_valid = True
        except:
            json_valid = False
        
        print(f"PASS: JSON file is valid: {json_valid}")
        
        if not json_valid:
            return
        
        # Check JSON structure
        has_assignments = 'assignments' in results or 'ss_assignments' in results
        has_statistics = 'statistics' in results or 'stats' in results
        
        print(f"PASS: JSON contains assignments: {has_assignments}")
        print(f"PASS: JSON contains statistics: {has_statistics}")
        
        # Load and validate CSV output
        try:
            output_df = pd.read_csv(output_csv)
            csv_valid = True
        except:
            csv_valid = False
        
        print(f"PASS: CSV file is valid: {csv_valid}")
        
        if not csv_valid:
            return
        
        # Check CSV structure
        required_cols = ['residue_id', 'phi', 'psi']
        ss_col = None
        for col in ['ss_assignment', 'secondary_structure', 'ss', 'assignment']:
            if col in output_df.columns:
                ss_col = col
                break
        
        has_required_cols = all(col in output_df.columns for col in required_cols)
        has_ss_col = ss_col is not None
        
        print(f"PASS: CSV has required columns: {has_required_cols}")
        print(f"PASS: CSV has secondary structure assignments: {has_ss_col}")
        
        if not (has_required_cols and has_ss_col):
            return
        
        # Check assignment validity
        valid_ss = set(['H', 'E', 'C'])
        assignments = output_df[ss_col].values
        all_valid_ss = all(ss in valid_ss for ss in assignments)
        
        print(f"PASS: All assignments are valid (H/E/C): {all_valid_ss}")
        
        # Check NaN handling
        nan_mask = test_df['phi'].isna() | test_df['psi'].isna()
        nan_assignments = output_df.loc[nan_mask, ss_col].values
        nan_handled = all(ss == 'C' for ss in nan_assignments)
        
        print(f"PASS: NaN values assigned as coil (C): {nan_handled}")
        
        # Check correct number of residues
        correct_length = len(output_df) == len(test_df)
        print(f"PASS: Correct number of residues processed: {correct_length}")
        
        # Calculate accuracy score based on Ramachandran rules
        correct_assignments = 0
        total_valid = 0
        
        for i, row in output_df.iterrows():
            if pd.isna(row['phi']) or pd.isna(row['psi']):
                if row[ss_col] == 'C':
                    correct_assignments += 1
                total_valid += 1
            else:
                phi, psi = row['phi'], row['psi']
                predicted = row[ss_col]
                
                # Apply Ramachandran rules
                if -180 <= phi <= 0 and -90 <= psi <= 50:
                    expected = 'H'
                elif -180 <= phi <= -50 and 50 <= psi <= 180:
                    expected = 'E'
                else:
                    expected = 'C'
                
                if predicted == expected:
                    correct_assignments += 1
                total_valid += 1
        
        accuracy = correct_assignments / total_valid if total_valid > 0 else 0
        print(f"SCORE: Classification accuracy: {accuracy:.3f}")
        
        # Calculate statistics completeness score
        stats_score = 0
        if has_statistics:
            stats_key = 'statistics' if 'statistics' in results else 'stats'
            stats = results[stats_key]
            
            # Check for percentage statistics
            pct_keys = ['percentage', 'percent', 'pct', 'fraction']
            has_percentages = any(any(key in str(k).lower() for key in pct_keys) for k in stats.keys())
            if has_percentages:
                stats_score += 0.5
            
            # Check for segment length statistics
            len_keys = ['length', 'segment', 'average']
            has_lengths = any(any(key in str(k).lower() for key in len_keys) for k in stats.keys())
            if has_lengths:
                stats_score += 0.5
        
        print(f"SCORE: Statistics completeness: {stats_score:.3f}")

if __name__ == "__main__":
    run_test()
