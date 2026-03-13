# Shannon diversity calculation
def calculate_shannon_diversity(abundances):
    total = sum(abundances)
    if total == 0:
        return 0
    
    shannon = 0
    for count in abundances:
        if count > 0:
            p = count / total
            shannon += p * math.log(p)
    
    return -shannon

# Simpson diversity calculation  
def calculate_simpson_diversity(abundances):
    total = sum(abundances)
    if total == 0:
        return 0
    
    simpson_d = 0
    for count in abundances:
        if count > 0:
            p = count / total
            simpson_d += p * p
    
    return 1 - simpson_d

# Data validation example
def validate_abundance_data(df):
    issues = []
    
    # Check for negative values
    negative_mask = df < 0
    if negative_mask.any().any():
        neg_locations = negative_mask.stack()
        neg_sites = neg_locations[neg_locations].index.get_level_values(0).unique()
        issues.append(f"Negative values found in sites: {list(neg_sites)}")
    
    return issues

# Safe summary statistics
if total_sites > 0 and 'shannon' in indices_to_calc:
    mean_shannon = results_df['shannon_diversity'].mean()
    most_diverse_idx = results_df['shannon_diversity'].idxmax()
    most_diverse_site = results_df.loc[most_diverse_idx, 'site_id']
