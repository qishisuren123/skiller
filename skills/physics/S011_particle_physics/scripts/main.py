#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze particle collision event data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--mass-window', default='80,100', 
                       help='Mass window for signal selection (default: 80,100 GeV)')
    return parser.parse_args()

def load_data(filepath):
    """Load data with robust format detection"""
    logging.info(f"Loading data from {filepath}")
    
    # Try different encodings and formats
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            # First check if it might be a different format
            if filepath.lower().endswith(('.root', '.hdf5', '.h5')):
                raise ValueError(f"Unsupported file format: {filepath}")
            
            df = pd.read_csv(filepath, encoding=encoding)
            logging.info(f"Successfully loaded with encoding: {encoding}")
            return df
            
        except UnicodeDecodeError:
            logging.warning(f"Failed to load with encoding: {encoding}")
            continue
        except Exception as e:
            logging.error(f"Error loading file: {e}")
            raise
    
    raise ValueError("Could not load file with any supported encoding")

def clean_data(df):
    """Clean and convert data types"""
    logging.info("Cleaning and validating data...")
    
    # Work with a copy to avoid view issues
    df = df.copy()
    
    # Define expected numeric columns
    numeric_columns = ['n_tracks', 'total_energy', 'missing_et', 'leading_jet_pt', 
                      'leading_jet_eta', 'n_jets', 'n_leptons', 'invariant_mass']
    
    initial_count = len(df)
    
    for col in numeric_columns:
        if col in df.columns:
            # Replace common missing value indicators
            df[col] = df[col].replace(['N/A', 'n/a', '-', '', 'NULL', 'null'], np.nan)
            
            # Convert to numeric, coercing errors to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Log data quality info
    for col in numeric_columns:
        if col in df.columns:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                logging.warning(f"Column {col}: {nan_count} missing/invalid values")
    
    # Remove rows with critical missing values
    critical_columns = ['n_tracks', 'total_energy', 'leading_jet_eta']
    df_clean = df.dropna(subset=critical_columns).copy()
    
    removed_count = initial_count - len(df_clean)
    if removed_count > 0:
        logging.info(f"Removed {removed_count} rows due to missing critical data")
    
    return df_clean

def apply_quality_cuts(df):
    """Apply quality cuts to the data"""
    initial_count = len(df)
    
    # Apply cuts and make a copy
    df_filtered = df[
        (df['n_tracks'] >= 2) &
        (df['total_energy'] > 10) &
        (np.abs(df['leading_jet_eta']) < 2.5)
    ].copy()
    
    cut_flow = {
        'initial': initial_count,
        'after_cuts': len(df_filtered)
    }
    
    return df_filtered, cut_flow

def classify_events(df, mass_min, mass_max):
    """Classify events as signal or background"""
    # Ensure we're working with a copy
    df = df.copy()
    
    signal_mask = (
        (df['invariant_mass'] >= mass_min) &
        (df['invariant_mass'] <= mass_max) &
        (df['n_leptons'] >= 2)
    )
    
    df.loc[:, 'event_type'] = np.where(signal_mask, 'signal', 'background')
    return df

def compute_statistics(df, mass_min, mass_max):
    """Compute signal-to-noise ratio and significance"""
    # Total signal and background counts
    signal_count = len(df[df['event_type'] == 'signal'])
    background_count = len(df[df['event_type'] == 'background'])
    
    # Events in the mass window (signal region)
    in_mass_window = (df['invariant_mass'] >= mass_min) & (df['invariant_mass'] <= mass_max)
    
    # Signal events (already have n_leptons >= 2 requirement)
    signal_in_window = len(df[(df['event_type'] == 'signal')])
    
    # Background events in the mass window (n_leptons < 2 but in mass range)
    background_in_window = len(df[in_mass_window & (df['n_leptons'] < 2)])
    
    # Signal-to-noise ratio
    if background_in_window == 0:
        snr = float('inf') if signal_in_window > 0 else 0
    else:
        snr = signal_in_window / background_in_window
    
    # Statistical significance: S / sqrt(S + B) where S and B are in signal region
    total_in_window = signal_in_window + background_in_window
    if total_in_window > 0:
        significance = signal_in_window / np.sqrt(total_in_window)
    else:
        significance = 0
    
    return {
        'signal_count': signal_count,
        'background_count': background_count,
        'signal_in_window': signal_in_window,
        'background_in_window': background_in_window,
        'snr': snr,
        'significance': significance
    }

def main():
    setup_logging()
    args = parse_arguments()
    
    # Parse mass window
    mass_min, mass_max = map(float, args.mass_window.split(','))
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load and clean data
    df = load_data(args.input)
    df_clean = clean_data(df)
    
    # Apply quality cuts
    df_filtered, cut_flow = apply_quality_cuts(df_clean)
    
    # Classify events
    df_classified = classify_events(df_filtered, mass_min, mass_max)
    
    # Compute statistics
    stats = compute_statistics(df_classified, mass_min, mass_max)
    
    # Save filtered events
    output_csv = os.path.join(args.output, 'filtered_events.csv')
    df_classified.to_csv(output_csv, index=False)
    
    # Create summary
    summary = {
        'total_events': len(df),
        'events_after_cleaning': len(df_clean),
        'events_after_cuts': len(df_classified),
        'signal_events': stats['signal_count'],
        'background_events': stats['background_count'],
        'signal_in_window': stats['signal_in_window'],
        'background_in_window': stats['background_in_window'],
        'significance': stats['significance'],
        'cut_flow': cut_flow
    }
    
    # Save summary
    summary_file = os.path.join(args.output, 'event_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    signal_fraction = stats['signal_count'] / len(df_classified) if len(df_classified) > 0 else 0
    print(f"Events before cuts: {len(df)}")
    print(f"Events after cleaning: {len(df_clean)}")
    print(f"Events after cuts: {len(df_classified)}")
    print(f"Signal events in window: {stats['signal_in_window']}")
    print(f"Background events in window: {stats['background_in_window']}")
    print(f"Signal fraction: {signal_fraction:.3f}")
    print(f"Statistical significance: {stats['significance']:.3f}")

if __name__ == '__main__':
    main()
