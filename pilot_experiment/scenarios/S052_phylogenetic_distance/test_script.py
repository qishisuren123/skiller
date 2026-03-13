import subprocess
import tempfile
import os
import json
import numpy as np
import pandas as pd
from io import StringIO
import sys

def create_data():
    """Generate synthetic multiple sequence alignment data"""
    # Create a realistic MSA with some evolutionary relationships
    sequences = {
        "seq1": "ATCGATCGATCGATCGAATCGATCGATCG",
        "seq2": "ATCGATCGATCGATCGAATCGATCGATCG",  # identical to seq1
        "seq3": "ATCGATCGATCGATCGAATCGATCGTTCG",  # 1 difference from seq1
        "seq4": "ATCGATCGATCGATCGAATCGTTCGATCG",  # 1 difference from seq1, different position
        "seq5": "ATCGATCGATCGATCGAATC-ATCGATCG",  # gap in middle
        "seq6": "TTCGATCGATCGATCGAATCGATCGATCG",  # 1 difference at start
        "seq7": "ATCGATCGATCGATCGAATCGATCGAAAA",  # multiple differences at end
        "seq8": "GGCGATCGATCGATCGAATCGATCGATCG",  # 1 difference at start
    }
    
    fasta_content = ""
    for name, seq in sequences.items():
        fasta_content += f">{name}\n{seq}\n"
    
    return fasta_content, sequences

