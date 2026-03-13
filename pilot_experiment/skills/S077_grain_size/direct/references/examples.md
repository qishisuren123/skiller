# Example 1: Basic grain size analysis workflow
import numpy as np
import json

# Sample grain diameter data (micrometers)
grain_data = "45.2, 67.8, 123.4, 89.1, 156.7, 234.5, 78.9, 145.2, 67.3, 189.4"
diameters = np.array([float(x.strip()) for x in grain_data.split(',')])

# Calculate key metrics
d10, d50, d90 = np.percentile(diameters, [10, 50, 90])
mean_size = np.mean(diameters)

# Size classification
fine_count = np.sum(diameters < 50)
medium_count = np.sum((diameters >= 50) & (diameters <= 200))
coarse_count = np.sum(diameters > 200)

print(f"D50: {d50:.1f} μm, Mean: {mean_size:.1f} μm")
print(f"Fine: {fine_count}, Medium: {medium_count}, Coarse: {coarse_count}")

# Example 2: Complete analysis with error handling
def robust_grain_analysis(diameter_string):
    try:
        # Parse and validate
        diameters = np.array([float(x.strip()) for x in diameter_string.split(',')])
        
        if len(diameters) < 5:
            raise ValueError("Insufficient data for reliable analysis")
        
        if np.any(diameters <= 0):
            raise ValueError("Invalid grain sizes detected")
        
        # Distribution analysis
        percentiles = np.percentile(diameters, [10, 30, 50, 60, 90])
        d10, d30, d50, d60, d90 = percentiles
        
        # Coefficients with error handling
        cu = d60 / d10 if d10 > 0 else float('inf')
        cc = (d30**2) / (d60 * d10) if (d60 * d10) > 0 else float('inf')
        
        results = {
            'statistics': {
                'mean': float(np.mean(diameters)),
                'std_dev': float(np.std(diameters, ddof=1))
            },
            'distribution': {
                'd10': float(d10), 'd50': float(d50), 'd90': float(d90),
                'uniformity_coefficient': float(cu),
                'curvature_coefficient': float(cc)
            }
        }
        
        return results
        
    except Exception as e:
        return {'error': str(e)}

# Usage example
sample_data = "12.5, 45.8, 67.2, 89.1, 123.4, 156.7, 189.3, 234.5"
analysis = robust_grain_analysis(sample_data)
print(json.dumps(analysis, indent=2))
