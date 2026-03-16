#!/usr/bin/env python3
import argparse
import pandas as pd
import json
from datetime import datetime
import logging
import numpy as np

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def normalize_values_vectorized(df):
    """Vectorized normalization of values and reference ranges to SI units"""
    # Create copies to avoid modifying original
    normalized_value = df['value'].copy()
    normalized_ref_low = df['reference_low'].copy()
    normalized_ref_high = df['reference_high'].copy()
    
    # Create boolean masks for different test types
    glucose_mask = df['test_name'].str.contains('glucose', case=False, na=False) & (df['unit'] == 'mg/dL')
    creatinine_mask = df['test_name'].str.contains('creatinine', case=False, na=False) & (df['unit'] == 'mg/dL')
    
    # Apply conversions using vectorized operations
    # Glucose: mg/dL to mmol/L
    normalized_value.loc[glucose_mask] = normalized_value.loc[glucose_mask] * 0.0555
    normalized_ref_low.loc[glucose_mask] = normalized_ref_low.loc[glucose_mask] * 0.0555
    normalized_ref_high.loc[glucose_mask] = normalized_ref_high.loc[glucose_mask] * 0.0555
    
    # Creatinine: mg/dL to μmol/L
    normalized_value.loc[creatinine_mask] = normalized_value.loc[creatinine_mask] * 88.4
    normalized_ref_low.loc[creatinine_mask] = normalized_ref_low.loc[creatinine_mask] * 88.4
    normalized_ref_high.loc[creatinine_mask] = normalized_ref_high.loc[creatinine_mask] * 88.4
    
    return normalized_value, normalized_ref_low, normalized_ref_high

def flag_results_vectorized(values, ref_low, ref_high):
    """Vectorized flagging of results"""
    # Initialize all as 'unknown'
    flags = pd.Series(['unknown'] * len(values), index=values.index)
    
    # Create mask for valid (non-NaN) values
    valid_mask = ~(pd.isna(values) | pd.isna(ref_low) | pd.isna(ref_high))
    
    # Apply flags only to valid values
    valid_values = values[valid_mask]
    valid_ref_low = ref_low[valid_mask]
    valid_ref_high = ref_high[valid_mask]
    
    flags.loc[valid_mask & (valid_values < valid_ref_low)] = 'low'
    flags.loc[valid_mask & (valid_values > valid_ref_high)] = 'high'
    flags.loc[valid_mask & (valid_values >= valid_ref_low) & (valid_values <= valid_ref_high)] = 'normal'
    
    return flags

def is_critical_vectorized(values, ref_low, ref_high):
    """Vectorized critical value checking"""
    # Initialize all as False
    critical = pd.Series([False] * len(values), index=values.index)
    
    # Create mask for valid values
    valid_mask = ~(pd.isna(values) | pd.isna(ref_low) | pd.isna(ref_high))
    
    # Apply critical logic only to valid values
    valid_values = values[valid_mask]
    valid_ref_low = ref_low[valid_mask]
    valid_ref_high = ref_high[valid_mask]
    
    # Critical high: > 2x upper reference limit
    # Critical low: < 0.5x lower reference limit
    critically_high = valid_values > 2 * valid_ref_high
    critically_low = valid_values < 0.5 * valid_ref_low
    
    critical.loc[valid_mask] = critically_high | critically_low
    
    return critical

def process_lab_data(input_file, output_file, flag_output):
    """Main processing function"""
    logging.info("Reading input CSV...")
    df = pd.read_csv(input_file)
    
    # Convert timestamp to datetime
    logging.info("Converting timestamps...")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Log missing data statistics
    missing_values = df['value'].isna().sum()
    missing_ref_low = df['reference_low'].isna().sum()
    missing_ref_high = df['reference_high'].isna().sum()
    
    logging.info(f"Missing values: {missing_values}, Missing ref_low: {missing_ref_low}, Missing ref_high: {missing_ref_high}")
    
    # Log unique test names for debugging
    unique_tests = df['test_name'].unique()
    logging.info(f"Found {len(unique_tests)} unique test types")
    
    # Vectorized normalization of values AND reference ranges
    logging.info("Normalizing values and reference ranges...")
    df['normalized_value'], df['normalized_ref_low'], df['normalized_ref_high'] = normalize_values_vectorized(df)
    
    # Log conversion statistics
    glucose_tests = df[df['test_name'].str.contains('glucose', case=False, na=False)]
    creatinine_tests = df[df['test_name'].str.contains('creatinine', case=False, na=False)]
    logging.info(f"Glucose tests found: {len(glucose_tests)}, Creatinine tests found: {len(creatinine_tests)}")
    
    # Vectorized flagging using normalized reference ranges
    logging.info("Flagging results...")
    df['flag'] = flag_results_vectorized(df['normalized_value'], df['normalized_ref_low'], df['normalized_ref_high'])
    
    # Vectorized critical checking using normalized reference ranges
    logging.info("Checking critical values...")
    df['is_critical'] = is_critical_vectorized(df['normalized_value'], df['normalized_ref_low'], df['normalized_ref_high'])
    
    # Debug: Log some critical value examples
    critical_results = df[df['is_critical'] == True]
    if len(critical_results) > 0:
        logging.info(f"Found {len(critical_results)} critical results")
        # Show a few examples
        for idx, row in critical_results.head(3).iterrows():
            logging.info(f"Critical example: {row['test_name']} = {row['normalized_value']:.2f}, normalized ref: {row['normalized_ref_low']:.2f}-{row['normalized_ref_high']:.2f}")
    
    # Save normalized CSV
    logging.info("Saving normalized CSV...")
    df.to_csv(output_file, index=False)
    
    # Generate summary statistics using groupby for better performance
    logging.info("Generating patient summaries...")
    patient_summary = {}
    
    # Group by patient for efficient processing
    for patient_id, patient_data in df.groupby('patient_id'):
        flaggable_data = patient_data[patient_data['flag'] != 'unknown']
        n_abnormal = int(len(flaggable_data[flaggable_data['flag'] != 'normal']))
        n_critical = int(patient_data['is_critical'].sum())
        most_recent_date = patient_data['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')
        
        patient_summary[str(patient_id)] = {
            'n_abnormal': n_abnormal,
            'n_critical': n_critical,
            'most_recent_test': most_recent_date,
            'tests': patient_data[['test_name', 'flag', 'is_critical']].to_dict('records')
        }
    
    # Save flag summary JSON
    logging.info("Saving flag summary JSON...")
    with open(flag_output, 'w') as f:
        json.dump(patient_summary, f, indent=2, default=str)
    
    # Print summary statistics
    total_patients = len(df['patient_id'].unique())
    total_tests = len(df)
    flaggable_tests = len(df[df['flag'] != 'unknown'])
    abnormal_rate = len(df[df['flag'].isin(['low', 'high'])]) / flaggable_tests if flaggable_tests > 0 else 0
    critical_rate = df['is_critical'].sum() / total_tests
    
    print(f"Total patients: {total_patients}")
    print(f"Total tests: {total_tests}")
    print(f"Flaggable tests: {flaggable_tests}")
    print(f"Abnormal rate: {abnormal_rate:.2%}")
    print(f"Critical rate: {critical_rate:.2%}")

def main():
    parser = argparse.ArgumentParser(description='Normalize and flag clinical laboratory test results')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output CSV file')
    parser.add_argument('--flag-output', required=True, help='Flag summary JSON file')
    
    args = parser.parse_args()
    
    setup_logging()
    process_lab_data(args.input, args.output, args.flag_output)

if __name__ == '__main__':
    main()
