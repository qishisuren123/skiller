# Species Accumulation Curve Analysis

## Overview
This skill enables computation and analysis of species accumulation curves from ecological sampling data using sample-based rarefaction methods. It generates synthetic biodiversity data, calculates accumulation patterns, and provides statistical estimates for biodiversity assessment and sampling optimization.

## Workflow
1. **Generate synthetic ecological data** with realistic species abundance distributions using log-normal patterns across multiple sampling sites
2. **Create site-by-species occurrence matrix** representing presence/absence data for biodiversity analysis
3. **Compute observed accumulation curves** through multiple random site orderings to calculate mean cumulative species richness and confidence intervals
4. **Calculate sample-based rarefaction** to estimate expected species richness for different sampling efforts and enable fair comparisons
5. **Estimate asymptotic richness** using Chao2 estimator to predict total species diversity in the community
6. **Generate visualization** showing accumulation curves, confidence bands, rarefaction estimates, and asymptotic projections
7. **Export results** to JSON (statistics and curves) and CSV (occurrence matrix) formats for further analysis

## Common Pitfalls
- **Insufficient randomizations**: Using too few iterations (<50) leads to unstable confidence intervals. Solution: Use at least 100 randomizations for robust statistics
- **Unrealistic species distributions**: Using uniform distributions creates unrealistic ecological patterns. Solution: Apply log-normal abundance distributions to simulate natural rarity patterns
- **Ignoring sampling effort differences**: Comparing raw accumulation curves between studies with different site numbers. Solution: Always use rarefaction to standardize sampling effort
- **Incorrect Chao2 calculation**: Using species frequency data incorrectly or with insufficient rare species. Solution: Ensure proper incidence-based frequency calculations and validate with adequate sample sizes
- **Overinterpreting asymptotic estimates**: Treating Chao2 estimates as absolute truth rather than statistical estimates. Solution: Report confidence intervals and acknowledge estimation uncertainty

## Error Handling
- Validate that species pool size is larger than maximum species per site to prevent impossible sampling scenarios
- Check for empty sites or sites with no species and handle gracefully by excluding from analysis
- Implement bounds checking for rarefaction to prevent extrapolation beyond observed sample sizes
- Handle edge cases where all species are singletons or doubletons in Chao2 calculations by providing fallback estimates
- Ensure output directories exist and are writable before attempting file operations

## Quick Reference
