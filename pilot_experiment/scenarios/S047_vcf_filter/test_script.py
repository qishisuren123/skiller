import subprocess
import tempfile
import os
import json
import pandas as pd
import numpy as np

def create_data():
    """Generate synthetic VCF-like variant data"""
    np.random.seed(42)
    
    # Generate 200 variants across different chromosomes
    n_variants = 200
    
    chroms = np.random.choice(['chr1', 'chr2', 'chr3', 'chr4', 'chr5'], n_variants)
    positions = np.random.randint(1000000, 50000000, n_variants)
    refs = np.random.choice(['A', 'T', 'G', 'C'], n_variants)
    alts = np.random.choice(['A', 'T', 'G', 'C'], n_variants)
    
    # Quality scores with some low quality variants
    quals = np.concatenate([
        np.random.normal(45, 15, n_variants//2),  # Good quality
        np.random.normal(20, 10, n_variants//2)   # Poor quality
    ])
    quals = np.clip(quals, 0, 99)
    
    # Depth values
    depths = np.random.poisson(25, n_variants)
    depths = np.clip(depths, 1, 100)
    
    # Allele frequencies
    afs = np.random.beta(2, 8, n_variants)  # Skewed toward lower frequencies
    
    # Genotypes
    genotypes = np.random.choice(['0/0', '0/1', '1/1', '0/2', '1/2'], n_variants, 
                                p=[0.3, 0.4, 0.2, 0.05, 0.05])
    
    # Add some missing values
    missing_indices = np.random.choice(n_variants, n_variants//20, replace=False)
    quals_str = quals.astype(str)
    depths_str = depths.astype(str)
    afs_str = afs.astype(str)
    
    for idx in missing_indices[:len(missing_indices)//3]:
        quals_str[idx] = '.'
    for idx in missing_indices[len(missing_indices)//3:2*len(missing_indices)//3]:
        depths_str[idx] = '.'
    for idx in missing_indices[2*len(missing_indices)//3:]:
        afs_str[idx] = '.'
    
    # Create DataFrame
    data = pd.DataFrame({
        'CHROM': chroms,
        'POS': positions,
        'REF': refs,
        'ALT': alts,
        'QUAL': quals_str,
        'DP': depths_str,
        'AF': afs_str,
        'GT': genotypes
    })
    
    return data

def test_vcf_filter():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test data
        test_data = create_data()
        input_file = os.path.join(tmpdir, 'variants.tsv')
        test_data.to_csv(input_file, sep='\t', index=False)
        
        output_prefix = os.path.join(tmpdir, 'filtered')
        
        # Test 1: Basic filtering with default parameters
        result = subprocess.run([
            'python', 'generated.py',
            '--input', input_file,
            '--output', output_prefix,
        ], capture_output=True, text=True, cwd='.')
        
        print("PASS" if result.returncode == 0 else "FAIL", "- Script runs without errors")
        
        # Check output files exist
        filtered_file = f"{output_prefix}_filtered.tsv"
        rejected_file = f"{output_prefix}_rejected.tsv"
        summary_file = f"{output_prefix}_summary.json"
        
        print("PASS" if os.path.exists(filtered_file) else "FAIL", "- Filtered output file created")
        print("PASS" if os.path.exists(rejected_file) else "FAIL", "- Rejected output file created")
        print("PASS" if os.path.exists(summary_file) else "FAIL", "- Summary JSON file created")
        
        if os.path.exists(filtered_file) and os.path.exists(rejected_file):
            filtered_df = pd.read_csv(filtered_file, sep='\t')
            rejected_df = pd.read_csv(rejected_file, sep='\t')
            
            # Test 2: Check required columns exist
            required_cols = ['CHROM', 'POS', 'REF', 'ALT', 'QUAL', 'DP', 'AF', 'GT', 
                           'FILTER_STATUS', 'QUAL_CATEGORY', 'HET_HOM']
            has_all_cols = all(col in filtered_df.columns for col in required_cols)
            print("PASS" if has_all_cols else "FAIL", "- All required columns present in filtered output")
            
            # Test 3: Filter status annotation
            if 'FILTER_STATUS' in filtered_df.columns:
                all_pass = all(filtered_df['FILTER_STATUS'] == 'PASS')
                print("PASS" if all_pass else "FAIL", "- All filtered variants marked as PASS")
            
            if 'FILTER_STATUS' in rejected_df.columns:
                all_fail = all(rejected_df['FILTER_STATUS'] == 'FAIL')
                print("PASS" if all_fail else "FAIL", "- All rejected variants marked as FAIL")
            
            # Test 4: Quality filtering logic
            if len(filtered_df) > 0:
                try:
                    filtered_df['QUAL_num'] = pd.to_numeric(filtered_df['QUAL'])
                    filtered_df['DP_num'] = pd.to_numeric(filtered_df['DP'])
                    filtered_df['AF_num'] = pd.to_numeric(filtered_df['AF'])
                    
                    qual_ok = all(filtered_df['QUAL_num'] >= 30)
                    depth_ok = all(filtered_df['DP_num'] >= 10)
                    af_ok = all(filtered_df['AF_num'] >= 0.05)
                    
                    print("PASS" if qual_ok else "FAIL", "- Quality threshold applied correctly")
                    print("PASS" if depth_ok else "FAIL", "- Depth threshold applied correctly")
                    print("PASS" if af_ok else "FAIL", "- Allele frequency threshold applied correctly")
                except:
                    print("FAIL - Error checking numeric thresholds")
            
            # Test 5: Quality categories
            if 'QUAL_CATEGORY' in filtered_df.columns and len(filtered_df) > 0:
                try:
                    high_qual = filtered_df[filtered_df['QUAL_num'] >= 50]['QUAL_CATEGORY']
                    medium_qual = filtered_df[(filtered_df['QUAL_num'] >= 30) & (filtered_df['QUAL_num'] < 50)]['QUAL_CATEGORY']
                    
                    high_correct = all(high_qual == 'HIGH') if len(high_qual) > 0 else True
                    medium_correct = all(medium_qual == 'MEDIUM') if len(medium_qual) > 0 else True
                    
                    print("PASS" if high_correct and medium_correct else "FAIL", "- Quality categories assigned correctly")
                except:
                    print("FAIL - Error checking quality categories")
            
            # Test 6: Genotype annotation
            if 'HET_HOM' in filtered_df.columns and len(filtered_df) > 0:
                het_mask = filtered_df['GT'].str.contains('0/1|1/0|0/2|2/0|1/2|2/1', na=False)
                het_correct = all(filtered_df.loc[het_mask, 'HET_HOM'] == 'HET') if het_mask.any() else True
                
                hom_mask = filtered_df['GT'].str.match(r'\d/\d') & ~het_mask
                hom_correct = all(filtered_df.loc[hom_mask, 'HET_HOM'] == 'HOM') if hom_mask.any() else True
                
                print("PASS" if het_correct and hom_correct else "FAIL", "- Genotype categories assigned correctly")
        
        # Test 7: Summary JSON structure
        if os.path.exists(summary_file):
            try:
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                
                required_keys = ['total_variants', 'passed_variants', 'failed_variants', 'mean_quality_passed']
                has_required_keys = all(key in summary for key in required_keys)
                print("PASS" if has_required_keys else "FAIL", "- Summary JSON has required keys")
                
                # Check if counts add up
                total_check = summary['total_variants'] == summary['passed_variants'] + summary['failed_variants']
                print("PASS" if total_check else "FAIL", "- Summary counts are consistent")
            except:
                print("FAIL - Error reading summary JSON")
        
        # Test 8: Custom thresholds
        result2 = subprocess.run([
            'python', 'generated.py',
            '--input', input_file,
            '--output', output_prefix + '2',
            '--min-qual', '50',
            '--min-depth', '20',
            '--min-af', '0.1'
        ], capture_output=True, text=True, cwd='.')
        
        print("PASS" if result2.returncode == 0 else "FAIL", "- Custom thresholds accepted")
        
        # Test 9: Chromosome filtering
        result3 = subprocess.run([
            'python', 'generated.py',
            '--input', input_file,
            '--output', output_prefix + '3',
            '--chr', 'chr1'
        ], capture_output=True, text=True, cwd='.')
        
        print("PASS" if result3.returncode == 0 else "FAIL", "- Chromosome filtering works")
        
        if os.path.exists(f"{output_prefix}3_filtered.tsv"):
            chr_filtered = pd.read_csv(f"{output_prefix}3_filtered.tsv", sep='\t')
            if len(chr_filtered) > 0:
                chr_correct = all(chr_filtered['CHROM'] == 'chr1')
                print("PASS" if chr_correct else "FAIL", "- Chromosome filtering applied correctly")
        
        # Calculate scores
        total_files = 3  # filtered, rejected, summary
        files_created = sum([os.path.exists(f"{output_prefix}_{suffix}") 
                           for suffix in ['filtered.tsv', 'rejected.tsv', 'summary.json']])
        file_score = files_created / total_files
        
        # Annotation completeness score
        annotation_score = 0.0
        if os.path.exists(filtered_file):
            try:
                df = pd.read_csv(filtered_file, sep='\t')
                expected_cols = ['FILTER_STATUS', 'QUAL_CATEGORY', 'HET_HOM']
                present_cols = sum([col in df.columns for col in expected_cols])
                annotation_score = present_cols / len(expected_cols)
            except:
                pass
        
        print(f"SCORE: {file_score:.3f} (file creation completeness)")
        print(f"SCORE: {annotation_score:.3f} (annotation completeness)")

if __name__ == "__main__":
    test_vcf_filter()
