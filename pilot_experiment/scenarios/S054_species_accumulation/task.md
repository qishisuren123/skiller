# Species Accumulation Curve Analysis

Create a CLI script that computes and analyzes species accumulation curves from ecological sampling data. Species accumulation curves show how the cumulative number of unique species increases as more sampling sites are surveyed, which is fundamental for understanding biodiversity patterns and planning sampling efforts.

Your script should generate synthetic sampling data representing multiple sites where different species were observed, then compute species accumulation curves using sample-based rarefaction. The analysis should include both observed accumulation and rarefaction-based estimates.

## Requirements

1. **Data Generation**: Create synthetic sampling data with a specified number of sites (default 50) and species pool (default 100 species). Each site should have a random subset of species with realistic abundance distributions following a log-normal pattern.

2. **Species Accumulation Calculation**: Compute the observed species accumulation curve by randomly ordering sites and calculating cumulative species richness. Perform multiple randomizations (default 100) to get mean and confidence intervals.

3. **Rarefaction Analysis**: Calculate sample-based rarefaction curves that estimate expected species richness for different numbers of sampling sites, accounting for sampling effort differences.

4. **Statistical Summary**: Output summary statistics including total species richness, mean species per site, species accumulation rate, and asymptotic richness estimates using the Chao2 estimator.

5. **Visualization**: Generate a plot showing the species accumulation curve with confidence bands, rarefaction curve, and asymptotic estimate. Save as PNG format.

6. **Data Export**: Save the results to a JSON file containing the accumulation data, rarefaction estimates, and summary statistics, plus a CSV file with site-by-species occurrence matrix.

Use argparse to handle command-line arguments for number of sites, species pool size, number of randomizations, and output directory.
