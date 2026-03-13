# SKILL: Neural Population Activity Visualization

## Overview
A Python CLI tool that processes neural firing rate data from CSV files and generates two key visualizations: a trial-averaged firing rate heatmap and a population PSTH (Peri-Stimulus Time Histogram) with error bars. The tool uses matplotlib with non-interactive backend for automated plot generation.

## Workflow

1. **Setup and Argument Parsing**
   - Configure matplotlib to use 'Agg' backend (non-interactive)
   - Parse CLI arguments for input CSV file and output directory
   - Validate file existence and create output directory if needed

2. **Data Loading and Validation**
   - Load CSV file using pandas
   - Identify neuron columns (those starting with 'neuron_')
   - Validate required columns exist (trial, time, at least one neuron column)

3. **Data Processing**
   - Group data by time points and calculate trial-averaged firing rates per neuron
   - Compute population statistics (mean and SEM across neurons for each time point)
   - Extract summary statistics (neuron count, trial count, time range)

4. **Generate Heatmap**
   - Create neurons × time matrix from trial-averaged data
   - Generate heatmap using matplotlib with appropriate colormap
   - Save as 'firing_rate_heatmap.png'

5. **Generate Population PSTH**
   - Plot population mean firing rate over time as line plot
   - Add shaded error region using SEM
   - Save as 'population_psth.png'

6. **Output Summary**
   - Print data summary including neuron count, trial count, and time range
   - Confirm successful plot generation

## Common Pitfalls & Solutions

1. **Interactive Backend Issues**
   - *Problem*: Script fails in headless environments or when display not available
   - *Solution*: Set `matplotlib.use('Agg')` before importing pyplot

2. **Missing Neuron Columns**
   - *Problem*: CSV has different column naming convention than expected 'neuron_X'
   - *Solution*: Use flexible pattern matching or allow custom column prefix via argument

3. **Memory Issues with Large Datasets**
   - *Problem*: Large CSV files cause memory overflow during groupby operations
   - *Solution*: Process data in chunks or use more memory-efficient aggregation methods

4. **Inconsistent Time Points Across Trials**
   - *Problem*: Different trials have different time sampling, causing alignment issues
   - *Solution*: Interpolate to common time grid or filter to common time range only

5. **Empty Output Directory Permissions**
   - *Problem*: Script fails when trying to create output directory due to permissions
   - *Solution*: Check directory permissions and provide clear error message with suggested fix

## Error Handling Tips

- Wrap file I/O operations in try-except blocks with specific error messages
- Validate data shape and content before processing (check for NaN values, negative firing rates)
- Use `os.makedirs(exist_ok=True)` for directory creation
- Add data type validation for numeric columns
- Implement graceful degradation if only subset of expected columns present

## Reference Code Snippet

```python
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

def process_neural_data(csv_path, output_dir):
    # Load and validate data
    df = pd.read_csv(csv_path)
    neuron_cols = [col for col in df.columns if col.startswith('neuron_')]
    
    # Trial-averaged firing rates
    avg_rates = df.groupby('time')[neuron_cols].mean()
    
    # Population statistics
    pop_mean = avg_rates.mean(axis=1)
    pop_sem = avg_rates.sem(axis=1)
    
    # Generate heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(avg_rates.T, cmap='viridis')
    plt.xlabel('Time')
    plt.ylabel('Neurons')
    plt.title('Trial-Averaged Firing Rate Heatmap')
    plt.savefig(f'{output_dir}/firing_rate_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Generate PSTH
    plt.figure(figsize=(10, 6))
    time_points = avg_rates.index
    plt.plot(time_points, pop_mean, 'b-', linewidth=2)
    plt.fill_between(time_points, pop_mean - pop_sem, pop_mean + pop_sem, 
                     alpha=0.3, color='blue')
    plt.xlabel('Time')
    plt.ylabel('Population Firing Rate (Hz)')
    plt.title('Population PSTH')
    plt.savefig(f'{output_dir}/population_psth.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return len(neuron_cols), df['trial'].nunique(), (df['time'].min(), df['time'].max())
```