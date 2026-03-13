import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import mannwhitneyu
import argparse
import sys

def load_methylation_data(filepath):
    """Load and validate beta-value methylation data"""
    try:
        data = pd.read_csv(filepath, index_col=0)
        
        # Validate beta-values are in [0,1] range
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        invalid_mask = (data[numeric_cols] < 0) | (data[numeric_cols] > 1)
        if invalid_mask.any().any():
            print(f"Warning: {invalid_mask.sum().sum()} invalid beta-values found, converting to NaN")
            data[numeric_cols] = data[numeric_cols].mask(invalid_mask)
        
        return data
    except Exception as e:
        print(f"Error loading methylation data: {e}")
        sys.exit(1)

def parse_genomic_coordinates(probe_names):
    """Extract chromosome and position from probe names (format: chrX:position)"""
    coordinates = []
    for probe in probe_names:
        try:
            if ':' in probe:
                chrom, pos = probe.split(':')
                chrom = chrom.replace('chr', '')  # Standardize chromosome naming
                coordinates.append((chrom, int(pos)))
            else:
                coordinates.append((None, None))
        except:
            coordinates.append((None, None))
    
    return coordinates

def filter_low_quality_probes(data, max_missing_rate=0.2):
    """Remove probes with high missing data rates"""
    missing_rates = data.isnull().sum(axis=1) / data.shape[1]
    valid_probes = missing_rates <= max_missing_rate
    
    print(f"Filtered {(~valid_probes).sum()} probes with >{max_missing_rate*100}% missing data")
    return data[valid_probes]

def calculate_differential_methylation(case_data, control_data):
    """Calculate differential methylation statistics between groups"""
    results = []
    
    for probe in case_data.index:
        case_values = case_data.loc[probe].dropna()
        control_values = control_data.loc[probe].dropna()
        
        if len(case_values) < 3 or len(control_values) < 3:
            results.append({
                'probe': probe,
                'delta_beta': np.nan,
                'pvalue': 1.0,
                'case_mean': np.nan,
                'control_mean': np.nan
            })
            continue
        
        # Use Mann-Whitney U test (non-parametric)
        try:
            statistic, pvalue = mannwhitneyu(case_values, control_values, alternative='two-sided')
            delta_beta = case_values.mean() - control_values.mean()
            
            results.append({
                'probe': probe,
                'delta_beta': delta_beta,
                'pvalue': pvalue,
                'case_mean': case_values.mean(),
                'control_mean': control_values.mean()
            })
        except Exception as e:
            results.append({
                'probe': probe,
                'delta_beta': np.nan,
                'pvalue': 1.0,
                'case_mean': case_values.mean(),
                'control_mean': control_values.mean()
            })
    
    return pd.DataFrame(results)

def apply_fdr_correction(pvalues):
    """Apply Benjamini-Hochberg FDR correction"""
    from scipy.stats import false_discovery_control
    valid_pvals = ~np.isnan(pvalues)
    corrected_pvals = np.full_like(pvalues, 1.0)
    corrected_pvals[valid_pvals] = false_discovery_control(pvalues[valid_pvals])
    return corrected_pvals

def detect_dmrs(stats_df, fdr_threshold=0.05, min_cpgs=3, max_gap=1000):
    """Identify contiguous differentially methylated regions"""
    # Parse coordinates and sort by genomic position
    coordinates = parse_genomic_coordinates(stats_df['probe'])
    stats_df['chromosome'] = [c[0] for c in coordinates]
    stats_df['position'] = [c[1] for c in coordinates]
    
    # Remove probes without valid coordinates
    valid_coords = stats_df['chromosome'].notna() & stats_df['position'].notna()
    stats_df = stats_df[valid_coords].copy()
    
    # Sort by chromosome and position
    stats_df['chrom_numeric'] = pd.to_numeric(stats_df['chromosome'], errors='coerce')
    stats_df = stats_df.sort_values(['chrom_numeric', 'position'], na_position='last')
    
    # Identify significant CpGs
    significant = stats_df['fdr_pvalue'] < fdr_threshold
    
    dmrs = []
    current_region = []
    
    for i, row in stats_df.iterrows():
        if significant.loc[i]:
            if (not current_region or 
                (row['chromosome'] == stats_df.loc[current_region[-1], 'chromosome'] and 
                 row['position'] - stats_df.loc[current_region[-1], 'position'] <= max_gap)):
                current_region.append(i)
            else:
                if len(current_region) >= min_cpgs:
                    dmrs.append(current_region)
                current_region = [i]
        else:
            if len(current_region) >= min_cpgs:
                dmrs.append(current_region)
            current_region = []
    
    # Don't forget the last region
    if len(current_region) >= min_cpgs:
        dmrs.append(current_region)
    
    return dmrs, stats_df

