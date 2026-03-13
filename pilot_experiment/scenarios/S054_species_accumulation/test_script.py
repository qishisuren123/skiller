import subprocess
import tempfile
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def create_data():
    """Generate synthetic species occurrence data for testing"""
    np.random.seed(42)
    n_sites = 30
    n_species = 60
    
    # Create site-by-species matrix with realistic patterns
    occurrence_matrix = np.zeros((n_sites, n_species))
    
    # Some species are common (high occurrence probability)
    common_species = np.random.choice(n_species, size=int(0.2 * n_species), replace=False)
    # Some species are rare (low occurrence probability)
    rare_species = np.random.choice([i for i in range(n_species) if i not in common_species], 
                                  size=int(0.3 * n_species), replace=False)
    
    for site in range(n_sites):
        # Common species: 60-80% occurrence probability
        for sp in common_species:
            if np.random.random() < np.random.uniform(0.6, 0.8):
                occurrence_matrix[site, sp] = 1
        
        # Rare species: 5-20% occurrence probability  
        for sp in rare_species:
            if np.random.random() < np.random.uniform(0.05, 0.2):
                occurrence_matrix[site, sp] = 1
                
        # Intermediate species: 20-50% occurrence probability
        for sp in range(n_species):
            if sp not in common_species and sp not in rare_species:
                if np.random.random() < np.random.uniform(0.2, 0.5):
                    occurrence_matrix[site, sp] = 1
    
    return occurrence_matrix, n_sites, n_species

