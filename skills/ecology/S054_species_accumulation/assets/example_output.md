Species Accumulation Analysis Results:
Total species observed: 87
Mean species per site: 14.82
Chao2 asymptotic estimate: 94.3
Sampling completeness: 92.3%
Results saved to: output

Files created:
- output/occurrence_matrix.csv (site-by-species data)
- output/species_accumulation_plot.png (comprehensive visualization)
- output/analysis_results.json (complete numerical results)

JSON structure includes:
{
  "summary_statistics": {
    "total_species_observed": 87,
    "chao2_estimate": 94.3,
    "sampling_completeness": 0.923
  },
  "species_accumulation": {
    "sites": [1, 2, 3, ...],
    "mean_richness": [8.2, 15.4, 21.8, ...],
    "ci_lower": [6.1, 13.2, 19.5, ...],
    "ci_upper": [10.3, 17.6, 24.1, ...]
  }
}
