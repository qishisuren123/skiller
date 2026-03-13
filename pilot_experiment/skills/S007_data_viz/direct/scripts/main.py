#!/usr/bin/env python3
"""
Neural Population Activity Visualization Tool
Generates heatmaps and population PSTHs from neural firing rate data.
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns

def load_and_validate_data(csv_file):
    """Load CSV and validate required structure."""
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        raise ValueError(f"Could not read CSV file: {e}")
    
    # Check required columns
    if 'trial' not in df.columns or 'time' not in df.columns:
        raise ValueError("CSV must contain 'trial' and 'time' columns")
    
    # Find neuron columns
    neuron_cols = [col for col in df.columns if col.startswith('neuron_')]
    if not neuron_cols:
        raise ValueError("No neuron columns found (should start with 'neuron_')")
    
    return df, neuron_cols

def process_neural_data(df, neuron_cols):
    """Process data into trial-averaged format and compute population statistics."""
    # Create pivot table to handle any duplicate trial/time combinations
    pivot_data = df.pivot_table(
        index=['trial', 'time'], 
        values=neuron_cols, 
        aggfunc='mean'
    ).reset_index()
    
    # Calculate trial-averaged firing rates (neurons × time)
    trial_avg = pivot_data.groupby('time')[neuron_cols].mean()
    
    # Population statistics over time
    pop_mean = trial_avg.mean(axis=1)
    pop_sem = trial_avg.sem(axis=1)
    
    # Get summary statistics
    n_neurons = len(neuron_cols)
    n_trials = df['trial'].nunique()
    time_range = (df['time'].min(), df['time'].max())
    
    return trial_avg, pop_mean, pop_sem, n_neurons, n_trials, time_range

def create_firing_rate_heatmap(trial_avg_data, output_path):
    """Generate and save firing rate heatmap."""
    plt.figure(figsize=(12, 8))
    
    # Create heatmap with neurons on y-axis, time on x-axis
    sns.heatmap(
        trial_avg_data.T,  # Transpose for neurons × time orientation
        cmap='viridis',
        cbar_kws={'label': 'Firing Rate (Hz)'},
        xticklabels=50,  # Show every 50th time label
        yticklabels=True
    )
    
    plt.title('Trial-Averaged Neural Population Activity', fontsize=14, fontweight='bold')
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('Neuron ID', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_population_psth(time_points, pop_mean, pop_sem, output_path):
    """Generate and save population PSTH with error shading."""
    plt.figure(figsize=(10, 6))
    
    # Plot mean with SEM shading
    plt.plot(time_points, pop_mean, 'b-', linewidth=2, label='Population Mean')
    plt.fill_between(
        time_points, 
        pop_mean - pop_sem, 
        pop_mean + pop_sem,
        alpha=0.3, 
        color='blue', 
        label='±SEM'
    )
    
    plt.title('Population Peristimulus Time Histogram', fontsize=14, fontweight='bold')
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('Mean Firing Rate (Hz)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(
        description='Visualize neural population activity data from CSV files'
    )
    parser.add_argument(
        '--input', 
        required=True, 
        help='Input CSV file with trial, time, and neuron_* columns'
    )
    parser.add_argument(
        '--output-dir', 
        required=True, 
        help='Output directory for saving PNG plots'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Load and process data
        print("Loading neural activity data...")
        df, neuron_cols = load_and_validate_data(args.input)
        
        print("Processing neural population data...")
        trial_avg, pop_mean, pop_sem, n_neurons, n_trials, time_range = process_neural_data(df, neuron_cols)
        
        # Generate visualizations
        print("Creating firing rate heatmap...")
        heatmap_path = os.path.join(args.output_dir, 'firing_rate_heatmap.png')
        create_firing_rate_heatmap(trial_avg, heatmap_path)
        
        print("Creating population PSTH...")
        psth_path = os.path.join(args.output_dir, 'population_psth.png')
        create_population_psth(trial_avg.index, pop_mean, pop_sem, psth_path)
        
        # Print summary
        print("\n" + "="*50)
        print("NEURAL POPULATION ANALYSIS SUMMARY")
        print("="*50)
        print(f"Number of neurons: {n_neurons}")
        print(f"Number of trials: {n_trials}")
        print(f"Time range: {time_range[0]:.2f} to {time_range[1]:.2f}")
        print(f"Mean population firing rate: {pop_mean.mean():.2f} ± {pop_mean.std():.2f} Hz")
        print(f"\nPlots saved to: {args.output_dir}")
        print(f"  - {heatmap_path}")
        print(f"  - {psth_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
