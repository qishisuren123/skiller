#!/usr/bin/env python3
"""
High-Energy Physics Event Analysis Tool
Analyzes particle collision data with quality cuts and signal classification.
"""

import argparse
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze particle collision event data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--mass-window', default='80,100', 
                       help='Mass window for signal selection (min,max in GeV)')
    return parser.parse_args()

def parse_mass_window(mass_window_str):
    """Parse mass window string into min,max values"""
    try:
        mass_min, mass_max = map(float, mass_window_str.split(','))
        if mass_min >= mass_max:
            raise ValueError("Mass window minimum must be less than maximum")
        return mass_min, mass_max
    except ValueError as e:
        raise ValueError(f"Invalid mass window format: {mass_window_str}. Use 'min,max' format.")

def load_and_validate_data(input_path):
    """Load CSV data and validate required columns"""
    required_columns = [
        'event_id', 'n_tracks', 'total_energy', 'missing_et', 
        'leading_jet_pt', 'leading_jet_eta', 'n_jets', 'n_leptons', 'invariant_mass'
    ]
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise IOError(f"Failed to read input file {input_path}: {e}")
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Convert to numeric, replacing invalid values with NaN
    numeric_cols = [col for col in required_columns if col != 'event_id']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove rows with any NaN values in physics quantities
    initial_count = len(df)
    df = df.dropna(subset=numeric_cols)
    if len(df) < initial_count:
        print(f"Warning: Removed {initial_count - len(df)} events with invalid data")
    
    return df

def apply_quality_cuts(df):
    """Apply sequential quality cuts and track cut flow"""
    cut_flow = {'initial': len(df)}
    
    # Cut 1: Minimum track requirement
    df = df[df['n_tracks'] >= 2]
    cut_flow['n_tracks_cut'] = len(df)
    
    # Cut 2: Energy threshold
    df = df[df['total_energy'] > 10.0]
    cut_flow['energy_cut'] = len(df)
    
    # Cut 3: Detector acceptance (pseudorapidity)
    df = df[np.abs(df['leading_jet_eta']) < 2.5]
    cut_flow['eta_cut'] = len(df)
    
    return df, cut_flow

def classify_events(df, mass_min, mass_max):
    """Classify events as signal or background"""
    # Signal: invariant mass in window AND at least 2 leptons
    signal_mask = (
        (df['invariant_mass'] >= mass_min) & 
        (df['invariant_mass'] <= mass_max) & 
        (df['n_leptons'] >= 2)
    )
    
    df = df.copy()
    df['event_type'] = np.where(signal_mask, 'signal', 'background')
    
    n_signal = (df['event_type'] == 'signal').sum()
    n_background = (df['event_type'] == 'background').sum()
    
    # Calculate statistical significance
    total_events = n_signal + n_background
    if total_events > 0:
        signal_to_noise = n_signal / n_background if n_background > 0 else float('inf')
        significance = n_signal / np.sqrt(total_events)
    else:
        signal_to_noise = 0
        significance = 0
    
    return df, n_signal, n_background, signal_to_noise, significance

def save_results(df, output_dir, cut_flow, n_signal, n_background, significance, signal_to_noise):
    """Save filtered events and summary statistics"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save filtered events
    events_path = os.path.join(output_dir, 'filtered_events.csv')
    df.to_csv(events_path, index=False)
    
    # Create summary statistics
    summary = {
        'total_events_after_cuts': len(df),
        'signal_events': int(n_signal),
        'background_events': int(n_background),
        'signal_fraction': float(n_signal / len(df)) if len(df) > 0 else 0,
        'signal_to_noise_ratio': float(signal_to_noise) if signal_to_noise != float('inf') else None,
        'statistical_significance': float(significance),
        'cut_flow': cut_flow
    }
    
    # Save summary as JSON
    summary_path = os.path.join(output_dir, 'event_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return events_path, summary_path

def print_analysis_summary(cut_flow, n_signal, n_background, significance):
    """Print analysis summary to console"""
    print("\n" + "="*50)
    print("PHYSICS EVENT ANALYSIS SUMMARY")
    print("="*50)
    
    print(f"Events before cuts: {cut_flow['initial']:,}")
    print(f"Events after cuts:  {cut_flow['eta_cut']:,}")
    
    total_after_cuts = n_signal + n_background
    if total_after_cuts > 0:
        cut_efficiency = (cut_flow['eta_cut'] / cut_flow['initial']) * 100
        signal_fraction = (n_signal / total_after_cuts) * 100
        
        print(f"Cut efficiency:     {cut_efficiency:.1f}%")
        print(f"Signal events:      {n_signal:,}")
        print(f"Background events:  {n_background:,}")
        print(f"Signal fraction:    {signal_fraction:.1f}%")
        print(f"Statistical significance: {significance:.2f}")
    else:
        print("No events survived quality cuts!")

def main():
    args = parse_arguments()
    
    try:
        # Parse mass window
        mass_min, mass_max = parse_mass_window(args.mass_window)
        print(f"Using mass window: {mass_min}-{mass_max} GeV")
        
        # Load and validate data
        print(f"Loading data from {args.input}...")
        df = load_and_validate_data(args.input)
        print(f"Loaded {len(df):,} events")
        
        # Apply quality cuts
        print("Applying quality cuts...")
        df_filtered, cut_flow = apply_quality_cuts(df)
        
        if len(df_filtered) == 0:
            print("Error: No events survived quality cuts!")
            return 1
        
        # Classify events
        print("Classifying events...")
        df_classified, n_signal, n_background, signal_to_noise, significance = classify_events(
            df_filtered, mass_min, mass_max
        )
        
        # Save results
        print(f"Saving results to {args.output}...")
        events_path, summary_path = save_results(
            df_classified, args.output, cut_flow, n_signal, n_background, 
            significance, signal_to_noise
        )
        
        # Print summary
        print_analysis_summary(cut_flow, n_signal, n_background, significance)
        print(f"\nResults saved:")
        print(f"  Events: {events_path}")
        print(f"  Summary: {summary_path}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
