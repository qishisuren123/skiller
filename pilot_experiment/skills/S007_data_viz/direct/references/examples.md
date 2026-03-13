# Example 1: Basic usage with sample data
"""
Sample CSV structure:
trial,time,neuron_0,neuron_1,neuron_2
1,0.0,2.3,1.8,3.1
1,0.1,2.5,2.1,3.4
2,0.0,2.1,1.9,2.8
2,0.1,2.4,2.0,3.2
"""

# Command line usage:
# python main.py --input neural_data.csv --output-dir ./plots

# Example 2: Processing workflow for custom analysis
import pandas as pd
import numpy as np

# Load and reshape neural data
df = pd.read_csv('neural_data.csv')
neuron_cols = [col for col in df.columns if col.startswith('neuron_')]

# Create trial-averaged activity matrix
pivot_data = df.pivot_table(
    index=['trial', 'time'], 
    values=neuron_cols, 
    aggfunc='mean'
)
trial_averaged = pivot_data.groupby('time').mean()

# Compute population statistics
population_mean = trial_averaged.mean(axis=1)
population_sem = trial_averaged.sem(axis=1)

# The trial_averaged DataFrame has shape (n_timepoints, n_neurons)
# Perfect for heatmap visualization with .T for (neurons, timepoints)
print(f"Data shape: {trial_averaged.shape}")
print(f"Population activity range: {population_mean.min():.2f} - {population_mean.max():.2f} Hz")
