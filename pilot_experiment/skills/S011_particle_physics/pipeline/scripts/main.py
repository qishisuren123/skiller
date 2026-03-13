#!/usr/bin/env python3
import argparse
import pandas as pd
import json
import os
import math

def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze particle collision event data')
    parser.add_argument('--input', required=True, help='Path to input CSV file')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--mass-window', default='80,100', 
                       help='Mass window for signal selection (default: 80,100)')
    return parser.parse_args()

def parse_mass_window(mass_window_str):
    """Parse mass window string into min,max values with validation"""
    try:
        parts = mass_window_str.split(',')
        if len(parts) != 2:
            raise ValueError(f"Mass window must have exactly 2 values separated by comma, got: {mass_window_str}")
        
        mass_min, mass_max = float(parts[0].strip()), float(parts[1].strip())
        
        if mass_min < 0 or mass_max < 0:
            raise ValueError(f"Mass values cannot be negative: {mass_min}, {mass_max}")
        
        if mass_min >= mass_max:
            raise ValueError(f"Mass minimum ({mass_min}) must be less than maximum ({mass_max})")
        
        if mass_max > 1000:
            print(f"Warning: Very high mass window maximum ({mass_max} GeV) - is this intentional?")
        
        return mass_min, mass_max
        
    except ValueError as e:
        print(f"Error parsing mass window '{mass_window_str}': {e}")
        raise
    except Exception as e:
        print(f"Unexpected error parsing mass window: {e}")
        raise

