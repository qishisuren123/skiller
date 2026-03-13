import subprocess
import tempfile
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def create_data():
    """Create synthetic environmental data for testing"""
    # This function creates the expected synthetic data structure
    # The actual data generation should be done by the generated script
    np.random.seed(42)
    
    # Create realistic environmental gradients
    x, y = np.meshgrid(np.linspace(0, 1, 50), np.linspace(0, 1, 50))
    
    # Temperature: varies with latitude (y-axis) + noise
    temperature = 10 + 20 * (1 - y) + 5 * np.random.random((50, 50))
    
    # Precipitation: varies with longitude + elevation effects
    precipitation = 300 + 800 * x + 200 * np.random.random((50, 50))
    
    # Elevation: mountain ridge pattern
    elevation = 1000 * np.exp(-((x-0.5)**2 + (y-0.3)**2) / 0.1) + 100 * np.random.random((50, 50))
    
    # Vegetation: related to precipitation and temperature
    vegetation = np.clip((precipitation / 1000) * (1 - np.abs(temperature - 20) / 30), 0, 1)
    
    return {
        'temperature': temperature,
        'precipitation': precipitation, 
        'elevation': elevation,
        'vegetation': vegetation
    }

def test_habitat_suitability():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Test basic functionality
        result = subprocess.run([
            'python', 'generated.py',
            '--output', 'results',
            '--species', 'test_species',
            '--weights', '0.3,0.3,0.2,0.2',
            '--temp_range', '18,22',
            '--precip_min', '400'
        ], capture_output=True, text=True)
        
        print("PASS" if result.returncode == 0 else "FAIL", "- Script runs without errors")
        
        # Check if output directory exists
        results_dir = Path('results')
        print("PASS" if results_dir.exists() else "FAIL", "- Output directory created")
        
        # Check required output files
        hsi_file = results_dir / 'test_species_hsi.csv'
        summary_file = results_dir / 'test_species_summary.json'
        map_file = results_dir / 'test_species_hsi_map.png'
        
        print("PASS" if hsi_file.exists() else "FAIL", "- HSI CSV file created")
        print("PASS" if summary_file.exists() else "FAIL", "- Summary JSON file created")
        print("PASS" if map_file.exists() else "FAIL", "- HSI map PNG file created")
        
        if hsi_file.exists():
            # Test HSI data structure
            hsi_data = pd.read_csv(hsi_file, header=None)
            print("PASS" if hsi_data.shape == (50, 50) else "FAIL", "- HSI grid has correct dimensions (50x50)")
            
            # Test HSI value range
            hsi_values = hsi_data.values
            valid_range = np.all((hsi_values >= 0) & (hsi_values <= 1))
            print("PASS" if valid_range else "FAIL", "- HSI values in valid range [0,1]")
            
            # Test for spatial variation
            hsi_std = np.std(hsi_values)
            print("PASS" if hsi_std > 0.01 else "FAIL", "- HSI shows spatial variation")
        else:
            print("FAIL - Cannot test HSI data structure")
            print("FAIL - Cannot test HSI value range") 
            print("FAIL - Cannot test spatial variation")
            hsi_values = None
        
        if summary_file.exists():
            # Test summary statistics
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            required_keys = ['mean_hsi', 'high_suitability_percent', 'optimal_locations']
            has_required_keys = all(key in summary for key in required_keys)
            print("PASS" if has_required_keys else "FAIL", "- Summary contains required statistics")
            
            if 'mean_hsi' in summary:
                mean_valid = 0 <= summary['mean_hsi'] <= 1
                print("PASS" if mean_valid else "FAIL", "- Mean HSI in valid range")
            else:
                print("FAIL - Mean HSI not found")
            
            if 'high_suitability_percent' in summary:
                percent_valid = 0 <= summary['high_suitability_percent'] <= 100
                print("PASS" if percent_valid else "FAIL", "- High suitability percentage valid")
            else:
                print("FAIL - High suitability percentage not found")
            
            if 'optimal_locations' in summary:
                locations_valid = len(summary['optimal_locations']) == 5
                print("PASS" if locations_valid else "FAIL", "- Optimal locations list has 5 entries")
            else:
                print("FAIL - Optimal locations not found")
        else:
            print("FAIL - Cannot test summary statistics")
            print("FAIL - Cannot test mean HSI range")
            print("FAIL - Cannot test high suitability percentage")
            print("FAIL - Cannot test optimal locations count")
        
        # Test weight validation
        result_bad_weights = subprocess.run([
            'python', 'generated.py',
            '--output', 'results2',
            '--species', 'test2',
            '--weights', '0.3,0.3,0.3,0.3'  # Sum > 1.0
        ], capture_output=True, text=True)
        
        print("PASS" if result_bad_weights.returncode != 0 else "FAIL", "- Validates weight sum")
        
        # Calculate scores
        if hsi_values is not None and summary_file.exists():
            # Score 1: HSI spatial coherence (neighboring cells should be similar)
            gradients = np.gradient(hsi_values)
            mean_gradient = np.mean(np.sqrt(gradients[0]**2 + gradients[1]**2))
            coherence_score = max(0, 1 - mean_gradient * 5)  # Penalize high gradients
            print(f"SCORE: {coherence_score:.3f} - HSI spatial coherence")
            
            # Score 2: Summary accuracy
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            actual_mean = np.mean(hsi_values)
            actual_high_percent = np.sum(hsi_values > 0.7) / hsi_values.size * 100
            
            mean_error = abs(summary.get('mean_hsi', 0) - actual_mean)
            percent_error = abs(summary.get('high_suitability_percent', 0) - actual_high_percent)
            
            accuracy_score = max(0, 1 - mean_error - percent_error/100)
            print(f"SCORE: {accuracy_score:.3f} - Summary statistics accuracy")
        else:
            print("SCORE: 0.000 - HSI spatial coherence")
            print("SCORE: 0.000 - Summary statistics accuracy")

if __name__ == "__main__":
    test_habitat_suitability()
