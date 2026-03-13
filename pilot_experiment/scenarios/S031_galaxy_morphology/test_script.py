import os
import sys
import subprocess
import tempfile
import json
import numpy as np
import pandas as pd
from pathlib import Path

def create_data():
    """Generate synthetic galaxy photometric catalog data"""
    np.random.seed(42)
    n_galaxies = 500
    
    # Generate different galaxy populations
    n_elliptical = 150
    n_spiral = 200
    n_irregular = 100
    n_lenticular = 50
    
    data = []
    
    # Elliptical galaxies
    for i in range(n_elliptical):
        u_mag = np.random.normal(20.5, 0.8)
        g_mag = np.random.normal(19.2, 0.6)
        r_mag = np.random.normal(18.3, 0.5)
        i_mag = np.random.normal(17.9, 0.5)
        z_mag = np.random.normal(17.7, 0.6)
        
        data.append({
            'galaxy_id': f'GAL_{i:05d}',
            'u_mag': u_mag,
            'g_mag': g_mag,
            'r_mag': r_mag,
            'i_mag': i_mag,
            'z_mag': z_mag,
            'half_light_radius': np.random.lognormal(0.8, 0.4),
            'axis_ratio': np.random.uniform(0.7, 1.0),
            'concentration_index': np.random.normal(3.2, 0.3),
            'surface_brightness': np.random.normal(22.5, 1.0),
            'u_mag_err': np.random.uniform(0.05, 0.2),
            'g_mag_err': np.random.uniform(0.02, 0.1),
            'r_mag_err': np.random.uniform(0.02, 0.08),
            'i_mag_err': np.random.uniform(0.02, 0.08),
            'z_mag_err': np.random.uniform(0.03, 0.12)
        })
    
    # Spiral galaxies
    for i in range(n_spiral):
        u_mag = np.random.normal(19.8, 0.9)
        g_mag = np.random.normal(18.8, 0.7)
        r_mag = np.random.normal(18.2, 0.6)
        i_mag = np.random.normal(17.9, 0.6)
        z_mag = np.random.normal(17.8, 0.7)
        
        data.append({
            'galaxy_id': f'GAL_{i+n_elliptical:05d}',
            'u_mag': u_mag,
            'g_mag': g_mag,
            'r_mag': r_mag,
            'i_mag': i_mag,
            'z_mag': z_mag,
            'half_light_radius': np.random.lognormal(1.2, 0.5),
            'axis_ratio': np.random.uniform(0.3, 0.8),
            'concentration_index': np.random.normal(2.5, 0.2),
            'surface_brightness': np.random.normal(21.8, 0.8),
            'u_mag_err': np.random.uniform(0.03, 0.15),
            'g_mag_err': np.random.uniform(0.02, 0.08),
            'r_mag_err': np.random.uniform(0.02, 0.06),
            'i_mag_err': np.random.uniform(0.02, 0.06),
            'z_mag_err': np.random.uniform(0.02, 0.1)
        })
    
    # Irregular galaxies
    for i in range(n_irregular):
        u_mag = np.random.normal(19.2, 1.0)
        g_mag = np.random.normal(18.5, 0.8)
        r_mag = np.random.normal(18.3, 0.7)
        i_mag = np.random.normal(18.1, 0.7)
        z_mag = np.random.normal(18.0, 0.8)
        
        data.append({
            'galaxy_id': f'GAL_{i+n_elliptical+n_spiral:05d}',
            'u_mag': u_mag,
            'g_mag': g_mag,
            'r_mag': r_mag,
            'i_mag': i_mag,
            'z_mag': z_mag,
            'half_light_radius': np.random.lognormal(0.5, 0.6),
            'axis_ratio': np.random.uniform(0.4, 0.9),
            'concentration_index': np.random.normal(1.8, 0.3),
            'surface_brightness': np.random.normal(21.2, 1.2),
            'u_mag_err': np.random.uniform(0.05, 0.25),
            'g_mag_err': np.random.uniform(0.03, 0.12),
            'r_mag_err': np.random.uniform(0.03, 0.1),
            'i_mag_err': np.random.uniform(0.03, 0.1),
            'z_mag_err': np.random.uniform(0.04, 0.15)
        })
    
    # Lenticular galaxies
    for i in range(n_lenticular):
        u_mag = np.random.normal(20.0, 0.7)
        g_mag = np.random.normal(18.9, 0.5)
        r_mag = np.random.normal(18.1, 0.4)
        i_mag = np.random.normal(17.8, 0.4)
        z_mag = np.random.normal(17.6, 0.5)
        
        data.append({
            'galaxy_id': f'GAL_{i+n_elliptical+n_spiral+n_irregular:05d}',
            'u_mag': u_mag,
            'g_mag': g_mag,
            'r_mag': r_mag,
            'i_mag': i_mag,
            'z_mag': z_mag,
            'half_light_radius': np.random.lognormal(0.9, 0.3),
            'axis_ratio': np.random.uniform(0.75, 1.0),
            'concentration_index': np.random.normal(3.0, 0.25),
            'surface_brightness': np.random.normal(22.0, 0.8),
            'u_mag_err': np.random.uniform(0.04, 0.18),
            'g_mag_err': np.random.uniform(0.02, 0.09),
            'r_mag_err': np.random.uniform(0.02, 0.07),
            'i_mag_err': np.random.uniform(0.02, 0.07),
            'z_mag_err': np.random.uniform(0.03, 0.11)
        })
    
    return pd.DataFrame(data)