def test_species_accumulation():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Test data
        occurrence_matrix, n_sites, n_species = create_data()
        
        # Test basic functionality
        cmd = ["python", "generated.py", "--sites", "30", "--species", "60", 
               "--randomizations", "50", "--output", "results"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"FAIL: Script execution failed: {result.stderr}")
                return
        except subprocess.TimeoutExpired:
            print("FAIL: Script execution timed out")
            return
        except FileNotFoundError:
            print("FAIL: generated.py not found")
            return

        # Check output files exist
        results_dir = Path("results")
        if not results_dir.exists():
            print("FAIL: Output directory not created")
            return
        print("PASS: Output directory created")

        # Check JSON results file
        json_files = list(results_dir.glob("*.json"))
        if not json_files:
            print("FAIL: No JSON results file found")
            return
        print("PASS: JSON results file created")
        
        # Load and validate JSON content
        try:
            with open(json_files[0], 'r') as f:
                results = json.load(f)
        except:
            print("FAIL: Could not parse JSON results file")
            return
        print("PASS: JSON file is valid")

        # Check required fields in JSON
        required_fields = ['total_species', 'mean_species_per_site', 'accumulation_curve', 'rarefaction_curve']
        missing_fields = [field for field in required_fields if field not in results]
        if missing_fields:
            print(f"FAIL: Missing required fields in JSON: {missing_fields}")
            return
        print("PASS: All required fields present in JSON")

        # Check CSV file
        csv_files = list(results_dir.glob("*.csv"))
        if not csv_files:
            print("FAIL: No CSV file found")
            return
        print("PASS: CSV file created")

        # Validate CSV content
        try:
            df = pd.read_csv(csv_files[0])
            if df.shape[0] != 30:  # Should match number of sites
                print(f"FAIL: CSV has wrong number of rows: {df.shape[0]} (expected 30)")
                return
            if df.shape[1] < 10:  # Should have reasonable number of species columns
                print(f"FAIL: CSV has too few columns: {df.shape[1]}")
                return
        except:
            print("FAIL: Could not read CSV file")
            return
        print("PASS: CSV file format is valid")

        # Check PNG plot
        png_files = list(results_dir.glob("*.png"))
        if not png_files:
            print("FAIL: No PNG plot file found")
            return
        print("PASS: PNG plot file created")

        # Validate accumulation curve data
        acc_curve = results.get('accumulation_curve', {})
        if 'mean' not in acc_curve or 'confidence_interval' not in acc_curve:
            print("FAIL: Accumulation curve missing mean or confidence intervals")
            return
        print("PASS: Accumulation curve has required statistics")

        # Check accumulation curve properties
        mean_curve = acc_curve['mean']
        if not isinstance(mean_curve, list) or len(mean_curve) == 0:
            print("FAIL: Accumulation curve mean is not a valid list")
            return
        
        # Should be monotonically increasing
        if not all(mean_curve[i] <= mean_curve[i+1] for i in range(len(mean_curve)-1)):
            print("FAIL: Accumulation curve is not monotonically increasing")
            return
        print("PASS: Accumulation curve is monotonically increasing")

        # Check rarefaction curve
        rare_curve = results.get('rarefaction_curve', {})
        if 'expected_richness' not in rare_curve:
            print("FAIL: Rarefaction curve missing expected richness")
            return
        print("PASS: Rarefaction curve data present")

        # Validate summary statistics
        total_species = results.get('total_species', 0)
        if not isinstance(total_species, (int, float)) or total_species <= 0:
            print("FAIL: Invalid total species count")
            return
        print("PASS: Valid total species count")

        mean_per_site = results.get('mean_species_per_site', 0)
        if not isinstance(mean_per_site, (int, float)) or mean_per_site <= 0:
            print("FAIL: Invalid mean species per site")
            return
        print("PASS: Valid mean species per site")

        # Check if Chao2 estimate is present
        if 'chao2_estimate' in results:
            chao2 = results['chao2_estimate']
            if isinstance(chao2, (int, float)) and chao2 >= total_species:
                print("PASS: Chao2 estimate is reasonable")
            else:
                print("FAIL: Chao2 estimate is unrealistic")
                return
        else:
            print("PASS: Chao2 estimate not required but recommended")

        # Test different parameter values
        cmd2 = ["python", "generated.py", "--sites", "20", "--species", "40", 
                "--randomizations", "25", "--output", "test2"]
        
        try:
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
            if result2.returncode == 0 and Path("test2").exists():
                print("PASS: Script works with different parameters")
            else:
                print("FAIL: Script failed with different parameters")
                return
        except:
            print("FAIL: Script failed with different parameters")
            return

        # SCORE metrics
        # Score 1: Data completeness and format correctness
        score1_components = [
            results_dir.exists(),
            len(json_files) > 0,
            len(csv_files) > 0, 
            len(png_files) > 0,
            all(field in results for field in required_fields),
            isinstance(total_species, (int, float)) and total_species > 0,
            isinstance(mean_per_site, (int, float)) and mean_per_site > 0
        ]
        score1 = sum(score1_components) / len(score1_components)
        print(f"SCORE: Data completeness: {score1:.3f}")

        # Score 2: Scientific accuracy of accumulation curve
        score2_components = []
        
        # Check if curve starts at reasonable value
        if len(mean_curve) > 0 and mean_curve[0] > 0:
            score2_components.append(True)
        else:
            score2_components.append(False)
            
        # Check if curve ends at reasonable total
        if len(mean_curve) > 0 and mean_curve[-1] <= total_species:
            score2_components.append(True)
        else:
            score2_components.append(False)
            
        # Check monotonic increase
        score2_components.append(all(mean_curve[i] <= mean_curve[i+1] for i in range(len(mean_curve)-1)))
        
        # Check confidence intervals exist and are reasonable
        ci = acc_curve.get('confidence_interval', {})
        if 'lower' in ci and 'upper' in ci:
            lower = ci['lower']
            upper = ci['upper']
            if (isinstance(lower, list) and isinstance(upper, list) and 
                len(lower) == len(mean_curve) and len(upper) == len(mean_curve)):
                # Check that CI bounds are reasonable
                ci_reasonable = all(lower[i] <= mean_curve[i] <= upper[i] 
                                  for i in range(len(mean_curve)))
                score2_components.append(ci_reasonable)
            else:
                score2_components.append(False)
        else:
            score2_components.append(False)
            
        score2 = sum(score2_components) / len(score2_components)
        print(f"SCORE: Scientific accuracy: {score2:.3f}")

if __name__ == "__main__":
    test_species_accumulation()