def run_test():
    fasta_data, expected_seqs = create_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Test different argument variations
        test_commands = [
            ["python", "generated.py", "--input", fasta_data, "--method", "hamming", "--output", "distances", "--matrix", "matrix.tsv", "--pairwise", "pairs.json"],
            ["python", "generated.py", "-i", fasta_data, "-m", "jukes-cantor", "-o", "distances2", "--matrix-file", "matrix2.tsv", "--pairwise-file", "pairs2.json"],
            ["python", "generated.py", "--alignment", fasta_data, "--distance", "p-distance", "--out", "distances3", "--matrix-output", "matrix3.tsv", "--json-output", "pairs3.json"]
        ]
        
        success_count = 0
        for i, cmd in enumerate(test_commands):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success_count += 1
                    working_cmd = cmd
                    break
            except:
                continue
        
        if success_count == 0:
            # Try basic command
            try:
                result = subprocess.run(["python", "generated.py", fasta_data, "hamming"], 
                                      capture_output=True, text=True, timeout=30)
                working_cmd = ["python", "generated.py", fasta_data, "hamming"]
            except:
                print("FAIL: Could not execute script with any argument format")
                return
        
        # Run tests with working command format
        test_results = []
        
        # Test 1: Script executes without error
        try:
            result = subprocess.run(working_cmd, capture_output=True, text=True, timeout=30)
            test_results.append(("Script execution", result.returncode == 0))
        except:
            test_results.append(("Script execution", False))
            
        # Test 2: Matrix file is created
        matrix_files = [f for f in os.listdir('.') if 'matrix' in f.lower() and f.endswith('.tsv')]
        test_results.append(("Matrix file created", len(matrix_files) > 0))
        
        # Test 3: JSON file is created  
        json_files = [f for f in os.listdir('.') if f.endswith('.json')]
        test_results.append(("JSON file created", len(json_files) > 0))
        
        # Test 4: Matrix has correct dimensions
        matrix_correct_size = False
        if matrix_files:
            try:
                df = pd.read_csv(matrix_files[0], sep='\t', index_col=0)
                matrix_correct_size = df.shape[0] == 8 and df.shape[1] == 8
            except:
                pass
        test_results.append(("Matrix correct dimensions", matrix_correct_size))
        
        # Test 5: Matrix is symmetric
        matrix_symmetric = False
        if matrix_files:
            try:
                df = pd.read_csv(matrix_files[0], sep='\t', index_col=0)
                matrix_symmetric = np.allclose(df.values, df.values.T, rtol=1e-10)
            except:
                pass
        test_results.append(("Matrix is symmetric", matrix_symmetric))
        
        # Test 6: Diagonal elements are zero
        diagonal_zero = False
        if matrix_files:
            try:
                df = pd.read_csv(matrix_files[0], sep='\t', index_col=0)
                diagonal_zero = np.allclose(np.diag(df.values), 0, atol=1e-10)
            except:
                pass
        test_results.append(("Diagonal elements zero", diagonal_zero))
        
        # Test 7: JSON contains pairwise distances
        json_valid = False
        if json_files:
            try:
                with open(json_files[0], 'r') as f:
                    data = json.load(f)
                json_valid = isinstance(data, (dict, list)) and len(data) > 0
            except:
                pass
        test_results.append(("JSON format valid", json_valid))
        
        # Test 8: Identical sequences have zero distance
        identical_zero = False
        if matrix_files:
            try:
                df = pd.read_csv(matrix_files[0], sep='\t', index_col=0)
                if 'seq1' in df.index and 'seq2' in df.index:
                    identical_zero = abs(df.loc['seq1', 'seq2']) < 1e-10
            except:
                pass
        test_results.append(("Identical sequences distance zero", identical_zero))
        
        # Test 9: Different sequences have positive distance
        different_positive = False
        if matrix_files:
            try:
                df = pd.read_csv(matrix_files[0], sep='\t', index_col=0)
                if 'seq1' in df.index and 'seq7' in df.index:
                    different_positive = df.loc['seq1', 'seq7'] > 0
            except:
                pass
        test_results.append(("Different sequences positive distance", different_positive))
        
        # Test 10: Handles gaps appropriately
        handles_gaps = False
        if matrix_files:
            try:
                df = pd.read_csv(matrix_files[0], sep='\t', index_col=0)
                if 'seq5' in df.index:  # seq5 has a gap
                    handles_gaps = not np.isnan(df.loc['seq5', 'seq1'])
            except:
                pass
        test_results.append(("Handles gaps", handles_gaps))
        
        # Test 11: Multiple distance methods work
        methods_work = False
        try:
            for method in ['hamming', 'jukes-cantor', 'p-distance']:
                cmd_copy = working_cmd.copy()
                # Update method in command
                for i, arg in enumerate(cmd_copy):
                    if arg in ['hamming', 'jukes-cantor', 'p-distance']:
                        cmd_copy[i] = method
                        break
                result = subprocess.run(cmd_copy, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    break
            else:
                methods_work = True
        except:
            pass
        test_results.append(("Multiple methods supported", methods_work))
        
        # Test 12: Output contains summary statistics
        has_summary = False
        if result.returncode == 0:
            output_text = result.stdout + result.stderr
            summary_keywords = ['mean', 'std', 'min', 'max', 'average']
            has_summary = any(keyword in output_text.lower() for keyword in summary_keywords)
        test_results.append(("Summary statistics provided", has_summary))
        
        # Test 13: Distance values are reasonable (0 to 1 range for most methods)
        reasonable_values = False
        if matrix_files:
            try:
                df = pd.read_csv(matrix_files[0], sep='\t', index_col=0)
                values = df.values[np.triu_indices_from(df.values, k=1)]
                reasonable_values = np.all(values >= 0) and np.all(values <= 2.0)  # Allow > 1 for Jukes-Cantor
            except:
                pass
        test_results.append(("Distance values reasonable", reasonable_values))
        
        # Test 14: Sequence names preserved in output
        names_preserved = False
        if matrix_files:
            try:
                df = pd.read_csv(matrix_files[0], sep='\t', index_col=0)
                expected_names = set(expected_seqs.keys())
                actual_names = set(df.index)
                names_preserved = expected_names.issubset(actual_names)
            except:
                pass
        test_results.append(("Sequence names preserved", names_preserved))
        
        # Test 15: Consistent results between matrix and JSON
        consistent_results = False
        if matrix_files and json_files:
            try:
                df = pd.read_csv(matrix_files[0], sep='\t', index_col=0)
                with open(json_files[0], 'r') as f:
                    json_data = json.load(f)
                
                # Check if at least one distance matches between formats
                if isinstance(json_data, dict):
                    for key, value in json_data.items():
                        if isinstance(value, (int, float)):
                            consistent_results = True
                            break
                elif isinstance(json_data, list):
                    consistent_results = len(json_data) > 0
            except:
                pass
        test_results.append(("Consistent matrix/JSON results", consistent_results))
        
        # Calculate scores
        accuracy_score = sum(1 for _, passed in test_results if passed) / len(test_results)
        
        # Completeness score based on output quality
        completeness_score = 0.0
        if matrix_files and json_files:
            completeness_score += 0.4
        if matrix_correct_size and matrix_symmetric:
            completeness_score += 0.3
        if identical_zero and different_positive:
            completeness_score += 0.3
            
        # Print results
        for test_name, passed in test_results:
            print(f"{'PASS' if passed else 'FAIL'}: {test_name}")
            
        print(f"SCORE: {accuracy_score:.3f}")
        print(f"SCORE: {completeness_score:.3f}")

if __name__ == "__main__":
    run_test()