def summarize_dmrs(dmrs, stats_df):
    """Generate DMR summary statistics"""
    dmr_summary = []
    
    for i, region_indices in enumerate(dmrs):
        region_data = stats_df.loc[region_indices]
        
        dmr_info = {
            'dmr_id': f"DMR_{i+1}",
            'chromosome': region_data['chromosome'].iloc[0],
            'start': region_data['position'].min(),
            'end': region_data['position'].max(),
            'num_cpgs': len(region_indices),
            'mean_delta_beta': region_data['delta_beta'].mean(),
            'min_pvalue': region_data['fdr_pvalue'].min(),
            'direction': 'hyper' if region_data['delta_beta'].mean() > 0 else 'hypo'
        }
        dmr_summary.append(dmr_info)
    
    return pd.DataFrame(dmr_summary)

def main():
    parser = argparse.ArgumentParser(description='DNA Methylation DMR Detection')
    parser.add_argument('--data', required=True, help='Methylation beta-value CSV file')
    parser.add_argument('--case-samples', required=True, help='Comma-separated case sample names')
    parser.add_argument('--control-samples', required=True, help='Comma-separated control sample names')
    parser.add_argument('--output', default='dmr_results.csv', help='Output file for DMR results')
    parser.add_argument('--fdr-threshold', type=float, default=0.05, help='FDR threshold for significance')
    parser.add_argument('--min-cpgs', type=int, default=3, help='Minimum CpGs per DMR')
    parser.add_argument('--max-gap', type=int, default=1000, help='Maximum gap between CpGs in DMR')
    
    args = parser.parse_args()
    
    # Load data
    print("Loading methylation data...")
    data = load_methylation_data(args.data)
    
    # Parse sample groups
    case_samples = [s.strip() for s in args.case_samples.split(',')]
    control_samples = [s.strip() for s in args.control_samples.split(',')]
    
    # Validate sample names
    missing_case = set(case_samples) - set(data.columns)
    missing_control = set(control_samples) - set(data.columns)
    
    if missing_case:
        print(f"Error: Case samples not found: {missing_case}")
        sys.exit(1)
    if missing_control:
        print(f"Error: Control samples not found: {missing_control}")
        sys.exit(1)
    
    # Filter low-quality probes
    print("Filtering low-quality probes...")
    data = filter_low_quality_probes(data)
    
    # Calculate differential methylation
    print("Calculating differential methylation statistics...")
    case_data = data[case_samples]
    control_data = data[control_samples]
    stats_df = calculate_differential_methylation(case_data, control_data)
    
    # Apply FDR correction
    print("Applying FDR correction...")
    stats_df['fdr_pvalue'] = apply_fdr_correction(stats_df['pvalue'].values)
    
    # Detect DMRs
    print("Detecting differentially methylated regions...")
    dmrs, stats_df = detect_dmrs(stats_df, args.fdr_threshold, args.min_cpgs, args.max_gap)
    
    # Summarize results
    dmr_summary = summarize_dmrs(dmrs, stats_df)
    
    print(f"Found {len(dmrs)} DMRs")
    print(f"Hypermethylated DMRs: {(dmr_summary['direction'] == 'hyper').sum()}")
    print(f"Hypomethylated DMRs: {(dmr_summary['direction'] == 'hypo').sum()}")
    
    # Save results
    dmr_summary.to_csv(args.output, index=False)
    stats_df.to_csv(args.output.replace('.csv', '_detailed_stats.csv'))
    
    print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
