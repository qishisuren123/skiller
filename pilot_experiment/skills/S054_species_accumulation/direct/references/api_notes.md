# NumPy Functions for Ecological Analysis
- np.random.lognormal(mean, sigma, size): Generate log-normal species abundance distributions
- np.random.permutation(n): Create random site orderings for accumulation curves
- np.percentile(data, [2.5, 97.5], axis=0): Calculate 95% confidence intervals
- np.sum(matrix, axis=0/1): Calculate species incidences or site richness

# SciPy Special Functions
- scipy.special.comb(n, k, exact=True): Exact combinatorial calculations for rarefaction
- Used in hypergeometric probability calculations for sample-based rarefaction

# Pandas for Data Export
- pd.DataFrame(matrix, index=sites, columns=species): Create labeled occurrence matrices
- df.to_csv(path): Export site-by-species data for external analysis

# Matplotlib Visualization
- plt.fill_between(x, y1, y2, alpha=0.3): Confidence interval bands
- plt.axhline(y=value, linestyle=':'): Horizontal asymptotic estimate lines
- plt.savefig(path, dpi=300, bbox_inches='tight'): High-quality plot export

# Key Ecological Formulas
- Chao2 = S_obs + (Q1²)/(2*Q2) where Q1=singletons, Q2=doubletons
- Sample-based rarefaction: E[S_m] = Σ(1 - P(species j absent from m sites))
- Hypergeometric probability for species absence in rarefaction calculations
