import subprocess
import tempfile
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys

def create_data():
    """Create synthetic drug interaction database for testing"""
    # Common drugs and their interactions
    drug_interactions = {
        ('warfarin', 'aspirin'): 'severe',
        ('warfarin', 'ibuprofen'): 'severe', 
        ('lisinopril', 'potassium'): 'moderate',
        ('metformin', 'alcohol'): 'moderate',
        ('simvastatin', 'grapefruit'): 'minor',
        ('digoxin', 'furosemide'): 'moderate',
        ('warfarin', 'simvastatin'): 'minor',
        ('aspirin', 'ibuprofen'): 'moderate',
        ('lisinopril', 'ibuprofen'): 'moderate',
        ('metformin', 'furosemide'): 'minor'
    }
    
    # Add reverse pairs
    interactions_db = {}
    for (drug1, drug2), severity in drug_interactions.items():
        interactions_db[(drug1, drug2)] = severity
        interactions_db[(drug2, drug1)] = severity
    
    return interactions_db

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Test parameters
        num_patients = 50
        num_prescriptions = 200
        json_file = "interactions.json"
        csv_file = "interactions.csv" 
        plot_file = "risk_distribution.png"
        
        # Run the script with various argument name possibilities
        cmd_variants = [
            ["python", "generated.py", "--num_patients", str(num_patients), 
             "--num_prescriptions", str(num_prescriptions), "--output_json", json_file,
             "--output_csv", csv_file, "--plot_file", plot_file],
            ["python", "generated.py", "--num-patients", str(num_patients),
             "--num-prescriptions", str(num_prescriptions), "--output-json", json_file, 
             "--output-csv", csv_file, "--plot-file", plot_file],
            ["python", "generated.py", "-n", str(num_patients), "-p", str(num_prescriptions),
             "-j", json_file, "-c", csv_file, "--plot", plot_file]
        ]
        
        success = False
        for cmd in cmd_variants:
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
        files_exist = 0
        if os.path.exists(json_file):
            print("PASS: JSON output file created")
            files_exist += 1
        else:
            print("FAIL: JSON output file not created")
            
        if os.path.exists(csv_file):
            print("PASS: CSV output file created") 
            files_exist += 1
        else:
            print("FAIL: CSV output file not created")
            
        if os.path.exists(plot_file):
            print("PASS: Plot file created")
            files_exist += 1
        else:
            print("FAIL: Plot file not created")
        
        if files_exist < 3:
            return
            
        # Test JSON structure and content
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            print("PASS: JSON file is valid")
            
            if 'patient_interactions' in data and 'summary_statistics' in data:
                print("PASS: JSON contains required sections")
            else:
                print("FAIL: JSON missing required sections")
                
            # Check summary statistics
            summary = data.get('summary_statistics', {})
            if 'total_interactions' in summary:
                print("PASS: Summary contains total interactions")
            else:
                print("FAIL: Summary missing total interactions")
                
            if 'interactions_by_severity' in summary:
                severity_counts = summary['interactions_by_severity']
                if isinstance(severity_counts, dict):
                    print("PASS: Severity breakdown provided")
                else:
                    print("FAIL: Invalid severity breakdown format")
            else:
                print("FAIL: Missing interactions by severity")
                
        except Exception as e:
            print("FAIL: Error reading JSON file")
            return
            
        # Test CSV structure
        try:
            df = pd.read_csv(csv_file)
            print("PASS: CSV file is valid")
            
            required_cols = ['patient_id', 'drug1', 'drug2', 'severity']
            if all(col in df.columns for col in required_cols):
                print("PASS: CSV contains required columns")
            else:
                print("FAIL: CSV missing required columns")
                
            if len(df) > 0:
                print("PASS: CSV contains interaction data")
                
                # Check severity levels
                severities = df['severity'].unique()
                valid_severities = set(['minor', 'moderate', 'severe'])
                if any(sev in valid_severities for sev in severities):
                    print("PASS: Valid severity levels found")
                else:
                    print("FAIL: Invalid severity levels")
            else:
                print("FAIL: CSV is empty")
                
        except Exception as e:
            print("FAIL: Error reading CSV file")
            
        # Test plot file
        try:
            import matplotlib.image as mpimg
            img = mpimg.imread(plot_file)
            if img.shape[0] > 0 and img.shape[1] > 0:
                print("PASS: Plot file is valid image")
            else:
                print("FAIL: Invalid plot file")
        except:
            print("FAIL: Cannot read plot file")
            
        # Calculate scores
        try:
            # Score 1: Data completeness (0-1)
            total_patients = len(data.get('patient_interactions', {}))
            total_interactions = summary.get('total_interactions', 0)
            completeness_score = min(1.0, (total_patients * total_interactions) / (num_patients * 10))
            print(f"SCORE: Data completeness: {completeness_score:.3f}")
            
            # Score 2: Analysis quality (0-1) 
            quality_factors = 0
            max_factors = 4
            
            if total_interactions > 0:
                quality_factors += 1
            if 'interactions_by_severity' in summary and len(summary['interactions_by_severity']) > 0:
                quality_factors += 1
            if len(df) > 0:
                quality_factors += 1
            if os.path.exists(plot_file):
                quality_factors += 1
                
            quality_score = quality_factors / max_factors
            print(f"SCORE: Analysis quality: {quality_score:.3f}")
            
        except Exception as e:
            print("SCORE: Data completeness: 0.000")
            print("SCORE: Analysis quality: 0.000")

if __name__ == "__main__":
    run_test()
