import os
import sys
import tempfile
import subprocess
import pandas as pd
import numpy as np
import json
from scipy import stats

def create_data():
    """Generate synthetic methylation data"""
    np.random.seed(42)
    
    # Create CpG annotation data
    n_cpgs = 1000
    chromosomes = np.random.choice(['chr1', 'chr2', 'chr3'], n_cpgs, p=[0.5, 0.3, 0.2])
    
    # Generate positions clustered to create potential DMRs
    positions = []
    for chrom in ['chr1', 'chr2', 'chr3']:
        chrom_cpgs = np.sum(chromosomes == chrom)
        if chrom_cpgs > 0:
            # Create clusters of CpGs
            n_clusters = max(1, chrom_cpgs // 20)
            cluster_starts = np.random.randint(1000000, 50000000, n_clusters)
            cluster_positions = []
            
            remaining_cpgs = chrom_cpgs
            for i, start in enumerate(cluster_starts):
                if i == len(cluster_starts) - 1:
                    cluster_size = remaining_cpgs
                else:
                    cluster_size = min(remaining_cpgs, np.random.poisson(chrom_cpgs // n_clusters))
                
                if cluster_size > 0:
                    pos = start + np.sort(np.random.randint(0, 5000, cluster_size))
                    cluster_positions.extend(pos)
                    remaining_cpgs -= cluster_size
                
                if remaining_cpgs <= 0:
                    break
            
            positions.extend(cluster_positions[:chrom_cpgs])
    
    positions = np.array(positions)
    
    # Create CpG IDs
    cpg_ids = [f"cg{i:08d}" for i in range(n_cpgs)]
    
    annotation_df = pd.DataFrame({
        'CpG_ID': cpg_ids,
        'chromosome': chromosomes,
        'position': positions
    })
    
    # Create beta-value matrix
    samples = [f"Sample_{i:03d}" for i in range(20)]
    case_samples = samples[:10]
    control_samples = samples[10:]
    
    # Generate beta values with some DMRs
    beta_matrix = np.random.beta(2, 2, (n_cpgs, len(samples)))
    
    # Introduce differential methylation in specific regions
    dmr_regions = []
    for chrom in ['chr1', 'chr2']:
        chrom_mask = chromosomes == chrom
        chrom_indices = np.where(chrom_mask)[0]
        if len(chrom_indices) > 10:
            # Create a DMR
            start_idx = np.random.choice(chrom_indices[:-10])
            end_idx = min(start_idx + np.random.randint(5, 15), len(chrom_indices))
            dmr_cpgs = chrom_indices[
                (chrom_indices >= start_idx) & (chrom_indices < end_idx)
            ][:10]  # Limit to 10 CpGs
            
            if len(dmr_cpgs) >= 3:
                # Add differential methylation
                delta = np.random.choice([-0.3, 0.3])
                for cpg_idx in dmr_cpgs:
                    if delta > 0:  # Hypermethylated in cases
                        beta_matrix[cpg_idx, :10] += delta
                    else:  # Hypomethylated in cases
                        beta_matrix[cpg_idx, :10] += delta
                
                dmr_regions.append({
                    'chromosome': chrom,
                    'cpgs': dmr_cpgs,
                    'delta': delta
                })
    
    # Clip beta values to [0, 1]
    beta_matrix = np.clip(beta_matrix, 0, 1)
    
    # Add some missing values
    missing_mask = np.random.random((n_cpgs, len(samples))) < 0.02
    beta_matrix[missing_mask] = np.nan
    
    # Create beta matrix DataFrame
    beta_df = pd.DataFrame(beta_matrix, index=cpg_ids, columns=samples)
    
    return annotation_df, beta_df, case_samples, control_samples, dmr_regions

def test_script():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        annotation_df, beta_df, case_samples, control_samples, true_dmrs = create_data()
        
        # Save input files
        annotation_df.to_csv('annotation.csv', index=False)
        beta_df.to_csv('beta_matrix.csv', index=True)
        
        # Prepare arguments
        case_str = ','.join(case_samples)
        control_str = ','.join(control_samples)
        
        # Run the script
        cmd = [
            sys.executable, '../generated.py',
            '--input', 'beta_matrix.csv',
            '--annotation', 'annotation.csv',
            '--output', 'test_output',
            '--case-samples', case_str,
            '--control-samples', control_str,
            '--min-cpgs', '3',
            '--delta-beta', '0.2',
            '--p-threshold', '0.05'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"FAIL: Script failed with return code {result.returncode}")
                print(f"STDERR: {result.stderr}")
                return
        except subprocess.TimeoutExpired:
            print("FAIL: Script timed out")
            return
        except Exception as e:
            print(f"FAIL: Error running script: {e}")
            return
        
        # Test outputs exist
        required_files = [
            'test_output_cpg_stats.csv',
            'test_output_dmrs.csv',
            'test_output_summary.json'
        ]
        
        for file in required_files:
            if os.path.exists(file):
                print(f"PASS: {file} exists")
            else:
                print(f"FAIL: {file} missing")
                return
        
        try:
            # Load and validate outputs
            cpg_stats = pd.read_csv('test_output_cpg_stats.csv')
            dmrs = pd.read_csv('test_output_dmrs.csv')
            
            with open('test_output_summary.json', 'r') as f:
                summary = json.load(f)
            
            # Test CpG stats structure
            required_cpg_cols = ['CpG_ID', 'chromosome', 'position', 'case_mean', 'control_mean', 'delta_beta', 'p_value']
            missing_cols = [col for col in required_cpg_cols if col not in cpg_stats.columns]
            if not missing_cols:
                print("PASS: CpG stats has required columns")
            else:
                print(f"FAIL: CpG stats missing columns: {missing_cols}")
            
            # Test CpG stats data validity
            if len(cpg_stats) == len(beta_df):
                print("PASS: CpG stats has correct number of rows")
            else:
                print(f"FAIL: CpG stats has {len(cpg_stats)} rows, expected {len(beta_df)}")
            
            # Test beta value ranges
            if (cpg_stats['case_mean'].between(0, 1).all() and 
                cpg_stats['control_mean'].between(0, 1).all()):
                print("PASS: Beta values in valid range [0,1]")
            else:
                print("FAIL: Beta values outside valid range")
            
            # Test delta beta calculation
            calculated_delta = cpg_stats['case_mean'] - cpg_stats['control_mean']
            if np.allclose(calculated_delta, cpg_stats['delta_beta'], rtol=1e-10, equal_nan=True):
                print("PASS: Delta beta correctly calculated")
            else:
                print("FAIL: Delta beta calculation incorrect")
            
            # Test p-values
            if cpg_stats['p_value'].between(0, 1).all():
                print("PASS: P-values in valid range [0,1]")
            else:
                print("FAIL: P-values outside valid range")
            
            # Test DMR structure
            if len(dmrs) > 0:
                required_dmr_cols = ['chromosome', 'start', 'end', 'n_cpgs', 'mean_delta_beta', 'min_p_value']
                missing_dmr_cols = [col for col in required_dmr_cols if col not in dmrs.columns]
                if not missing_dmr_cols:
                    print("PASS: DMR output has required columns")
                else:
                    print(f"FAIL: DMR output missing columns: {missing_dmr_cols}")
                
                # Test DMR constraints
                if (dmrs['n_cpgs'] >= 3).all():
                    print("PASS: All DMRs meet minimum CpG requirement")
                else:
                    print("FAIL: Some DMRs have fewer than 3 CpGs")
                
                if (dmrs['mean_delta_beta'].abs() >= 0.2).all():
                    print("PASS: All DMRs meet delta-beta threshold")
                else:
                    print("FAIL: Some DMRs below delta-beta threshold")
                
                if (dmrs['min_p_value'] <= 0.05).all():
                    print("PASS: All DMRs meet p-value threshold")
                else:
                    print("FAIL: Some DMRs above p-value threshold")
            else:
                print("PASS: No DMRs found (acceptable)")
            
            # Test summary structure
            required_summary_keys = ['total_dmrs', 'parameters']
            missing_summary_keys = [key for key in required_summary_keys if key not in summary]
            if not missing_summary_keys:
                print("PASS: Summary has required keys")
            else:
                print(f"FAIL: Summary missing keys: {missing_summary_keys}")
            
            # Test summary consistency
            if summary['total_dmrs'] == len(dmrs):
                print("PASS: Summary DMR count matches output")
            else:
                print("FAIL: Summary DMR count inconsistent")
            
            # Test genomic coordinates
            if (dmrs['start'] <= dmrs['end']).all() if len(dmrs) > 0 else True:
                print("PASS: DMR coordinates are valid")
            else:
                print("FAIL: Invalid DMR coordinates")
            
            # Calculate scores
            # Score 1: Statistical analysis accuracy
            valid_stats = (
                cpg_stats['case_mean'].between(0, 1).all() and
                cpg_stats['control_mean'].between(0, 1).all() and
                cpg_stats['p_value'].between(0, 1).all() and
                np.allclose(calculated_delta, cpg_stats['delta_beta'], rtol=1e-10, equal_nan=True)
            )
            stats_score = 1.0 if valid_stats else 0.0
            print(f"SCORE: Statistical analysis accuracy: {stats_score:.3f}")
            
            # Score 2: DMR detection quality
            dmr_quality_score = 0.0
            if len(dmrs) > 0:
                quality_checks = [
                    (dmrs['n_cpgs'] >= 3).all(),
                    (dmrs['mean_delta_beta'].abs() >= 0.2).all(),
                    (dmrs['min_p_value'] <= 0.05).all(),
                    (dmrs['start'] <= dmrs['end']).all(),
                    len(dmrs) <= 50  # Reasonable number of DMRs
                ]
                dmr_quality_score = sum(quality_checks) / len(quality_checks)
            else:
                dmr_quality_score = 0.5  # Neutral score for no DMRs
            
            print(f"SCORE: DMR detection quality: {dmr_quality_score:.3f}")
            
        except Exception as e:
            print(f"FAIL: Error validating outputs: {e}")

if __name__ == "__main__":
    test_script()
