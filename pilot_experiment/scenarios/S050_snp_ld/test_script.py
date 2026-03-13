import subprocess
import tempfile
import os
import pandas as pd
import numpy as np
import json
from pathlib import Path

def create_data(temp_dir):
    """Generate synthetic SNP genotype data"""
    np.random.seed(42)
    
    # Create 100 individuals, 20 SNPs across chromosome 1
    n_individuals = 100
    n_snps = 20
    
    # Generate SNP positions (chromosome 1, positions 1000000 to 2000000)
    positions = np.sort(np.random.choice(range(1000000, 2000000), n_snps, replace=False))
    
    # Create column headers with chr:position format
    snp_names = [f"1:{pos}" for pos in positions]
    
    # Generate genotype data with some LD structure
    genotypes = np.zeros((n_individuals, n_snps), dtype=int)
    
    # Create some SNPs in strong LD
    for i in range(n_individuals):
        # First generate independent SNPs
        for j in range(n_snps):
            genotypes[i, j] = np.random.choice([0, 1, 2], p=[0.5, 0.3, 0.2])
        
        # Create LD between some SNP pairs
        if np.random.random() < 0.7:  # 70% of individuals follow LD pattern
            # SNPs 0-2 in strong LD
            if genotypes[i, 0] == 2:
                genotypes[i, 1] = 2 if np.random.random() < 0.9 else genotypes[i, 1]
                genotypes[i, 2] = 2 if np.random.random() < 0.8 else genotypes[i, 2]
            
            # SNPs 5-7 in moderate LD
            if genotypes[i, 5] == 0:
                genotypes[i, 6] = 0 if np.random.random() < 0.7 else genotypes[i, 6]
                genotypes[i, 7] = 0 if np.random.random() < 0.6 else genotypes[i, 7]
    
    # Add some missing data (-1)
    missing_mask = np.random.random((n_individuals, n_snps)) < 0.05
    genotypes[missing_mask] = -1
    
    # Create DataFrame and save
    df = pd.DataFrame(genotypes, columns=snp_names)
    df.index.name = 'individual_id'
    
    input_file = os.path.join(temp_dir, 'genotypes.tsv')
    df.to_csv(input_file, sep='\t')
    
    return input_file, positions, snp_names

