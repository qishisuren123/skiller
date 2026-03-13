# Galaxy Morphology Classification from Photometric Catalog

Create a CLI script that classifies galaxy morphology using photometric catalog data. Your script should process synthetic galaxy observations and classify them into morphological types based on their photometric properties.

## Requirements

1. **Data Processing**: Read synthetic photometric catalog data containing galaxy measurements including magnitudes in different bands (u, g, r, i, z), half-light radius, axis ratio, concentration index, and surface brightness parameters.

2. **Color Calculations**: Compute standard color indices (g-r, r-i, u-g) from the magnitude measurements, which are crucial for morphological classification.

3. **Morphological Classification**: Implement a classification scheme that assigns galaxies to one of four morphological types:
   - Elliptical: High concentration index (>2.8), red colors (g-r > 0.8)
   - Spiral: Moderate concentration (2.2-2.8), intermediate colors, axis ratio < 0.7
   - Irregular: Low concentration (<2.2), blue colors (g-r < 0.6), small size
   - Lenticular: High concentration but bluer than ellipticals, axis ratio > 0.7

4. **Statistical Analysis**: Calculate and output summary statistics including the fraction of each morphological type, mean properties per type, and identification of outliers (galaxies with unusual property combinations).

5. **Quality Assessment**: Implement quality flags for unreliable classifications based on measurement uncertainties, extreme colors, or missing data, and report the fraction of high-quality classifications.

6. **Output Generation**: Save results as both a detailed CSV catalog with individual galaxy classifications and properties, and a JSON summary file containing population statistics and quality metrics.

## Command Line Interface
