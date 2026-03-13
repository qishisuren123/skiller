# NumPy Functions for Phylogenetic Distance Calculations

## Core Array Operations
- `np.zeros((n, n))` - Create symmetric distance matrix
- `np.triu_indices_from(matrix, k=1)` - Extract upper triangle indices (excluding diagonal)
- `np.isnan(array)` - Check for NaN values in distance calculations
- `np.log(x)` - Natural logarithm for Jukes-Cantor correction

## Statistical Functions
- `np.mean(array)` - Calculate mean distance
- `np.std(array)` - Calculate standard deviation
- `np.min(array)` - Find minimum distance
- `np.max(array)` - Find maximum distance

## Key Parameters
- `k=1` in triu_indices_from excludes diagonal (self-comparisons)
- Use `float('nan')` for undefined distances when no valid nucleotide pairs exist
- Matrix indexing: `matrix[i, j]` for accessing distance between sequences i and j

## JSON Module
- `json.dump(data, file, indent=2)` - Save pairwise distances with formatting
- Structure pairwise data as list of dictionaries with sequence1, sequence2, distance keys