def run_test():
    results = {'passed': 0, 'failed': 0, 'tests': []}
    
    def test_condition(condition, description):
        if condition:
            results['passed'] += 1
            results['tests'].append(f"PASS: {description}")
            return True
        else:
            results['failed'] += 1
            results['tests'].append(f"FAIL: {description}")
            return False
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test data
        catalog_data = create_data()
        input_file = tmpdir / "input_catalog.csv"
        catalog_data.to_csv(input_file, index=False)
        
        output_catalog = tmpdir / "output_catalog.csv"
        summary_json = tmpdir / "summary.json"
        
        # Test basic execution
        try:
            cmd = [
                sys.executable, "generated.py",
                "--input-catalog", str(input_file),
                "--output-catalog", str(output_catalog),
                "--summary", str(summary_json)
            ]
            
            # Try alternative argument names
            if not os.path.exists("generated.py"):
                results['tests'].append("FAIL: generated.py not found")
                return results
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                # Try alternative argument names
                cmd_alt = [
                    sys.executable, "generated.py",
                    "--input_catalog", str(input_file),
                    "--output_catalog", str(output_catalog),
                    "--summary", str(summary_json)
                ]
                result = subprocess.run(cmd_alt, capture_output=True, text=True, timeout=30)
            
            test_condition(result.returncode == 0, f"Script executes successfully (return code: {result.returncode})")
            
            if result.returncode != 0:
                results['tests'].append(f"STDERR: {result.stderr}")
                return results
                
        except subprocess.TimeoutExpired:
            test_condition(False, "Script completes within time limit")
            return results
        except Exception as e:
            test_condition(False, f"Script execution: {str(e)}")
            return results
        
        # Test output files exist
        test_condition(output_catalog.exists(), "Output catalog file created")
        test_condition(summary_json.exists(), "Summary JSON file created")
        
        if not output_catalog.exists() or not summary_json.exists():
            return results
        
        # Load and test output data
        try:
            output_df = pd.read_csv(output_catalog)
            with open(summary_json, 'r') as f:
                summary_data = json.load(f)
        except Exception as e:
            test_condition(False, f"Output files readable: {str(e)}")
            return results
        
        # Test output catalog structure
        test_condition('galaxy_id' in output_df.columns, "Output contains galaxy_id column")
        test_condition('morphology' in output_df.columns or 'morphological_type' in output_df.columns, 
                      "Output contains morphology classification column")
        
        # Get morphology column name
        morph_col = 'morphology' if 'morphology' in output_df.columns else 'morphological_type'
        
        if morph_col in output_df.columns:
            # Test color calculations
            color_cols = ['g_r_color', 'r_i_color', 'u_g_color']
            color_found = any(col in output_df.columns for col in color_cols) or \
                         any('color' in col.lower() for col in output_df.columns)
            test_condition(color_found, "Color indices calculated and included")
            
            # Test morphological classifications
            unique_morphs = set(output_df[morph_col].dropna().str.lower())
            expected_morphs = {'elliptical', 'spiral', 'irregular', 'lenticular'}
            morph_overlap = len(unique_morphs.intersection(expected_morphs))
            test_condition(morph_overlap >= 3, f"At least 3 expected morphological types found ({morph_overlap}/4)")
            
            # Test that classifications are reasonable
            n_classified = len(output_df.dropna(subset=[morph_col]))
            test_condition(n_classified >= 400, f"Most galaxies classified ({n_classified}/500)")
            
            # Test quality flags
            quality_cols = [col for col in output_df.columns if 'quality' in col.lower() or 'flag' in col.lower()]
            test_condition(len(quality_cols) > 0, "Quality assessment flags included")
        
        # Test summary statistics
        test_condition('morphology_fractions' in summary_data or 'population_statistics' in summary_data,
                      "Summary contains morphology population statistics")
        
        test_condition('mean_properties' in summary_data or 'statistics' in summary_data,
                      "Summary contains mean properties per type")
        
        # Test statistical reasonableness
        if morph_col in output_df.columns:
            elliptical_count = len(output_df[output_df[morph_col].str.lower().str.contains('elliptical', na=False)])
            spiral_count = len(output_df[output_df[morph_col].str.lower().str.contains('spiral', na=False)])
            
            # Should find reasonable numbers of each type
            test_condition(elliptical_count > 50, f"Reasonable number of ellipticals found ({elliptical_count})")
            test_condition(spiral_count > 50, f"Reasonable number of spirals found ({spiral_count})")
        
        # Calculate accuracy score (how well it recovers the input populations)
        accuracy_score = 0.0
        if morph_col in output_df.columns:
            # Expected roughly: 150 elliptical, 200 spiral, 100 irregular, 50 lenticular
            expected = {'elliptical': 150, 'spiral': 200, 'irregular': 100, 'lenticular': 50}
            total_error = 0
            
            for morph_type, expected_count in expected.items():
                actual_count = len(output_df[output_df[morph_col].str.lower().str.contains(morph_type, na=False)])
                error = abs(actual_count - expected_count) / expected_count
                total_error += error
            
            accuracy_score = max(0, 1 - total_error / 4)
        
        # Calculate completeness score
        completeness_score = 0.0
        if morph_col in output_df.columns:
            n_classified = len(output_df.dropna(subset=[morph_col]))
            completeness_score = n_classified / 500
        
        results['tests'].append(f"SCORE: Classification accuracy: {accuracy_score:.3f}")
        results['tests'].append(f"SCORE: Completeness: {completeness_score:.3f}")
    
    return results

if __name__ == "__main__":
    results = run_test()
    
    for test in results['tests']:
        print(test)
    
    print(f"\nSummary: {results['passed']} passed, {results['failed']} failed")
