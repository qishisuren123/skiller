import subprocess
import json
import tempfile
import os
import sys
from pathlib import Path

def create_data():
    """Generate synthetic DNA sequences for primer design testing"""
    sequences = {
        "seq1_high_gc": "ATGCGCGCGCGCATGCATGCATGCGCGCGCGCATGCATGC",  # High GC content
        "seq2_low_gc": "ATATATATATATATATATATATATATATATATATATATAT",    # Low GC content  
        "seq3_balanced": "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC",   # Balanced GC
        "seq4_long": "ATGCGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACG",
        "seq5_short": "ATGCGTACGTACGTACG"
    }
    return sequences

def calculate_tm(primer):
    """Calculate melting temperature using basic formula"""
    a_count = primer.upper().count('A')
    t_count = primer.upper().count('T') 
    g_count = primer.upper().count('G')
    c_count = primer.upper().count('C')
    return 2 * (a_count + t_count) + 4 * (g_count + c_count)

def calculate_gc_content(primer):
    """Calculate GC content percentage"""
    g_count = primer.upper().count('G')
    c_count = primer.upper().count('C')
    return (g_count + c_count) / len(primer) * 100

def run_test():
    sequences = create_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create input sequences string
        seq_input = ",".join([f">{name}\n{seq}" for name, seq in sequences.items()])
        
        # Test basic functionality
        result = subprocess.run([
            sys.executable, "generated.py",
            "--sequences", seq_input,
            "--output", "primers.json",
            "--min-length", "18",
            "--max-length", "25", 
            "--target-tm", "60",
            "--tm-tolerance", "5",
            "--min-gc", "40",
            "--max-gc", "60"
        ], capture_output=True, text=True)
        
        print("PASS" if result.returncode == 0 else "FAIL", "- Script runs without errors")
        
        # Check output file exists
        output_exists = os.path.exists("primers.json")
        print("PASS" if output_exists else "FAIL", "- Output JSON file created")
        
        if not output_exists:
            print("SCORE: 0.0")
            print("SCORE: 0.0") 
            return
            
        # Load and validate JSON output
        try:
            with open("primers.json", 'r') as f:
                results = json.load(f)
            json_valid = True
        except:
            json_valid = False
            results = {}
            
        print("PASS" if json_valid else "FAIL", "- Valid JSON output format")
        
        # Check if results contain expected sequences
        expected_seqs = set(sequences.keys())
        result_seqs = set(results.keys()) if isinstance(results, dict) else set()
        has_all_seqs = expected_seqs.issubset(result_seqs)
        print("PASS" if has_all_seqs else "FAIL", "- All input sequences processed")
        
        valid_primers = 0
        total_sequences = len(sequences)
        tm_accuracy_sum = 0
        tm_count = 0
        
        for seq_name, seq_data in results.items():
            if seq_name in sequences:
                # Check primer exists
                has_primer = 'primer' in seq_data
                print("PASS" if has_primer else "FAIL", f"- Primer found for {seq_name}")
                
                if has_primer:
                    primer = seq_data['primer']
                    
                    # Check primer length
                    length_valid = 18 <= len(primer) <= 25
                    print("PASS" if length_valid else "FAIL", f"- Primer length valid for {seq_name}")
                    
                    # Check primer is from sequence start
                    original_seq = sequences[seq_name]
                    from_start = original_seq.upper().startswith(primer.upper())
                    print("PASS" if from_start else "FAIL", f"- Primer from sequence start for {seq_name}")
                    
                    # Check Tm calculation
                    if 'tm' in seq_data:
                        calculated_tm = calculate_tm(primer)
                        reported_tm = seq_data['tm']
                        tm_correct = abs(calculated_tm - reported_tm) < 0.1
                        print("PASS" if tm_correct else "FAIL", f"- Tm calculation correct for {seq_name}")
                        
                        # Check Tm within tolerance
                        tm_in_range = abs(reported_tm - 60) <= 5
                        print("PASS" if tm_in_range else "FAIL", f"- Tm within tolerance for {seq_name}")
                        
                        tm_accuracy_sum += max(0, 1 - abs(reported_tm - 60) / 60)
                        tm_count += 1
                    
                    # Check GC content
                    if 'gc_content' in seq_data:
                        calculated_gc = calculate_gc_content(primer)
                        reported_gc = seq_data['gc_content']
                        gc_correct = abs(calculated_gc - reported_gc) < 0.1
                        print("PASS" if gc_correct else "FAIL", f"- GC content calculation correct for {seq_name}")
                        
                        # Check GC within range
                        gc_in_range = 40 <= reported_gc <= 60
                        print("PASS" if gc_in_range else "FAIL", f"- GC content within range for {seq_name}")
                        
                        if length_valid and tm_correct and gc_correct:
                            valid_primers += 1
        
        # Test with different parameters
        result2 = subprocess.run([
            sys.executable, "generated.py", 
            "--sequences", seq_input,
            "--output", "primers2.json",
            "--min-length", "20",
            "--max-length", "22",
            "--target-tm", "55"
        ], capture_output=True, text=True)
        
        print("PASS" if result2.returncode == 0 else "FAIL", "- Script works with different parameters")
        
        # Check invalid sequence handling
        invalid_seq = ">invalid\nATGCXYZ"
        result3 = subprocess.run([
            sys.executable, "generated.py",
            "--sequences", invalid_seq, 
            "--output", "primers3.json"
        ], capture_output=True, text=True)
        
        handles_invalid = result3.returncode != 0 or "error" in result3.stderr.lower()
        print("PASS" if handles_invalid else "FAIL", "- Handles invalid sequences appropriately")
        
        # Calculate scores
        primer_success_rate = valid_primers / total_sequences if total_sequences > 0 else 0
        tm_accuracy = tm_accuracy_sum / tm_count if tm_count > 0 else 0
        
        print(f"SCORE: {primer_success_rate:.3f}")
        print(f"SCORE: {tm_accuracy:.3f}")

if __name__ == "__main__":
    run_test()
