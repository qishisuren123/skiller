# Example 1: Basic morphometric calculation
import pandas as pd
import numpy as np

# Sample data
data = {
    'specimen_id': ['SPEC001', 'SPEC002'],
    'taxon': ['Trilobite_A', 'Trilobite_B'],
    'length_mm': [25.4, 18.7],
    'width_mm': [12.1, 15.2],
    'height_mm': [8.3, 6.9],
    'mass_g': [2.1, 1.8],
    'formation': ['Formation_X', 'Formation_Y'],
    'epoch': ['Cambrian', 'Ordovician']
}

df = pd.DataFrame(data)

# Calculate shape indices
df['elongation'] = df['length_mm'] / df['width_mm']
df['sphericity'] = np.power(df['width_mm'] * df['height_mm'], 1/3) / df['length_mm']
df['volume_mm3'] = (4/3) * np.pi * (df['length_mm']/2) * (df['width_mm']/2) * (df['height_mm']/2)
df['density_g_cm3'] = df['mass_g'] / (df['volume_mm3'] / 1000)

print(df[['specimen_id', 'elongation', 'sphericity', 'density_g_cm3']])

# Example 2: PCA implementation with eigen-decomposition
measurements = df[['length_mm', 'width_mm', 'height_mm', 'mass_g']].values

# Standardize data
standardized = (measurements - np.mean(measurements, axis=0)) / np.std(measurements, axis=0)

# Compute PCA
cov_matrix = np.cov(standardized.T)
eigenvals, eigenvecs = np.linalg.eigh(cov_matrix)

# Sort by eigenvalue (descending)
idx = np.argsort(eigenvals)[::-1]
eigenvals = eigenvals[idx]
eigenvecs = eigenvecs[:, idx]

# Calculate explained variance and PC scores
explained_variance = eigenvals / np.sum(eigenvals)
pc_scores = standardized @ eigenvecs

print("Explained variance ratios:", explained_variance)
print("PC1 loadings:", eigenvecs[:, 0])
