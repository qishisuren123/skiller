# Example 1: Basic phenological analysis
import pandas as pd
import numpy as np

# Create sample phenological data
years = np.arange(1990, 2021)
base_doy = 120  # Day 120 (late April)
trend = -0.3 * (years - 1990)  # Advancing trend
noise = np.random.normal(0, 5, len(years))
temperature = 15 + 0.02 * (years - 1990) + np.random.normal(0, 1, len(years))
precipitation = 800 + np.random.normal(0, 100, len(years))

# Add a change-point at year 2005
change_year = 2005
change_idx = np.where(years >= change_year)[0]
trend[change_idx] += -0.5 * (years[change_idx] - change_year)

doy = base_doy + trend + noise

data = pd.DataFrame({
    'year': years,
    'doy': doy,
    'temperature': temperature,
    'precipitation': precipitation
})

# Run analysis
analyzer = PhenologicalAnalyzer()
results = analyzer.analyze(data)

print(f"Detected change-points: {results['changepoints']}")
print(f"Trend: {results['mann_kendall']['trend']}")

# Example 2: Climate correlation analysis with lag effects
def analyze_climate_phenology_relationship(data, species_name):
    """Analyze relationship between climate and phenology with lag effects"""
    analyzer = PhenologicalAnalyzer()
    
    # Perform full analysis
    results = analyzer.analyze(data)
    
    # Extract significant climate correlations
    significant_correlations = {}
    
    for climate_var in results['climate_correlations']:
        significant_correlations[climate_var] = {}
        
        for lag in results['climate_correlations'][climate_var]:
            corr_data = results['climate_correlations'][climate_var][lag]
            
            # Check if correlation is significant (p < 0.05)
            if corr_data['pearson_p'] < 0.05:
                significant_correlations[climate_var][lag] = {
                    'correlation': corr_data['pearson_r'],
                    'p_value': corr_data['pearson_p'],
                    'strength': 'strong' if abs(corr_data['pearson_r']) > 0.7 else 
                               'moderate' if abs(corr_data['pearson_r']) > 0.4 else 'weak'
                }
    
    # Generate interpretation
    interpretation = {
        'species': species_name,
        'analysis_period': f"{data['year'].min()}-{data['year'].max()}",
        'significant_climate_drivers': significant_correlations,
        'change_points': results['changepoints'],
        'overall_trend': results['mann_kendall']['trend'],
        'trend_magnitude': f"{results['mann_kendall']['sens_slope']:.2f} days/year"
    }
    
    return interpretation

# Usage example
sample_data = pd.DataFrame({
    'year': range(2000, 2021),
    'doy': [115, 118, 112, 110, 108, 114, 109, 107, 105, 111, 
            106, 104, 108, 103, 101, 105, 102, 100, 104, 99, 98],
    'temperature': [14.2, 14.8, 15.1, 15.3, 15.7, 15.2, 15.9, 16.1, 16.3, 15.8,
                   16.5, 16.8, 16.2, 17.1, 17.3, 16.9, 17.5, 17.8, 17.2, 18.1, 18.3],
    'precipitation': [850, 820, 780, 900, 760, 840, 720, 880, 690, 810,
                     740, 860, 700, 830, 680, 790, 660, 820, 640, 770, 620]
})

interpretation = analyze_climate_phenology_relationship(sample_data, "Cherry Blossom")
print(f"Analysis for {interpretation['species']}:")
print(f"Trend: {interpretation['overall_trend']} ({interpretation['trend_magnitude']})")
print(f"Change-points detected: {interpretation['change_points']}")
