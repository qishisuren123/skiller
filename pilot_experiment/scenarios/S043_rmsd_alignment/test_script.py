import numpy as np
import json
import subprocess
import tempfile
import os
import sys
from pathlib import Path

def create_data():
    """Generate synthetic protein coordinate data for testing"""
    np.random.seed(42)
    
    # Create reference structure (50 atoms in a roughly helical arrangement)
    n_atoms = 50
    t = np.linspace(0, 4*np.pi, n_atoms)
    reference = np.column_stack([
        3 * np.cos(t) + np.random.normal(0, 0.1, n_atoms),
        3 * np.sin(t) + np.random.normal(0, 0.1, n_atoms),
        t + np.random.normal(0, 0.1, n_atoms)
    ])
    
    # Create target structure by applying known transformation + noise
    rotation_angle = np.pi/4
    R_true = np.array([
        [np.cos(rotation_angle), -np.sin(rotation_angle), 0],
        [np.sin(rotation_angle), np.cos(rotation_angle), 0],
        [0, 0, 1]
    ])
    translation_true = np.array([2.0, -1.5, 3.0])
    
    target = (reference @ R_true.T) + translation_true
    target += np.random.normal(0, 0.2, target.shape)  # Add noise
    
    # Create a second test case with smaller structures
    n_atoms_small = 20
    ref_small = np.random.normal(0, 2, (n_atoms_small, 3))
    target_small = ref_small + np.random.normal(0, 0.5, (n_atoms_small, 3))
    
    return {
        'reference': reference,
        'target': target,
        'reference_small': ref_small,
        'target_small': target_small,
        'rotation_true': R_true,
        'translation_true': translation_true
    }

