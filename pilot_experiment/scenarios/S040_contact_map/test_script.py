import subprocess
import json
import tempfile
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

def create_data():
    """Generate synthetic protein atomic coordinates"""
    # Create a small protein with 20 residues
    atoms = []
    residue_id = 1
    
    # Generate coordinates for a simple helical structure
    for i in range(20):  # 20 residues
        # C-alpha atom (backbone)
        ca_x = 2.0 * np.cos(i * 0.3) + np.random.normal(0, 0.1)
        ca_y = 2.0 * np.sin(i * 0.3) + np.random.normal(0, 0.1)
        ca_z = i * 1.5 + np.random.normal(0, 0.1)
        
        atoms.append({
            "residue_id": residue_id,
            "atom_name": "CA",
            "x": ca_x,
            "y": ca_y,
            "z": ca_z
        })
        
        # C-beta atom (side chain, except for glycine)
        if i != 5:  # Make residue 6 glycine (no CB)
            cb_x = ca_x + np.random.normal(0, 0.5)
            cb_y = ca_y + np.random.normal(0, 0.5)
            cb_z = ca_z + np.random.normal(0, 0.5)
            
            atoms.append({
                "residue_id": residue_id,
                "atom_name": "CB",
                "x": cb_x,
                "y": cb_y,
                "z": cb_z
            })
        
        # Add some other atoms
        atoms.append({
            "residue_id": residue_id,
            "atom_name": "N",
            "x": ca_x + np.random.normal(0, 0.3),
            "y": ca_y + np.random.normal(0, 0.3),
            "z": ca_z + np.random.normal(0, 0.3)
        })
        
        residue_id += 1
    
    return atoms

