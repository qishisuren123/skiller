#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
from scipy import stats
import gc

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_process_data(input_file, chunksize=10000):
    """Load CSV data in chunks and separate neuron columns from metadata."""
    logging.info(f"Loading data from {input_file}")
    
    # Read first chunk to get column info
    try:
        first_chunk = pd.read_csv(input_file, nrows=100)
    except:
        try:
            first_chunk = pd.read_csv(input_file, sep=';', nrows=100)
        except:
            first_chunk = pd.read_csv(input_file, sep='\t', nrows=100)
    
    # Identify neuron columns
    neuron_cols = [col for col in first_chunk.columns if col.startswith('neuron_')]
    metadata_cols = ['trial', 'time']
    
    logging.info(f"Found {len(neuron_cols)} neurons. Loading data in chunks...")
    
    # Load data in chunks to manage memory
    chunks = []
    chunk_reader = pd.read_csv(input_file, chunksize=chunksize)
    
    for i, chunk in enumerate(chunk_reader):
        if i % 10 == 0:
            logging.info(f"Processing chunk {i+1}")
        
        # Clean up numeric columns
        for col in neuron_cols + ['time']:
            if col in chunk.columns:
                chunk[col] = chunk[col].astype(str).str.replace(',', '.').astype(float)
        
        # Handle missing values - keep NaN for now to detect silent neurons
        chunks.append(chunk)
    
    # Concatenate all chunks
    logging.info("Combining chunks...")
    df = pd.concat(chunks, ignore_index=True)
    del chunks
    gc.collect()
    
    logging.info(f"Data loaded successfully. Shape: {df.shape}")
    return df, neuron_cols, metadata_cols

def create_heatmap(df, neuron_cols, output_dir):
    """Create trial-averaged firing rate heatmap with memory optimization."""
    logging.info("Creating heatmap...")
    
    # Process in smaller time windows to reduce memory usage
    unique_times = sorted(df['time'].unique())
    n_times = len(unique_times)
    
    # Calculate trial averages more efficiently
    trial_avg_data = []
    
    # Group by time and calculate means in batches
    for time_val in unique_times:
        time_data = df[df['time'] == time_val][neuron_cols].mean(numeric_only=True, skipna=True)
        trial_avg_data.append(time_data.values)
    
    # Convert to numpy array for heatmap
    heatmap_data = np.array(trial_avg_data).T  # neurons x time
    
    plt.figure(figsize=(12, 8))
    
    # Create heatmap
    ax = sns.heatmap(heatmap_data, cmap='viridis', cbar_kws={'label': 'Firing Rate (Hz)'})
    
    # Customize x-axis
    tick_interval = max(1, n_times // 10)
    tick_positions = range(0, n_times, tick_interval)
    tick_labels = [f'{unique_times[i]:.3f}' for i in tick_positions]
    
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Neurons')
    ax.set_title('Trial-Averaged Firing Rate Heatmap')
    
    output_path = Path(output_dir) / 'firing_rate_heatmap.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Clean up
    del heatmap_data, trial_avg_data
    gc.collect()
    
    logging.info(f"Saved heatmap to {output_path}")

def calculate_robust_population_mean(row, neuron_cols, min_neurons=3):
    """Calculate population mean only for neurons with valid data."""
    neuron_data = row[neuron_cols]
    valid_neurons = neuron_data.dropna()
    
    # Only calculate mean if we have enough valid neurons
    if len(valid_neurons) >= min_neurons:
        return valid_neurons.mean()
    else:
        return np.nan  # Return NaN if too few neurons

def safe_sem(x):
    """Calculate SEM with proper handling of edge cases."""
    x_clean = x.dropna()
    if len(x_clean) <= 1:
        return 0.0
    return stats.sem(x_clean)

def create_population_psth(df, neuron_cols, output_dir):
    """Create population PSTH with SEM and proper handling of missing neurons."""
    logging.info("Creating population PSTH...")
    
    # Calculate minimum number of neurons needed (e.g., at least 50% of total neurons)
    min_neurons = max(3, len(neuron_cols) // 2)
    logging.info(f"Requiring at least {min_neurons} active neurons per time point")
    
    # Calculate robust population mean
    df['pop_mean'] = df.apply(
        lambda row: calculate_robust_population_mean(row, neuron_cols, min_neurons), 
        axis=1
    )
    
    # Remove rows where we don't have enough neurons
    valid_data = df.dropna(subset=['pop_mean'])
    n_excluded = len(df) - len(valid_data)
    
    if n_excluded > 0:
        logging.warning(f"Excluded {n_excluded} data points with insufficient active neurons")
    
    # Group by time and calculate statistics
    psth_data = valid_data.groupby('time')['pop_mean'].agg([
        ('mean', lambda x: x.mean()),
        ('sem', safe_sem),
        ('count', 'count')  # Track how many trials contribute to each time point
    ]).reset_index()
    
    # Filter out time points with very few trials
    min_trials = max(2, psth_data['count'].quantile(0.1))  # At least 10th percentile of trial counts
    psth_data = psth_data[psth_data['count'] >= min_trials]
    
    logging.info(f"PSTH includes {len(psth_data)} time points after filtering")
    
    plt.figure(figsize=(10, 6))
    plt.plot(psth_data['time'], psth_data['mean'], 'b-', linewidth=2, label='Population Mean')
    plt.fill_between(psth_data['time'], 
                     psth_data['mean'] - psth_data['sem'],
                     psth_data['mean'] + psth_data['sem'],
                     alpha=0.3, color='blue')
    
    plt.xlabel('Time (s)')
    plt.ylabel('Population Firing Rate (Hz)')
    plt.title('Population PSTH')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_path = Path(output_dir) / 'population_psth.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Clean up
    df.drop('pop_mean', axis=1, inplace=True)
    gc.collect()
    
    logging.info(f"Saved PSTH to {output_path}")

def print_summary(df, neuron_cols):
    """Print data summary statistics."""
    n_neurons = len(neuron_cols)
    n_trials = df['trial'].nunique()
    time_range = (df['time'].min(), df['time'].max())
    
    print(f"\nData Summary:")
    print(f"Number of neurons: {n_neurons}")
    print(f"Number of trials: {n_trials}")
    print(f"Time range: {time_range[0]:.3f} to {time_range[1]:.3f} seconds")
    print(f"Total data points: {len(df):,}")

def main():
    parser = argparse.ArgumentParser(description='Visualize neural population activity data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output-dir', required=True, help='Output directory for plots')
    parser.add_argument('--chunksize', type=int, default=10000, 
                       help='Chunk size for reading large files (default: 10000)')
    
    args = parser.parse_args()
    
    setup_logging()
    
    # Create output directory if it doesn't exist
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load and process data
    df, neuron_cols, metadata_cols = load_and_process_data(args.input, args.chunksize)
    
    # Create visualizations
    create_heatmap(df, neuron_cols, args.output_dir)
    create_population_psth(df, neuron_cols, args.output_dir)
    
    # Print summary
    print_summary(df, neuron_cols)

if __name__ == '__main__':
    main()