def load_data(input_file):
    """Load collision event data from CSV with validation and memory optimization"""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    try:
        # Check required columns with sample
        sample_df = pd.read_csv(input_file, nrows=100)
        required_columns = ['event_id', 'n_tracks', 'total_energy', 'missing_et', 
                          'leading_jet_pt', 'leading_jet_eta', 'n_jets', 'n_leptons', 'invariant_mass']
        
        missing_columns = [col for col in required_columns if col not in sample_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Load with memory-efficient data types
        df = pd.read_csv(input_file, dtype={
            'event_id': 'int32',
            'n_tracks': 'int16', 
            'total_energy': 'float32',
            'missing_et': 'float32',
            'leading_jet_pt': 'float32',
            'leading_jet_eta': 'float32',
            'n_jets': 'int16',
            'n_leptons': 'int8',
            'invariant_mass': 'float32'
        })
        
        print(f"Loaded {len(df)} events from CSV")
        return df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

def clean_data(df):
    """Clean data by handling NaN values and invalid entries"""
    n_initial = len(df)
    print(f"Cleaning {n_initial} events...")
    
    if n_initial == 0:
        print("Warning: No events to clean!")
        return df
    
    # Report NaN values
    nan_counts = df.isnull().sum()
    if nan_counts.any():
        print("NaN values found:")
        for col, count in nan_counts[nan_counts > 0].items():
            print(f"  {col}: {count} NaN values")
    
    # Create boolean masks for efficiency
    critical_columns = ['n_tracks', 'total_energy', 'leading_jet_eta', 'n_leptons', 'invariant_mass']
    valid_mask = ~df[critical_columns].isnull().any(axis=1)
    
    invalid_mask = (
        (df['n_tracks'] < 0) |
        (df['total_energy'] <= 0) |
        (df['n_leptons'] < 0) |
        (df['n_jets'] < 0) |
        (df['leading_jet_eta'].abs() > 10)
    )
    
    final_mask = valid_mask & ~invalid_mask
    df_clean = df[final_mask].copy()
    
    del df  # Free memory
    
    n_removed = n_initial - len(df_clean)
    if n_removed > 0:
        print(f"Removed {n_removed} events with invalid/missing data")
    
    return df_clean

def apply_quality_cuts_with_flow(df):
    """Apply quality cuts and track cut flow"""
    if len(df) == 0:
        return df, {'initial_events': 0, 'after_n_tracks_cut': 0, 'after_energy_cut': 0, 'after_eta_cut': 0, 'final_events': 0}
    
    cut_flow = {}
    cut_flow['initial_events'] = len(df)
    
    # Use cumulative boolean mask for memory efficiency
    mask = pd.Series(True, index=df.index)
    
    # Apply cuts sequentially
    n_tracks_mask = df['n_tracks'] >= 2
    mask &= n_tracks_mask
    cut_flow['after_n_tracks_cut'] = mask.sum()
    print(f"After n_tracks >= 2: {mask.sum()} events")
    
    energy_mask = df['total_energy'] > 10
    mask &= energy_mask
    cut_flow['after_energy_cut'] = mask.sum()
    print(f"After total_energy > 10: {mask.sum()} events")
    
    eta_mask = df['leading_jet_eta'].abs() < 2.5
    mask &= eta_mask
    cut_flow['after_eta_cut'] = mask.sum()
    print(f"After |leading_jet_eta| < 2.5: {mask.sum()} events")
    
    cut_flow['final_events'] = mask.sum()
    
    df_filtered = df[mask].copy()
    return df_filtered, cut_flow

def classify_events(df, mass_min, mass_max):
    """Classify events as signal or background"""
    if len(df) == 0:
        return df
    
    print(f"Debug: Classifying {len(df)} events")
    print(f"Debug: Mass range {mass_min} - {mass_max}")
    
    # Create boolean conditions
    mass_condition = (df['invariant_mass'] >= mass_min) & (df['invariant_mass'] <= mass_max)
    lepton_condition = (df['n_leptons'] >= 2)
    signal_mask = mass_condition & lepton_condition
    
    print(f"Debug: Events in mass window: {mass_condition.sum()}")
    print(f"Debug: Events with >=2 leptons: {lepton_condition.sum()}")
    print(f"Debug: Signal events: {signal_mask.sum()}")
    
    # Assign classification
    df['classification'] = 'background'
    df.loc[signal_mask, 'classification'] = 'signal'
    
    return df

def calculate_statistics(df):
    """Calculate signal-to-noise ratio and significance"""
    if len(df) == 0:
        return 0, 0, 0, 0.0
    
    n_signal = (df['classification'] == 'signal').sum()
    n_background = (df['classification'] == 'background').sum()
    
    print(f"Debug: Counted {n_signal} signal, {n_background} background events")
    
    # Handle signal-to-noise ratio
    if n_background == 0:
        snr = float('inf') if n_signal > 0 else 0
    else:
        snr = n_signal / n_background
    
    # Handle significance calculation
    if n_signal + n_background == 0:
        significance = 0.0
    else:
        significance = n_signal / math.sqrt(n_signal + n_background)
    
    return n_signal, n_background, snr, significance

def save_results(df, output_dir, cut_flow, n_signal, n_background, snr, significance):
    """Save filtered events and summary statistics"""
    
    # Save filtered events CSV
    filtered_csv_path = os.path.join(output_dir, 'filtered_events.csv')
    df.to_csv(filtered_csv_path, index=False)
    print(f"Saved filtered events to: {filtered_csv_path}")
    
    # Create summary dictionary
    summary = {
        'total_events': cut_flow['final_events'],
        'signal_events': n_signal,
        'background_events': n_background,
        'signal_to_noise_ratio': snr if snr != float('inf') else None,
        'significance': significance,
        'cut_flow': cut_flow
    }
    
    # Save summary JSON
    summary_json_path = os.path.join(output_dir, 'event_summary.json')
    with open(summary_json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to: {summary_json_path}")

def main():
    try:
        args = parse_arguments()
        
        # Parse and validate mass window
        mass_min, mass_max = parse_mass_window(args.mass_window)
        print(f"Using mass window: {mass_min} - {mass_max} GeV")
        
        # Create output directory
        os.makedirs(args.output, exist_ok=True)
        
        # Load and clean data
        df = load_data(args.input)
        df_clean = clean_data(df)
        
        if len(df_clean) == 0:
            print("Error: No valid events after cleaning!")
            return
        
        # Apply cuts with flow tracking
        print("\nApplying quality cuts:")
        df_filtered, cut_flow = apply_quality_cuts_with_flow(df_clean)
        n_after_cuts = len(df_filtered)
        
        if n_after_cuts == 0:
            print("Warning: No events passed quality cuts!")
            save_results(df_filtered, args.output, cut_flow, 0, 0, 0, 0)
            return
        
        # Classify events
        df_classified = classify_events(df_filtered, mass_min, mass_max)
        n_signal, n_background, snr, significance = calculate_statistics(df_classified)
        
        # Print summary
        print(f"\n=== ANALYSIS SUMMARY ===")
        print(f"Events before cuts: {cut_flow['initial_events']}")
        print(f"Events after cuts: {n_after_cuts}")
        print(f"Signal events: {n_signal}")
        print(f"Background events: {n_background}")
        if n_after_cuts > 0:
            print(f"Signal fraction: {n_signal/n_after_cuts:.3f}")
        print(f"Significance: {significance:.3f}")
        
        # Save results
        save_results(df_classified, args.output, cut_flow, n_signal, n_background, snr, significance)
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