def test_script():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test data
        input_file, positions, snp_names = create_data(temp_dir)
        output_dir = os.path.join(temp_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Test with different possible argument names
        cmd_variants = [
            ['python', 'generated.py', '--input', input_file, '--output', output_dir, '--max-distance', '500000'],
            ['python', 'generated.py', '-i', input_file, '-o', output_dir, '--max_distance', '500000'],
            ['python', 'generated.py', '--genotypes', input_file, '--outdir', output_dir, '--distance', '500000']
        ]
        
        success = False
        for cmd in cmd_variants:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=temp_dir)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed with all argument variants")
            return
        
        print("PASS: Script executed successfully")
        
        # Check output files exist
        output_files = list(Path(output_dir).glob('*.tsv')) + list(Path(output_dir).glob('*.csv'))
        if len(output_files) >= 2:
            print("PASS: Multiple output files generated")
        else:
            print("FAIL: Expected at least 2 output files")
            return
        
        # Load and analyze results
        results_file = None
        summary_file = None
        
        for f in output_files:
            df = pd.read_csv(f, sep='\t' if f.suffix == '.tsv' else ',')
            if len(df.columns) >= 6:  # Comprehensive results file
                results_file = df
            elif len(df.columns) >= 4:  # Summary file
                summary_file = df
        
        if results_file is not None:
            print("PASS: Comprehensive results file found and loaded")
        else:
            print("FAIL: Could not identify comprehensive results file")
            return
        
        # Check required columns in results
        required_cols = ['snp1', 'snp2', 'r2', 'd_prime', 'lod']
        col_names = [col.lower().replace('_', '').replace('-', '') for col in results_file.columns]
        required_normalized = [col.lower().replace('_', '').replace('-', '') for col in required_cols]
        
        cols_found = sum(1 for req in required_normalized if any(req in col for col in col_names))
        if cols_found >= 4:
            print("PASS: Required LD statistics columns present")
        else:
            print("FAIL: Missing required LD statistics columns")
        
        # Check SNP pair format
        snp_cols = [col for col in results_file.columns if 'snp' in col.lower()]
        if len(snp_cols) >= 2:
            sample_snp = str(results_file[snp_cols[0]].iloc[0])
            if ':' in sample_snp:
                print("PASS: SNP identifiers follow chr:position format")
            else:
                print("FAIL: SNP identifiers don't follow expected format")
        else:
            print("FAIL: SNP pair columns not found")
        
        # Check distance filtering
        if len(results_file) > 0:
            # Extract positions and check distances
            try:
                snp1_pos = results_file[snp_cols[0]].apply(lambda x: int(str(x).split(':')[1]))
                snp2_pos = results_file[snp_cols[1]].apply(lambda x: int(str(x).split(':')[1]))
                distances = abs(snp1_pos - snp2_pos)
                if distances.max() <= 500000:
                    print("PASS: Distance filtering applied correctly")
                else:
                    print("FAIL: Some SNP pairs exceed maximum distance")
            except:
                print("FAIL: Could not verify distance filtering")
        else:
            print("FAIL: No SNP pairs in results")
        
        # Check for statistical values in reasonable ranges
        r2_col = None
        dprime_col = None
        lod_col = None
        
        for col in results_file.columns:
            col_lower = col.lower().replace('_', '').replace('-', '')
            if 'r2' in col_lower or 'rsquared' in col_lower:
                r2_col = col
            elif 'dprime' in col_lower or "d'" in col_lower:
                dprime_col = col
            elif 'lod' in col_lower:
                lod_col = col
        
        valid_ranges = 0
        if r2_col and results_file[r2_col].between(0, 1).all():
            valid_ranges += 1
        if dprime_col and results_file[dprime_col].between(-1, 1).all():
            valid_ranges += 1
        if lod_col and results_file[lod_col].min() >= -10:  # LOD can be negative
            valid_ranges += 1
        
        if valid_ranges >= 2:
            print("PASS: LD statistics in valid ranges")
        else:
            print("FAIL: LD statistics outside expected ranges")
        
        # Check for significant pairs identification
        if summary_file is not None:
            print("PASS: Summary file with significant pairs found")
            if len(summary_file) < len(results_file):
                print("PASS: Summary file contains fewer pairs (filtering applied)")
            else:
                print("FAIL: Summary file should contain filtered significant pairs")
        else:
            print("FAIL: Summary file not found")
        
        # Check haplotype frequency columns
        hap_cols = [col for col in (summary_file.columns if summary_file is not None else results_file.columns) 
                   if any(x in col.lower() for x in ['hap', 'freq', '00', '01', '10', '11'])]
        if len(hap_cols) >= 4:
            print("PASS: Haplotype frequency columns present")
        else:
            print("FAIL: Haplotype frequency columns missing")
        
        # Check that haplotype frequencies sum to ~1 for each pair
        if len(hap_cols) >= 4 and summary_file is not None:
            try:
                freq_cols = [col for col in hap_cols if any(x in col for x in ['00', '01', '10', '11'])][:4]
                if len(freq_cols) == 4:
                    freq_sums = summary_file[freq_cols].sum(axis=1)
                    if abs(freq_sums - 1.0).max() < 0.1:
                        print("PASS: Haplotype frequencies sum to approximately 1")
                    else:
                        print("FAIL: Haplotype frequencies don't sum to 1")
                else:
                    print("FAIL: Could not identify all 4 haplotype frequency columns")
            except:
                print("FAIL: Error validating haplotype frequencies")
        
        # Check missing data handling
        original_data = pd.read_csv(input_file, sep='\t', index_col=0)
        missing_count = (original_data == -1).sum().sum()
        if missing_count > 0:
            print("PASS: Test data contains missing values for handling verification")
        else:
            print("FAIL: Test data should contain missing values")
        
        # SCORE: Proportion of expected SNP pairs analyzed
        max_possible_pairs = len(snp_names) * (len(snp_names) - 1) // 2
        actual_pairs = len(results_file) if results_file is not None else 0
        pair_coverage = min(actual_pairs / max(max_possible_pairs * 0.3, 1), 1.0)  # Expect at least 30% due to distance filtering
        print(f"SCORE: {pair_coverage:.3f}")
        
        # SCORE: Quality of LD computation (based on statistical coherence)
        quality_score = 0.0
        if results_file is not None and len(results_file) > 0:
            quality_factors = 0
            total_factors = 0
            
            # Check r² values distribution
            if r2_col:
                r2_values = results_file[r2_col]
                if r2_values.var() > 0.01:  # Some variation in r² values
                    quality_factors += 1
                total_factors += 1
            
            # Check D' values distribution  
            if dprime_col:
                dprime_values = results_file[dprime_col]
                if dprime_values.var() > 0.01:  # Some variation in D' values
                    quality_factors += 1
                total_factors += 1
            
            # Check LOD score reasonableness
            if lod_col:
                lod_values = results_file[lod_col]
                if lod_values.std() > 0.5:  # Reasonable variation in LOD scores
                    quality_factors += 1
                total_factors += 1
            
            # Check filtering effectiveness
            if summary_file is not None and len(summary_file) > 0:
                filter_ratio = len(summary_file) / len(results_file)
                if 0.1 <= filter_ratio <= 0.8:  # Reasonable filtering
                    quality_factors += 1
                total_factors += 1
            
            quality_score = quality_factors / max(total_factors, 1)
        
        print(f"SCORE: {quality_score:.3f}")

if __name__ == "__main__":
    test_script()
