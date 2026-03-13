import numpy as np
import pandas as pd
import json
import subprocess
import tempfile
import os
from scipy.spatial.distance import cdist
from scipy.cluster.hierarchy import linkage, fcluster
import sys

def create_data():
    """Generate synthetic protein structure data"""
    np.random.seed(42)
    
    # Generate protein coordinates (backbone + sidechains)
    n_residues = 150
    protein_coords = []
    atom_props = []
    
    # Create a roughly globular protein structure
    center = np.array([0, 0, 0])
    
    for i in range(n_residues):
        # Backbone atoms (N, CA, C, O)
        base_pos = center + np.random.normal(0, 8, 3)
        
        # Add some secondary structure bias
        if i % 10 < 4:  # alpha helix regions
            base_pos += np.array([0, 0, i * 1.5])
        elif i % 10 < 7:  # beta sheet regions  
            base_pos += np.array([i * 0.8, (-1)**i * 2, 0])
            
        for j, atom_type in enumerate(['N', 'CA', 'C', 'O']):
            pos = base_pos + np.random.normal(0, 0.5, 3)
            protein_coords.append([i+1, atom_type, pos[0], pos[1], pos[2]])
            
            # Atom properties
            vdw_radius = {'N': 1.55, 'CA': 1.7, 'C': 1.7, 'O': 1.52}[atom_type]
            hydrophobicity = {'N': -0.2, 'CA': 0.1, 'C': 0.0, 'O': -0.4}[atom_type]
            charge = {'N': -0.3, 'CA': 0.0, 'C': 0.5, 'O': -0.5}[atom_type]
            
            atom_props.append([i+1, atom_type, vdw_radius, hydrophobicity, charge])
        
        # Add sidechain atoms for variety
        if np.random.random() > 0.3:
            sidechain_atoms = np.random.choice(['CB', 'CG', 'CD', 'CE', 'NZ', 'OG', 'SG'], 
                                             size=np.random.randint(1, 4), replace=False)
            for atom_type in sidechain_atoms:
                pos = base_pos + np.random.normal(0, 2, 3)
                protein_coords.append([i+1, atom_type, pos[0], pos[1], pos[2]])
                
                vdw_radius = 1.7 if atom_type.startswith('C') else 1.55
                hydrophobicity = 0.3 if atom_type.startswith('C') else -0.1
                charge = np.random.normal(0, 0.2)
                
                atom_props.append([i+1, atom_type, vdw_radius, hydrophobicity, charge])
    
    # Convert to DataFrames
    coords_df = pd.DataFrame(protein_coords, 
                           columns=['residue_id', 'atom_type', 'x', 'y', 'z'])
    props_df = pd.DataFrame(atom_props,
                          columns=['residue_id', 'atom_type', 'vdw_radius', 'hydrophobicity', 'charge'])
    
    return coords_df, props_df