def run_test():
    test_data = create_data()
    coords_json = json.dumps(test_data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        output_file = "contact_map.csv"
        json_file = "contact_map.json"
        
        # Test basic functionality
        cmd = [
            sys.executable, "generated.py",
            "--coords", coords_json,
            "--output", output_file,
            "--threshold", "8.0",
            "--method", "ca_only",
            "--min_separation", "4"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"FAIL: Script execution failed: {result.stderr}")
                return
        except Exception as e:
            print(f"FAIL: Script execution error: {e}")
            return
        
        # Test 1: Output file exists
        if not os.path.exists(output_file):
            print("FAIL: Contact map CSV file not created")
            return
        print("PASS: Contact map CSV file created")
        
        # Test 2: JSON stats file exists
        if not os.path.exists(json_file):
            print("FAIL: JSON statistics file not created")
            return
        print("PASS: JSON statistics file created")
        
        # Load and validate contact map
        try:
            contact_map = pd.read_csv(output_file, index_col=0)
        except Exception as e:
            print(f"FAIL: Could not read contact map CSV: {e}")
            return
        print("PASS: Contact map CSV readable")
        
        # Test 3: Correct dimensions
        expected_residues = 20
        if contact_map.shape != (expected_residues, expected_residues):
            print(f"FAIL: Contact map dimensions {contact_map.shape}, expected ({expected_residues}, {expected_residues})")
            return
        print("PASS: Contact map has correct dimensions")
        
        # Test 4: Symmetric matrix
        contact_array = contact_map.values
        if not np.allclose(contact_array, contact_array.T):
            print("FAIL: Contact map is not symmetric")
            return
        print("PASS: Contact map is symmetric")
        
        # Test 5: Diagonal is zero
        if not np.allclose(np.diag(contact_array), 0):
            print("FAIL: Contact map diagonal is not zero")
            return
        print("PASS: Contact map diagonal is zero")
        
        # Test 6: Binary values
        unique_vals = np.unique(contact_array)
        if not all(val in [0, 1] for val in unique_vals):
            print(f"FAIL: Contact map contains non-binary values: {unique_vals}")
            return
        print("PASS: Contact map contains only binary values")
        
        # Test 7: JSON statistics
        try:
            with open(json_file, 'r') as f:
                stats = json.load(f)
        except Exception as e:
            print(f"FAIL: Could not read JSON statistics: {e}")
            return
        print("PASS: JSON statistics readable")
        
        # Test 8: Required statistics fields
        required_fields = ['total_residues', 'total_contacts', 'contact_density', 'average_contacts_per_residue']
        for field in required_fields:
            if field not in stats:
                print(f"FAIL: Missing required field in statistics: {field}")
                return
        print("PASS: All required statistics fields present")
        
        # Test 9: Statistics values reasonable
        if stats['total_residues'] != expected_residues:
            print(f"FAIL: Incorrect total_residues: {stats['total_residues']}")
            return
        print("PASS: Correct total_residues in statistics")
        
        # Test 10: Contact density calculation
        total_contacts = np.sum(contact_array) // 2  # Divide by 2 because matrix is symmetric
        expected_density = total_contacts / (expected_residues * (expected_residues - 1) / 2)
        if not np.isclose(stats['contact_density'], expected_density, rtol=0.01):
            print(f"FAIL: Incorrect contact density calculation")
            return
        print("PASS: Contact density correctly calculated")
        
        # Test different methods
        # Test 11: min_distance method
        cmd_min = cmd.copy()
        cmd_min[cmd_min.index("ca_only")] = "min_distance"
        cmd_min[cmd_min.index(output_file)] = "contact_map_min.csv"
        
        try:
            result = subprocess.run(cmd_min, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print("FAIL: min_distance method failed")
                return
        except:
            print("FAIL: min_distance method execution error")
            return
        print("PASS: min_distance method works")
        
        # Test 12: cb_distance method
        cmd_cb = cmd.copy()
        cmd_cb[cmd_cb.index("ca_only")] = "cb_distance"
        cmd_cb[cmd_cb.index(output_file)] = "contact_map_cb.csv"
        
        try:
            result = subprocess.run(cmd_cb, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print("FAIL: cb_distance method failed")
                return
        except:
            print("FAIL: cb_distance method execution error")
            return
        print("PASS: cb_distance method works")
        
        # Test 13: Different threshold
        cmd_thresh = cmd.copy()
        cmd_thresh[cmd_thresh.index("8.0")] = "5.0"
        cmd_thresh[cmd_thresh.index(output_file)] = "contact_map_thresh.csv"
        
        try:
            result = subprocess.run(cmd_thresh, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                contact_map_thresh = pd.read_csv("contact_map_thresh.csv", index_col=0)
                # Should have fewer contacts with smaller threshold
                if np.sum(contact_map_thresh.values) >= np.sum(contact_array):
                    print("FAIL: Smaller threshold should produce fewer contacts")
                    return
        except:
            print("FAIL: Different threshold test failed")
            return
        print("PASS: Different threshold produces expected results")
        
        # Test 14: Sequence separation
        # Check that contacts within min_separation are excluded
        min_sep = 4
        for i in range(expected_residues):
            for j in range(max(0, i-min_sep+1), min(expected_residues, i+min_sep)):
                if i != j and contact_array[i, j] != 0:
                    print(f"FAIL: Contact found within sequence separation limit: {i}, {j}")
                    return
        print("PASS: Sequence separation correctly applied")
        
        # SCORE 1: Contact map completeness (fraction of expected contacts found)
        # For a helical structure, expect some local and medium-range contacts
        expected_contacts = 0
        actual_contacts = np.sum(contact_array) // 2
        
        # Estimate expected contacts for helical structure
        for i in range(expected_residues):
            for j in range(i + min_sep, expected_residues):
                # Calculate actual distance between CA atoms
                atom_i = next(a for a in test_data if a['residue_id'] == i+1 and a['atom_name'] == 'CA')
                atom_j = next(a for a in test_data if a['residue_id'] == j+1 and a['atom_name'] == 'CA')
                dist = np.sqrt((atom_i['x'] - atom_j['x'])**2 + 
                              (atom_i['y'] - atom_j['y'])**2 + 
                              (atom_i['z'] - atom_j['z'])**2)
                if dist <= 8.0:
                    expected_contacts += 1
        
        completeness_score = min(1.0, actual_contacts / max(1, expected_contacts)) if expected_contacts > 0 else 1.0
        print(f"SCORE: {completeness_score:.3f}")
        
        # SCORE 2: Statistics accuracy
        stats_accuracy = 1.0
        if abs(stats['total_contacts'] - actual_contacts) > 0:
            stats_accuracy *= 0.8
        if abs(stats['average_contacts_per_residue'] - (actual_contacts * 2 / expected_residues)) > 0.1:
            stats_accuracy *= 0.8
        
        print(f"SCORE: {stats_accuracy:.3f}")

if __name__ == "__main__":
    run_test()