def run_test():
    data = create_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Save test data
        ref_file = tmpdir / "reference.npy"
        target_file = tmpdir / "target.npy"
        ref_small_file = tmpdir / "ref_small.npy"
        target_small_file = tmpdir / "target_small.npy"
        
        np.save(ref_file, data['reference'])
        np.save(target_file, data['target'])
        np.save(ref_small_file, data['reference_small'])
        np.save(target_small_file, data['target_small'])
        
        output_file = tmpdir / "aligned.npy"
        report_file = tmpdir / "report.json"
        
        # Test 1: Basic functionality
        cmd = [
            sys.executable, "generated.py",
            "--reference", str(ref_file),
            "--target", str(target_file),
            "--output", str(output_file),
            "--report", str(report_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            script_runs = result.returncode == 0
        except:
            script_runs = False
        
        print(f"PASS: Script runs without errors: {script_runs}")
        
        if not script_runs:
            print(f"FAIL: Script execution failed")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return
        
        # Check output files exist
        output_exists = output_file.exists()
        report_exists = report_file.exists()
        print(f"PASS: Output file created: {output_exists}")
        print(f"PASS: Report file created: {report_exists}")
        
        if not (output_exists and report_exists):
            print("FAIL: Required output files not created")
            return
        
        # Load results
        try:
            aligned_coords = np.load(output_file)
            with open(report_file, 'r') as f:
                report = json.load(f)
        except Exception as e:
            print(f"FAIL: Could not load output files: {e}")
            return
        
        # Test coordinate dimensions
        coords_shape_correct = aligned_coords.shape == data['target'].shape
        print(f"PASS: Aligned coordinates have correct shape: {coords_shape_correct}")
        
        # Test report contents
        required_keys = ['initial_rmsd', 'final_rmsd', 'rotation_matrix', 'translation_vector']
        report_complete = all(key in report for key in required_keys)
        print(f"PASS: Report contains required keys: {report_complete}")
        
        if report_complete:
            # Test RMSD improvement
            initial_rmsd = report['initial_rmsd']
            final_rmsd = report['final_rmsd']
            rmsd_improved = final_rmsd < initial_rmsd
            print(f"PASS: RMSD improved after alignment: {rmsd_improved}")
            
            # Test rotation matrix properties
            R = np.array(report['rotation_matrix'])
            is_rotation_matrix = (
                R.shape == (3, 3) and
                np.allclose(np.linalg.det(R), 1.0, atol=0.1) and
                np.allclose(R @ R.T, np.eye(3), atol=0.1)
            )
            print(f"PASS: Rotation matrix is valid: {is_rotation_matrix}")
            
            # Test translation vector
            t = np.array(report['translation_vector'])
            translation_valid = t.shape == (3,) and np.all(np.isfinite(t))
            print(f"PASS: Translation vector is valid: {translation_valid}")
            
            # Test final RMSD is reasonable
            final_rmsd_reasonable = 0.0 <= final_rmsd <= 10.0
            print(f"PASS: Final RMSD is reasonable: {final_rmsd_reasonable}")
        
        # Test 2: Small structure
        output_file2 = tmpdir / "aligned_small.npy"
        report_file2 = tmpdir / "report_small.json"
        
        cmd2 = [
            sys.executable, "generated.py",
            "--reference", str(ref_small_file),
            "--target", str(target_small_file),
            "--output", str(output_file2),
            "--report", str(report_file2)
        ]
        
        try:
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
            small_test_runs = result2.returncode == 0
        except:
            small_test_runs = False
        
        print(f"PASS: Small structure test runs: {small_test_runs}")
        
        if small_test_runs and output_file2.exists() and report_file2.exists():
            try:
                aligned_small = np.load(output_file2)
                with open(report_file2, 'r') as f:
                    report_small = json.load(f)
                
                small_coords_correct = aligned_small.shape == data['target_small'].shape
                small_report_complete = all(key in report_small for key in required_keys)
                print(f"PASS: Small structure coordinates correct: {small_coords_correct}")
                print(f"PASS: Small structure report complete: {small_report_complete}")
            except:
                print("FAIL: Could not process small structure results")
        
        # Test 3: Identical structures
        identical_output = tmpdir / "identical.npy"
        identical_report = tmpdir / "identical_report.json"
        
        cmd3 = [
            sys.executable, "generated.py",
            "--reference", str(ref_file),
            "--target", str(ref_file),  # Same as reference
            "--output", str(identical_output),
            "--report", str(identical_report)
        ]
        
        try:
            result3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=30)
            identical_test_runs = result3.returncode == 0
        except:
            identical_test_runs = False
        
        print(f"PASS: Identical structures test runs: {identical_test_runs}")
        
        if identical_test_runs and identical_report.exists():
            try:
                with open(identical_report, 'r') as f:
                    identical_rep = json.load(f)
                near_zero_rmsd = identical_rep.get('final_rmsd', 1.0) < 0.01
                print(f"PASS: Identical structures give near-zero RMSD: {near_zero_rmsd}")
            except:
                print("FAIL: Could not check identical structure RMSD")
        
        # Scoring metrics
        if report_complete and coords_shape_correct:
            # Score 1: Alignment quality (how much RMSD improved)
            rmsd_reduction = max(0, (initial_rmsd - final_rmsd) / initial_rmsd)
            alignment_score = min(1.0, rmsd_reduction * 2)  # Scale to 0-1
            print(f"SCORE: Alignment quality: {alignment_score:.3f}")
            
            # Score 2: Implementation completeness
            implementation_score = 0.0
            if script_runs: implementation_score += 0.3
            if output_exists and report_exists: implementation_score += 0.2
            if coords_shape_correct: implementation_score += 0.2
            if report_complete: implementation_score += 0.2
            if is_rotation_matrix: implementation_score += 0.1
            print(f"SCORE: Implementation completeness: {implementation_score:.3f}")
        else:
            print("SCORE: Alignment quality: 0.000")
            print("SCORE: Implementation completeness: 0.000")

if __name__ == "__main__":
    run_test()
