import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import subprocess
import tempfile
import os
import sys
from scipy import stats

def create_data():
    """Generate synthetic RNA-seq count data"""
    np.random.seed(42)
    
    # Create count matrix (1000 genes x 6 samples)
    n_genes, n_samples = 1000, 6
    gene_names = [f"Gene_{i:04d}" for i in range(n_genes)]
    sample_names = [f"Sample_{i+1}" for i in range(n_samples)]
    
    # Simulate different library sizes
    lib_sizes = np.array([1e6, 1.5e6, 0.8e6, 1.2e6, 0.9e6, 1.3e6])
    
    # Generate gene lengths (500 to 5000 bp)
    gene_lengths = np.random.randint(500, 5001, n_genes)
    
    # Generate counts with length bias and different expression levels
    base_expression = np.random.exponential(10, n_genes)
    length_bias = gene_lengths / 2000  # Longer genes tend to have more counts
    
    counts = np.zeros((n_genes, n_samples))
    for i, lib_size in enumerate(lib_sizes):
        # Add some sample-specific effects
        sample_effect = np.random.normal(1, 0.1, n_genes)
        expected_counts = base_expression * length_bias * sample_effect * (lib_size / 1e6)
        counts[:, i] = np.random.poisson(expected_counts)
    
    # Ensure some genes have zero counts
    zero_mask = np.random.random((n_genes, n_samples)) < 0.05
    counts[zero_mask] = 0
    
    count_df = pd.DataFrame(counts.astype(int), index=gene_names, columns=sample_names)
    length_df = pd.DataFrame({'gene_length': gene_lengths}, index=gene_names)
    
    return count_df, length_df

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        count_df, length_df = create_data()
        
        # Save input files
        count_df.to_csv('counts.csv')
        length_df.to_csv('gene_lengths.csv')
        
        # Test different argument name variations
        cmd_variations = [
            ['python', 'generated.py', '--counts', 'counts.csv', '--lengths', 'gene_lengths.csv', '--output-dir', '.'],
            ['python', 'generated.py', '--count-matrix', 'counts.csv', '--gene-lengths', 'gene_lengths.csv', '--outdir', '.'],
            ['python', 'generated.py', '-c', 'counts.csv', '-l', 'gene_lengths.csv', '-o', '.']
        ]
        
        success = False
        for cmd in cmd_variations:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed with all argument variations")
            return
        
        # Test 1: Check if TPM output file exists
        tpm_files = [f for f in os.listdir('.') if 'tpm' in f.lower() and f.endswith('.csv')]
        if tpm_files:
            print("PASS: TPM output file created")
            tpm_file = tpm_files[0]
        else:
            print("FAIL: TPM output file not found")
            return
        
        # Test 2: Check if DESeq2-style output file exists
        deseq_files = [f for f in os.listdir('.') if any(x in f.lower() for x in ['deseq', 'size_factor', 'normalized']) and f.endswith('.csv')]
        if deseq_files:
            print("PASS: DESeq2-style output file created")
            deseq_file = deseq_files[0]
        else:
            print("FAIL: DESeq2-style output file not found")
            return
        
        # Test 3: Check if JSON summary exists
        json_files = [f for f in os.listdir('.') if f.endswith('.json')]
        if json_files:
            print("PASS: JSON summary file created")
            json_file = json_files[0]
        else:
            print("FAIL: JSON summary file not found")
            return
        
        # Test 4: Check if plot exists
        plot_files = [f for f in os.listdir('.') if f.endswith('.png')]
        if plot_files:
            print("PASS: Visualization plot created")
        else:
            print("FAIL: Visualization plot not found")
        
        # Load outputs for detailed testing
        try:
            tpm_df = pd.read_csv(tpm_file, index_col=0)
            deseq_df = pd.read_csv(deseq_file, index_col=0)
            with open(json_file, 'r') as f:
                summary = json.load(f)
        except Exception as e:
            print(f"FAIL: Error loading output files: {e}")
            return
        
        # Test 5: Check TPM matrix dimensions
        if tpm_df.shape == count_df.shape:
            print("PASS: TPM matrix has correct dimensions")
        else:
            print("FAIL: TPM matrix dimensions incorrect")
        
        # Test 6: Check DESeq2 matrix dimensions
        if deseq_df.shape == count_df.shape:
            print("PASS: DESeq2 matrix has correct dimensions")
        else:
            print("FAIL: DESeq2 matrix dimensions incorrect")
        
        # Test 7: Verify TPM values are reasonable (should sum to ~1M per sample)
        tpm_sums = tpm_df.sum(axis=0)
        if all(abs(s - 1e6) < 1e3 for s in tpm_sums):
            print("PASS: TPM values sum to approximately 1 million per sample")
        else:
            print("FAIL: TPM values do not sum correctly")
        
        # Test 8: Check for non-negative values in TPM
        if (tpm_df >= 0).all().all():
            print("PASS: All TPM values are non-negative")
        else:
            print("FAIL: Found negative TPM values")
        
        # Test 9: Check for non-negative values in DESeq2 output
        if (deseq_df >= 0).all().all():
            print("PASS: All DESeq2 normalized values are non-negative")
        else:
            print("FAIL: Found negative DESeq2 normalized values")
        
        # Test 10: Verify JSON contains required fields
        required_fields = ['library_sizes', 'size_factors']
        if all(field in summary for field in required_fields):
            print("PASS: JSON summary contains required fields")
        else:
            print("FAIL: JSON summary missing required fields")
        
        # Test 11: Check if size factors are reasonable (should be around 1)
        if 'size_factors' in summary:
            size_factors = summary['size_factors']
            if isinstance(size_factors, (list, dict)) and len(size_factors) == count_df.shape[1]:
                sf_values = list(size_factors.values()) if isinstance(size_factors, dict) else size_factors
                if all(0.1 < sf < 10 for sf in sf_values):
                    print("PASS: Size factors are in reasonable range")
                else:
                    print("FAIL: Size factors out of reasonable range")
            else:
                print("FAIL: Size factors format incorrect")
        else:
            print("FAIL: Size factors not found in summary")
        
        # Test 12: Verify TPM accounts for gene length
        # Longer genes should generally have lower TPM than raw counts (relative to shorter genes)
        long_genes = length_df[length_df['gene_length'] > 3000].index[:10]
        short_genes = length_df[length_df['gene_length'] < 1000].index[:10]
        
        if len(long_genes) > 0 and len(short_genes) > 0:
            raw_ratio = count_df.loc[long_genes].mean().mean() / count_df.loc[short_genes].mean().mean()
            tpm_ratio = tpm_df.loc[long_genes].mean().mean() / tpm_df.loc[short_genes].mean().mean()
            if tpm_ratio < raw_ratio:
                print("PASS: TPM normalization accounts for gene length bias")
            else:
                print("FAIL: TPM normalization does not properly account for gene length")
        else:
            print("PASS: TPM normalization accounts for gene length bias (insufficient test genes)")
        
        # Test 13: Check correlation preservation
        sample1_raw = count_df.iloc[:, 0]
        sample1_tpm = tpm_df.iloc[:, 0]
        # Remove zeros for correlation calculation
        mask = (sample1_raw > 0) & (sample1_tpm > 0)
        if mask.sum() > 10:
            correlation = stats.spearmanr(sample1_raw[mask], sample1_tpm[mask])[0]
            if correlation > 0.8:
                print("PASS: High correlation maintained between raw and normalized data")
            else:
                print("FAIL: Poor correlation between raw and normalized data")
        else:
            print("PASS: High correlation maintained between raw and normalized data (insufficient data)")
        
        # Test 14: Verify DESeq2 normalization reduces library size variation
        raw_lib_sizes = count_df.sum(axis=0)
        deseq_lib_sizes = deseq_df.sum(axis=0)
        raw_cv = raw_lib_sizes.std() / raw_lib_sizes.mean()
        deseq_cv = deseq_lib_sizes.std() / deseq_lib_sizes.mean()
        if deseq_cv < raw_cv:
            print("PASS: DESeq2 normalization reduces library size variation")
        else:
            print("FAIL: DESeq2 normalization does not reduce library size variation")
        
        # SCORE 1: TPM calculation accuracy
        # Calculate expected TPM for a subset and compare
        test_genes = count_df.index[:100]
        expected_tpm = []
        for col in count_df.columns:
            counts = count_df.loc[test_genes, col]
            lengths = length_df.loc[test_genes, 'gene_length']
            rpk = counts / lengths
            scaling_factor = rpk.sum() / 1e6
            expected_tpm.append(rpk / scaling_factor if scaling_factor > 0 else rpk * 0)
        
        expected_tpm_df = pd.DataFrame(expected_tpm).T
        expected_tpm_df.index = test_genes
        expected_tpm_df.columns = count_df.columns
        
        tpm_accuracy = 0.0
        if expected_tpm_df.shape == tpm_df.loc[test_genes].shape:
            # Calculate mean absolute percentage error
            mask = expected_tpm_df > 0
            if mask.sum().sum() > 0:
                mape = np.abs((expected_tpm_df[mask] - tpm_df.loc[test_genes][mask]) / expected_tpm_df[mask]).mean().mean()
                tpm_accuracy = max(0, 1 - mape)
        
        print(f"SCORE: TPM calculation accuracy: {tpm_accuracy:.3f}")
        
        # SCORE 2: Overall normalization quality
        # Based on multiple factors: correlation preservation, size factor reasonableness, output completeness
        quality_score = 0.0
        
        # Factor 1: Output completeness (0.3 weight)
        outputs_exist = len(tpm_files) > 0 and len(deseq_files) > 0 and len(json_files) > 0
        completeness_score = 1.0 if outputs_exist else 0.0
        
        # Factor 2: Size factor quality (0.3 weight)
        sf_score = 0.0
        if 'size_factors' in summary:
            sf_values = list(summary['size_factors'].values()) if isinstance(summary['size_factors'], dict) else summary['size_factors']
            if len(sf_values) == count_df.shape[1]:
                # Good size factors should be close to 1 and reduce variation
                sf_mean = np.mean(sf_values)
                sf_cv = np.std(sf_values) / sf_mean if sf_mean > 0 else 1
                sf_score = max(0, 1 - abs(sf_mean - 1) - sf_cv)
        
        # Factor 3: Correlation preservation (0.4 weight)
        corr_score = max(0, correlation) if 'correlation' in locals() and not np.isnan(correlation) else 0.5
        
        quality_score = 0.3 * completeness_score + 0.3 * sf_score + 0.4 * corr_score
        print(f"SCORE: Overall normalization quality: {quality_score:.3f}")

if __name__ == "__main__":
    run_test()
