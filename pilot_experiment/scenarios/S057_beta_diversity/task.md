# Beta Diversity Analysis Tool

Create a command-line tool that computes beta diversity metrics between ecological sampling sites. Beta diversity measures the variation in species composition between different sites or communities.

Your script should accept species abundance data for multiple sampling sites and calculate various beta diversity indices that quantify how different the communities are from each other.

## Requirements

1. **Data Input**: Accept species abundance data via command-line arguments, where each site is represented by a list of species abundances (counts or relative abundances).

2. **Bray-Curtis Dissimilarity**: Calculate the Bray-Curtis dissimilarity matrix between all pairs of sites. This metric ranges from 0 (identical communities) to 1 (completely different communities).

3. **Jaccard Index**: Compute the Jaccard dissimilarity matrix based on species presence/absence data (convert abundance data to binary). Calculate both the similarity and dissimilarity versions.

4. **Sorensen Index**: Calculate the Sorensen dissimilarity coefficient between all site pairs, which emphasizes shared species.

5. **Output Generation**: Save results to a JSON file containing all dissimilarity matrices and summary statistics (mean, standard deviation, min, max for each metric).

6. **Visualization**: Generate a heatmap visualization showing the Bray-Curtis dissimilarity matrix and save it as a PNG file.

## Command Line Interface
