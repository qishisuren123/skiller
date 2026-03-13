import subprocess
import tempfile
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

def create_data():
    """Generate synthetic PDB data for testing"""
    
    # Create synthetic PDB data with multiple chains
    pdb_lines = []
    
    # Chain A - Alpha helix region
    residues_a = ['ALA', 'VAL', 'LEU', 'ILE', 'PHE', 'TRP', 'TYR', 'ASP', 'GLU', 'LYS']
    atom_id = 1
    
    for i, res in enumerate(residues_a):
        res_num = i + 1
        # Typical atoms for each residue (simplified)
        atoms = ['N', 'CA', 'C', 'O']
        if res != 'GLY':
            atoms.append('CB')
        
        for j, atom in enumerate(atoms):
            # Generate coordinates in helical pattern
            x = 10.0 + i * 1.5 + np.random.normal(0, 0.1)
            y = 5.0 + j * 1.2 + np.random.normal(0, 0.1)
            z = i * 1.54 + np.random.normal(0, 0.1)  # helical rise
            
            # B-factor varies by position and atom type
            b_factor = 20.0 + i * 2.0 + np.random.normal(0, 5.0)
            b_factor = max(5.0, min(80.0, b_factor))
            
            line = f"ATOM  {atom_id:5d}  {atom:<3s} {res} A{res_num:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00{b_factor:6.2f}           {atom[0]}"
            pdb_lines.append(line)
            atom_id += 1
    
    # Chain B - Beta sheet region
    residues_b = ['GLY', 'SER', 'THR', 'ASN', 'GLN', 'CYS', 'MET', 'PRO']
    
    for i, res in enumerate(residues_b):
        res_num = i + 1
        atoms = ['N', 'CA', 'C', 'O']
        if res != 'GLY':
            atoms.append('CB')
        
        for j, atom in enumerate(atoms):
            # Generate coordinates in extended pattern
            x = 25.0 + i * 3.8 + np.random.normal(0, 0.1)
            y = 10.0 + (-1)**i * 2.0 + np.random.normal(0, 0.1)
            z = 2.0 + j * 1.1 + np.random.normal(0, 0.1)
            
            # Different B-factor pattern for chain B
            b_factor = 15.0 + i * 1.5 + np.random.normal(0, 3.0)
            b_factor = max(8.0, min(60.0, b_factor))
            
            line = f"ATOM  {atom_id:5d}  {atom:<3s} {res} B{res_num:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00{b_factor:6.2f}           {atom[0]}"
            pdb_lines.append(line)
            atom_id += 1
    
    # Add some water molecules
    for i in range(5):
        x = np.random.uniform(0, 40)
        y = np.random.uniform(0, 20)
        z = np.random.uniform(0, 15)
        b_factor = np.random.uniform(30, 70)
        
        line = f"HETATM{atom_id:5d}  O   HOH W{i+1:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00{b_factor:6.2f}           O"
        pdb_lines.append(line)
        atom_id += 1
    
    return '\n'.join(pdb_lines)

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create synthetic data
        pdb_data = create_data()
        
        # Write PDB data to file
        with open('test_structure.pdb', 'w') as f:
            f.write(pdb_data)
        
        # Test basic functionality
        cmd = ['python', 'generated.py', '--input', 'test_structure.pdb', 
               '--output-json', 'results.json', '--output-csv', 'residues.csv',
               '--summary', 'summary.txt']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except:
            # Try alternative argument names
            cmd = ['python', 'generated.py', '-i', 'test_structure.pdb', 
                   '-j', 'results.json', '-c', 'residues.csv', '-s', 'summary.txt']
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            except:
                cmd = ['python', 'generated.py', 'test_structure.pdb']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Check basic execution
        print("PASS" if result.returncode == 0 else "FAIL", "- Script executes without errors")
        
        # Check output files exist
        json_exists = os.path.exists('results.json') or any(f.endswith('.json') for f in os.listdir('.'))
        csv_exists = os.path.exists('residues.csv') or any(f.endswith('.csv') for f in os.listdir('.'))
        
        print("PASS" if json_exists else "FAIL", "- JSON output file created")
        print("PASS" if csv_exists else "FAIL", "- CSV output file created")
        
        # Load and validate JSON output
        json_valid = False
        residue_stats_valid = False
        chain_stats_valid = False
        
        try:
            json_files = [f for f in os.listdir('.') if f.endswith('.json')]
            if json_files:
                with open(json_files[0], 'r') as f:
                    data = json.load(f)
                json_valid = True
                
                # Check for residue-level statistics
                if 'residues' in data or 'residue_stats' in data:
                    residue_stats_valid = True
                
                # Check for chain-level statistics  
                if 'chains' in data or 'chain_stats' in data:
                    chain_stats_valid = True
        except:
            pass
        
        print("PASS" if json_valid else "FAIL", "- JSON output is valid")
        print("PASS" if residue_stats_valid else "FAIL", "- Residue statistics present in output")
        print("PASS" if chain_stats_valid else "FAIL", "- Chain statistics present in output")
        
        # Load and validate CSV output
        csv_valid = False
        csv_residue_count = 0
        csv_has_coords = False
        csv_has_bfactor = False
        
        try:
            csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
            if csv_files:
                df = pd.read_csv(csv_files[0])
                csv_valid = True
                csv_residue_count = len(df)
                
                # Check for coordinate columns
                coord_cols = [col for col in df.columns if any(c in col.lower() for c in ['x', 'y', 'z', 'coord', 'center'])]
                csv_has_coords = len(coord_cols) >= 3
                
                # Check for B-factor column
                bfactor_cols = [col for col in df.columns if any(b in col.lower() for b in ['b_factor', 'bfactor', 'b-factor', 'temperature'])]
                csv_has_bfactor = len(bfactor_cols) > 0
        except:
            pass
        
        print("PASS" if csv_valid else "FAIL", "- CSV output is valid")
        print("PASS" if csv_residue_count >= 15 else "FAIL", f"- CSV contains expected residue count ({csv_residue_count})")
        print("PASS" if csv_has_coords else "FAIL", "- CSV contains coordinate information")
        print("PASS" if csv_has_bfactor else "FAIL", "- CSV contains B-factor information")
        
        # Test chain filtering
        filter_cmd = ['python', 'generated.py', '--input', 'test_structure.pdb', 
                     '--chain', 'A', '--output-json', 'chain_a.json']
        try:
            filter_result = subprocess.run(filter_cmd, capture_output=True, text=True, timeout=30)
            chain_filter_works = filter_result.returncode == 0
        except:
            try:
                filter_cmd = ['python', 'generated.py', 'test_structure.pdb', '--chains', 'A']
                filter_result = subprocess.run(filter_cmd, capture_output=True, text=True, timeout=30)
                chain_filter_works = filter_result.returncode == 0
            except:
                chain_filter_works = False
        
        print("PASS" if chain_filter_works else "FAIL", "- Chain filtering functionality works")
        
        # Test B-factor filtering
        bfactor_cmd = ['python', 'generated.py', '--input', 'test_structure.pdb', 
                      '--max-bfactor', '50.0', '--output-json', 'filtered.json']
        try:
            bfactor_result = subprocess.run(bfactor_cmd, capture_output=True, text=True, timeout=30)
            bfactor_filter_works = bfactor_result.returncode == 0
        except:
            bfactor_filter_works = False
        
        print("PASS" if bfactor_filter_works else "FAIL", "- B-factor filtering functionality works")
        
        # Calculate accuracy scores
        structure_accuracy = 0.0
        if json_valid and csv_valid:
            # Score based on data completeness and correctness
            completeness_score = (residue_stats_valid + chain_stats_valid + csv_has_coords + csv_has_bfactor) / 4.0
            count_accuracy = min(1.0, csv_residue_count / 18.0) if csv_residue_count > 0 else 0.0
            structure_accuracy = (completeness_score + count_accuracy) / 2.0
        
        functionality_score = 0.0
        if result.returncode == 0:
            features = [json_exists, csv_exists, json_valid, residue_stats_valid, 
                       chain_stats_valid, csv_has_coords, csv_has_bfactor]
            functionality_score = sum(features) / len(features)
        
        print(f"SCORE: {structure_accuracy:.3f} - Structure analysis accuracy")
        print(f"SCORE: {functionality_score:.3f} - Overall functionality score")

if __name__ == "__main__":
    run_test()
