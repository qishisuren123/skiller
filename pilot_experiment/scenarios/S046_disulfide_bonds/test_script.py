import os
import json
import subprocess
import tempfile
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
import shutil

def create_data():
    """Generate synthetic protein structure data with cysteine residues"""
    np.random.seed(42)
    
    # Create a protein with multiple chains and cysteine residues
    chains = ['A', 'B']
    cysteines = []
    
    # Chain A cysteines (4 residues)
    chain_a_positions = [
        [10.0, 15.0, 20.0],  # Cys 10
        [12.5, 17.2, 18.5],  # Cys 25 (close to first - should form bond)
        [25.0, 30.0, 35.0],  # Cys 45
        [27.8, 32.1, 33.2],  # Cys 60 (close to third - should form bond)
    ]
    
    # Chain B cysteines (3 residues)
    chain_b_positions = [
        [15.0, 20.0, 25.0],  # Cys 15
        [40.0, 45.0, 50.0],  # Cys 35 (isolated)
        [26.2, 31.5, 34.8],  # Cys 55 (close to chain A Cys 45 - inter-chain bond)
    ]
    
    residue_id = 1
    for i, pos in enumerate(chain_a_positions):
        res_num = [10, 25, 45, 60][i]
        # Add some noise to create realistic atomic positions
        ca_pos = np.array(pos) + np.random.normal(0, 0.1, 3)
        cb_pos = ca_pos + np.random.normal(0, 0.5, 3)
        sg_pos = cb_pos + np.random.normal(0, 0.3, 3)
        
        cysteines.extend([
            {
                'atom_id': residue_id * 3 - 2,
                'atom_name': 'CA',
                'residue_name': 'CYS',
                'chain_id': 'A',
                'residue_number': res_num,
                'x': float(ca_pos[0]),
                'y': float(ca_pos[1]),
                'z': float(ca_pos[2])
            },
            {
                'atom_id': residue_id * 3 - 1,
                'atom_name': 'CB',
                'residue_name': 'CYS',
                'chain_id': 'A',
                'residue_number': res_num,
                'x': float(cb_pos[0]),
                'y': float(cb_pos[1]),
                'z': float(cb_pos[2])
            },
            {
                'atom_id': residue_id * 3,
                'atom_name': 'SG',
                'residue_name': 'CYS',
                'chain_id': 'A',
                'residue_number': res_num,
                'x': float(sg_pos[0]),
                'y': float(sg_pos[1]),
                'z': float(sg_pos[2])
            }
        ])
        residue_id += 1
    
    for i, pos in enumerate(chain_b_positions):
        res_num = [15, 35, 55][i]
        ca_pos = np.array(pos) + np.random.normal(0, 0.1, 3)
        cb_pos = ca_pos + np.random.normal(0, 0.5, 3)
        sg_pos = cb_pos + np.random.normal(0, 0.3, 3)
        
        cysteines.extend([
            {
                'atom_id': residue_id * 3 - 2,
                'atom_name': 'CA',
                'residue_name': 'CYS',
                'chain_id': 'B',
                'residue_number': res_num,
                'x': float(ca_pos[0]),
                'y': float(ca_pos[1]),
                'z': float(ca_pos[2])
            },
            {
                'atom_id': residue_id * 3 - 1,
                'atom_name': 'CB',
                'residue_name': 'CYS',
                'chain_id': 'B',
                'residue_number': res_num,
                'x': float(cb_pos[0]),
                'y': float(cb_pos[1]),
                'z': float(cb_pos[2])
            },
            {
                'atom_id': residue_id * 3,
                'atom_name': 'SG',
                'residue_name': 'CYS',
                'chain_id': 'B',
                'residue_number': res_num,
                'x': float(sg_pos[0]),
                'y': float(sg_pos[1]),
                'z': float(sg_pos[2])
            }
        ])
        residue_id += 1
    
    return {'atoms': cysteines}

