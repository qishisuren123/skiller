# Key Libraries for DNA Methylation Analysis

## pandas
- `pd.read_csv()`: Load methylation data matrices
- `DataFrame.isnull()`: Detect missing beta-values
- `DataFrame.sort_values()`: Sort by genomic coordinates
- `DataFrame.groupby()`: Group CpGs by chromosome

## scipy.stats
- `mannwhitneyu()`: Non-parametric test for differential methylation
- `false_discovery_control()`: Benjamini-Hochberg FDR correction
- `ttest_ind()`: Alternative parametric test for normal data

## numpy
- `np.isnan()`: Handle missing values in statistical calculations
- `np.full_like()`: Initialize arrays for corrected p-values
- `np.logspace()`: Generate thresholds for sensitivity analysis

## Key Parameters
- Beta-values: Range [0,1], 0=unmethylated, 1=fully methylated
- Missing data threshold: Typically 20% maximum per probe
- DMR criteria: Minimum 3 CpGs, maximum 1kb gap
- FDR threshold: 0.05 for genome-wide significance
