# Reverse coding formula for 5-point Likert scale
df[f'{item}_r'] = 6 - df[item]

# Safe column reference checking
if item in reverse_items and f'{item}_r' in df.columns:
    use_column = f'{item}_r'
else:
    use_column = item

# Cronbach's alpha using correlation approach
corr_matrix = item_data.corr()
sum_correlations = corr_matrix.sum().sum() - k
avg_correlation = sum_correlations / (k * (k - 1))
alpha = (k * avg_correlation) / (1 + (k - 1) * avg_correlation)

# Command line usage
python script.py --input data.csv --output results/ --reverse-items "q2,q4,q6"
