# Key Libraries for Biodiversity Analysis

## pandas
- `pd.read_csv(file, index_col=0)` - Load abundance matrix with site names as index
- `df.iterrows()` - Iterate through sites (rows) for index calculations
- `df.sum()` - Calculate total abundances per species or site
- `(df > 0).any(axis=0)` - Count species present across all sites

## numpy
- `np.sum(condition)` - Count species meeting criteria (richness calculation)
- `np.log(values)` - Natural logarithm for Shannon diversity
- `abundances[abundances > 0]` - Boolean indexing to filter zeros
- `np.sum(proportions * np.log(proportions))` - Vectorized Shannon calculation

## Ecological Formulas
- Shannon: H' = -Σ(pi * ln(pi)) where pi = ni/N
- Simpson: 1-D where D = Σ(pi²)  
- Pielou: J = H'/ln(S) where S = species richness
- Richness: S = count of species with abundance > 0