def run_test():
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        pdb_data = create_data()
        
        # Write input file
        with open('protein.json', 'w') as f:
            json.dump(pdb_data, f)
        
        # Test basic functionality
        result = subprocess.run([
            'python', 'generated.py',
            '--input', 'protein.json',
            '--output', 'bonds.json',
            '--distance-cutoff', '3.0',
            '--angle-tolerance', '25',
            '--energy-model', 'simple'
        ], capture_output=True, text=True)
        
        print("PASS" if result.returncode == 0 else "FAIL", ": Script runs without errors")
        print("PASS" if os.path.exists('bonds.json') else "FAIL", ": Output file created")
        
        if os.path.exists('bonds.json'):
            with open('bonds.json', 'r') as f:
                output = json.load(f)
            
            # Test output structure
            required_keys = ['disulfide_bonds', 'summary']
            print("PASS" if all(key in output for key in required_keys) else "FAIL", 
                  ": Output contains required top-level keys")
            
            # Test disulfide bonds detection
            bonds = output.get('disulfide_bonds', [])
            print("PASS" if len(bonds) >= 2 else "FAIL", 
                  f": Detected reasonable number of bonds ({len(bonds)})")
            
            # Test bond structure
            if bonds:
                bond = bonds[0]
                bond_keys = ['residue1', 'residue2', 'distance', 'bond_type', 'validated']
                print("PASS" if all(key in bond for key in bond_keys) else "FAIL",
                      ": Bond entries contain required fields")
                
                # Test distance values
                distances = [b.get('distance', 0) for b in bonds]
                print("PASS" if all(0 < d <= 3.0 for d in distances) else "FAIL",
                      ": All distances within cutoff range")
                
                # Test bond types
                bond_types = [b.get('bond_type') for b in bonds]
                valid_types = all(bt in ['intra-chain', 'inter-chain'] for bt in bond_types)
                print("PASS" if valid_types else "FAIL", ": Bond types properly classified")
                
                # Test validation status
                validated_bonds = [b for b in bonds if b.get('validated', False)]
                print("PASS" if len(validated_bonds) > 0 else "FAIL", 
                      ": Some bonds pass geometric validation")
            
            # Test summary statistics
            summary = output.get('summary', {})
            summary_keys = ['total_bonds', 'intra_chain_bonds', 'inter_chain_bonds']
            print("PASS" if all(key in summary for key in summary_keys) else "FAIL",
                  ": Summary contains required statistics")
            
            if 'total_bonds' in summary:
                total = summary['total_bonds']
                intra = summary.get('intra_chain_bonds', 0)
                inter = summary.get('inter_chain_bonds', 0)
                print("PASS" if total == intra + inter else "FAIL",
                      ": Bond counts are consistent")
        
        # Test different parameters
        result2 = subprocess.run([
            'python', 'generated.py',
            '--pdb', 'protein.json',
            '--out', 'bonds2.json',
            '--cutoff', '2.0',
            '--tolerance', '15',
            '--model', 'advanced'
        ], capture_output=True, text=True)
        
        print("PASS" if result2.returncode == 0 else "FAIL", 
              ": Script works with alternative argument names")
        
        if os.path.exists('bonds2.json'):
            with open('bonds2.json', 'r') as f:
                output2 = json.load(f)
            
            bonds2 = output2.get('disulfide_bonds', [])
            bonds1 = output.get('disulfide_bonds', []) if 'output' in locals() else []
            
            print("PASS" if len(bonds2) <= len(bonds1) else "FAIL",
                  ": Stricter cutoff reduces number of bonds")
            
            # Test energy calculations
            if bonds2:
                energies = [b.get('energy') for b in bonds2]
                print("PASS" if all(e is not None for e in energies) else "FAIL",
                      ": Energy values calculated for all bonds")
        
        # Calculate scores
        bond_detection_score = 0.0
        geometric_validation_score = 0.0
        
        if 'output' in locals() and 'disulfide_bonds' in output:
            bonds = output['disulfide_bonds']
            
            # Score based on expected bonds (should find ~3 bonds)
            expected_bonds = 3
            detected_bonds = len(bonds)
            bond_detection_score = min(1.0, detected_bonds / expected_bonds)
            
            # Score based on geometric validation quality
            if bonds:
                validated = sum(1 for b in bonds if b.get('validated', False))
                geometric_validation_score = validated / len(bonds)
        
        print(f"SCORE: {bond_detection_score:.3f} : Bond detection accuracy")
        print(f"SCORE: {geometric_validation_score:.3f} : Geometric validation quality")

if __name__ == "__main__":
    run_test()