def run_test():
    results = {'passed': 0, 'failed': 0, 'tests': []}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        coords_df, props_df = create_data()
        
        coords_file = 'protein_coords.csv'
        props_file = 'atom_props.csv'
        sites_file = 'binding_sites.json'
        surface_file = 'surface_analysis.csv'
        
        coords_df.to_csv(coords_file, index=False)
        props_df.to_csv(props_file, index=False)
        
        # Test 1: Basic execution
        try:
            result = subprocess.run([
                sys.executable, '../generated.py',
                '--protein_coords', coords_file,
                '--atom_properties', props_file,
                '--output_sites', sites_file,
                '--output_surface', surface_file
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                results['passed'] += 1
                results['tests'].append("PASS: Script executes without errors")
            else:
                results['failed'] += 1
                results['tests'].append(f"FAIL: Script execution failed: {result.stderr}")
        except Exception as e:
            results['failed'] += 1
            results['tests'].append(f"FAIL: Script execution error: {str(e)}")
            return results
        
        # Test 2: Output files created
        if os.path.exists(sites_file) and os.path.exists(surface_file):
            results['passed'] += 1
            results['tests'].append("PASS: Output files created")
        else:
            results['failed'] += 1
            results['tests'].append("FAIL: Output files not created")
            return results
        
        # Load outputs for further testing
        try:
            with open(sites_file, 'r') as f:
                sites_data = json.load(f)
            surface_data = pd.read_csv(surface_file)
        except Exception as e:
            results['failed'] += 1
            results['tests'].append(f"FAIL: Cannot load output files: {str(e)}")
            return results
        
        # Test 3: JSON structure validation
        required_keys = ['binding_sites', 'metadata']
        if all(key in sites_data for key in required_keys):
            results['passed'] += 1
            results['tests'].append("PASS: JSON has required top-level keys")
        else:
            results['failed'] += 1
            results['tests'].append("FAIL: JSON missing required keys")
        
        # Test 4: Binding sites found
        binding_sites = sites_data.get('binding_sites', [])
        if len(binding_sites) >= 1:
            results['passed'] += 1
            results['tests'].append("PASS: At least one binding site identified")
        else:
            results['failed'] += 1
            results['tests'].append("FAIL: No binding sites identified")
        
        # Test 5: Binding site properties
        site_keys = ['site_id', 'center_coords', 'volume', 'score', 'druggability']
        if binding_sites and all(all(key in site for key in site_keys) for site in binding_sites):
            results['passed'] += 1
            results['tests'].append("PASS: Binding sites have required properties")
        else:
            results['failed'] += 1
            results['tests'].append("FAIL: Binding sites missing required properties")
        
        # Test 6: Volume filtering
        min_volume = 50.0
        valid_volumes = [site['volume'] >= min_volume for site in binding_sites if 'volume' in site]
        if valid_volumes and all(valid_volumes):
            results['passed'] += 1
            results['tests'].append("PASS: All sites meet minimum volume threshold")
        else:
            results['failed'] += 1
            results['tests'].append("FAIL: Sites below minimum volume threshold found")
        
        # Test 7: Score ranges
        scores = [site.get('score', 0) for site in binding_sites]
        if scores and all(0 <= score <= 1 for score in scores):
            results['passed'] += 1
            results['tests'].append("PASS: Binding site scores in valid range [0,1]")
        else:
            results['failed'] += 1
            results['tests'].append("FAIL: Binding site scores outside valid range")
        
        # Test 8: Sites ranked by score
        if len(scores) > 1:
            is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
            if is_sorted:
                results['passed'] += 1
                results['tests'].append("PASS: Binding sites ranked by score")
            else:
                results['failed'] += 1
                results['tests'].append("FAIL: Binding sites not properly ranked")
        else:
            results['passed'] += 1
            results['tests'].append("PASS: Single site ranking valid")
        
        # Test 9: Surface data structure
        required_surface_cols = ['x', 'y', 'z', 'cavity_id']
        if all(col in surface_data.columns for col in required_surface_cols):
            results['passed'] += 1
            results['tests'].append("PASS: Surface data has required columns")
        else:
            results['failed'] += 1
            results['tests'].append("FAIL: Surface data missing required columns")
        
        # Test 10: Surface points reasonable
        if len(surface_data) >= 100:
            results['passed'] += 1
            results['tests'].append("PASS: Sufficient surface points generated")
        else:
            results['failed'] += 1
            results['tests'].append("FAIL: Too few surface points generated")
        
        # Test 11: Coordinate ranges reasonable
        coords = surface_data[['x', 'y', 'z']].values
        coord_range = np.max(coords, axis=0) - np.min(coords, axis=0)
        if all(r > 5 and r < 100 for r in coord_range):
            results['passed'] += 1
            results['tests'].append("PASS: Surface coordinate ranges reasonable")
        else:
            results['failed'] += 1
            results['tests'].append("FAIL: Surface coordinate ranges unreasonable")
        
        # Test 12: Custom probe radius
        try:
            result = subprocess.run([
                sys.executable, '../generated.py',
                '--protein_coords', coords_file,
                '--atom_properties', props_file,
                '--probe_radius', '2.0',
                '--output_sites', 'sites2.json',
                '--output_surface', 'surface2.csv'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                results['passed'] += 1
                results['tests'].append("PASS: Custom probe radius accepted")
            else:
                results['failed'] += 1
                results['tests'].append("FAIL: Custom probe radius rejected")
        except:
            results['failed'] += 1
            results['tests'].append("FAIL: Custom probe radius test failed")
        
        # Test 13: Druggability scores
        druggability_scores = [site.get('druggability', -1) for site in binding_sites]
        if all(0 <= score <= 1 for score in druggability_scores):
            results['passed'] += 1
            results['tests'].append("PASS: Druggability scores in valid range")
        else:
            results['failed'] += 1
            results['tests'].append("FAIL: Invalid druggability scores")
        
        # Test 14: Metadata completeness
        metadata = sites_data.get('metadata', {})
        meta_keys = ['probe_radius', 'min_cavity_volume', 'n_sites_found']
        if all(key in metadata for key in meta_keys):
            results['passed'] += 1
            results['tests'].append("PASS: Metadata complete")
        else:
            results['failed'] += 1
            results['tests'].append("FAIL: Metadata incomplete")
        
        # SCORE 1: Site detection quality (0-1)
        expected_sites = 5  # Reasonable expectation
        actual_sites = len(binding_sites)
        detection_score = min(actual_sites / expected_sites, 1.0) if actual_sites > 0 else 0.0
        results['tests'].append(f"SCORE: Site detection quality: {detection_score:.3f}")
        
        # SCORE 2: Algorithm comprehensiveness (0-1)
        comprehensiveness = 0.0
        if binding_sites:
            # Check for diverse properties
            has_volume = any('volume' in site for site in binding_sites)
            has_score = any('score' in site for site in binding_sites)
            has_druggability = any('druggability' in site for site in binding_sites)
            has_coords = any('center_coords' in site for site in binding_sites)
            
            comprehensiveness = sum([has_volume, has_score, has_druggability, has_coords]) / 4.0
            
            # Bonus for surface analysis
            if len(surface_data) > 0:
                comprehensiveness = min(comprehensiveness + 0.2, 1.0)
        
        results['tests'].append(f"SCORE: Algorithm comprehensiveness: {comprehensiveness:.3f}")
    
    return results

if __name__ == "__main__":
    results = run_test()
    
    for test in results['tests']:
        print(test)
    
    print(f"\nSummary: {results['passed']} passed, {results['failed']} failed")
