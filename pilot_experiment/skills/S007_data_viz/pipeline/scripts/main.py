#!/usr/bin/env python3
import argparse
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import os

def load_and_process_data(input_file):
    """Load CSV data and extract neuron columns"""
    df = pd.read_csv(input_file)
    
    # Get neuron columns
    neuron_cols = [col for col in df.columns if col.startswith('neuron_')]
    
    return df, neuron_cols

def create_heatmap(df, neuron_cols, output_dir):
    """Create firing rate heatmap"""
    # More efficient groupby operation - compute mean directly on neuron columns
    avg_data = df.groupby('time', sort=True)[neuron_cols].mean()
    
    plt.figure(figsize=(12, 8))
    
    # Create heatmap using imshow with proper axis labels
    heatmap_data = avg_data.T.values
    im = plt.imshow(heatmap_data, aspect='auto', cmap='viridis', origin='lower')
    
    # Set proper x-axis labels (time values)
    time_values = avg_data.index.values
    n_time_ticks = min(10, len(time_values))
    time_tick_indices = np.linspace(0, len(time_values)-1, n_time_ticks, dtype=int)
    plt.xticks(time_tick_indices, [f'{time_values[i]:.1f}' for i in time_tick_indices])
    
    # Smart y-axis labeling for neurons - avoid overcrowding
    n_neurons = len(neuron_cols)
    if n_neurons <= 20:
        # Show all neuron labels if reasonable number
        plt.yticks(range(n_neurons), neuron_cols)
    elif n_neurons <= 100:
        # Show every 5th neuron
        step = 5
        tick_indices = range(0, n_neurons, step)
        plt.yticks(tick_indices, [neuron_cols[i] for i in tick_indices])
    else:
        # For very large datasets, show only a few representative labels
        n_ticks = 10
        tick_indices = np.linspace(0, n_neurons-1, n_ticks, dtype=int)
        plt.yticks(tick_indices, [f'neuron_{i}' for i in tick_indices])
    
    plt.colorbar(im, label='Firing Rate')
    plt.xlabel('Time')
    plt.ylabel('Neurons')
    plt.title(f'Trial-Averaged Firing Rate Heatmap ({n_neurons} neurons)')
    plt.savefig(os.path.join(output_dir, 'firing_rate_heatmap.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_population_psth(df, neuron_cols, output_dir):
    """Create population PSTH with SEM"""
    # More efficient approach: calculate population mean directly without copying entire DataFrame
    
    # Calculate population mean for each row using numpy for speed
    neuron_data = df[neuron_cols].values
    pop_means = np.nanmean(neuron_data, axis=1)
    
    # Create a smaller DataFrame with just the columns we need
    psth_df = pd.DataFrame({
        'trial': df['trial'].values,
        'time': df['time'].values,
        'pop_mean': pop_means
    })
    
    # Create pivot table - this is the bottleneck for large datasets
    try:
        pivot_data = psth_df.pivot_table(index='trial', columns='time', values='pop_mean', 
                                       fill_value=np.nan)
    except MemoryError:
        # Fallback for very large datasets - use groupby approach
        print("Warning: Dataset too large for pivot table, using alternative method...")
        time_stats = psth_df.groupby('time')['pop_mean'].agg(['mean', 'sem']).reset_index()
        time_values = time_stats['time'].values
        mean_values = time_stats['mean'].values
        sem_values = time_stats['sem'].fillna(0).values
    else:
        # Standard pivot approach
        time_mean = pivot_data.mean(axis=0, skipna=True)
        time_sem = pivot_data.sem(axis=0, skipna=True)
        
        # Remove any time points where we couldn't calculate valid statistics
        valid_mask = ~(time_mean.isna() | time_sem.isna())
        time_values = time_mean.index[valid_mask].values
        mean_values = time_mean[valid_mask].values
        sem_values = time_sem[valid_mask].fillna(0).values
    
    plt.figure(figsize=(10, 6))
    plt.plot(time_values, mean_values, 'b-', linewidth=2)
    plt.fill_between(time_values, 
                     mean_values - sem_values,
                     mean_values + sem_values, 
                     alpha=0.3, color='blue')
    plt.xlabel('Time')
    plt.ylabel('Population Firing Rate')
    plt.title('Population PSTH')
    plt.savefig(os.path.join(output_dir, 'population_psth.png'), dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Visualize neural population activity')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output-dir', required=True, help='Output directory for plots')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load data
    df, neuron_cols = load_and_process_data(args.input)
    
    # Create plots
    create_heatmap(df, neuron_cols, args.output_dir)
    create_population_psth(df, neuron_cols, args.output_dir)
    
    # Print summary
    n_neurons = len(neuron_cols)
    n_trials = df['trial'].nunique()
    time_range = (df['time'].min(), df['time'].max())
    
    print(f"Summary:")
    print(f"Number of neurons: {n_neurons}")
    print(f"Number of trials: {n_trials}")
    print(f"Time range: {time_range[0]} to {time_range[1]}")

if __name__ == "__main__":
    main()
