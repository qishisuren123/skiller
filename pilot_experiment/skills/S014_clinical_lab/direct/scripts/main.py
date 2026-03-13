import argparse
import pandas as pd
import json
from datetime import datetime
import numpy as np

def normalize_lab_value(value, unit, test_name):
    """Normalize lab values to SI units"""
    conversions = {
        ('glucose', 'mg/dl'): 0.0555,  # to mmol/L
        ('glucose', 'mg/dl'): 0.0555,
        ('creatinine', 'mg/dl'): 88.4,  # to μmol/L
    }
    
    key = (test_name.lower().strip(), unit.lower().strip())
    if key in conversions:
        return value * conversions[key]
    return value

def flag_result(normalized_value, reference_low, reference_high):
    """Flag lab result as low, normal, or high"""
    if pd.isna(normalized_value) or pd.isna(reference_low) or pd.isna(reference_high):
        return "unknown"
    
    if normalized_value < reference_low:
        return "low"
    elif normalized_value > reference_high:
        return "high"
    else:
        return "normal"

def is_critical_result(normalized_value, reference_low, reference_high):
    """Check if result is critically abnormal (>2x outside reference)"""
    if pd.isna(normalized_value) or pd.isna(reference_low) or pd.isna(reference_high):
        return False
    
    # Avoid division by zero
    if reference_low == 0 and reference_high == 0:
        return False
    
    if normalized_value < reference_low:
        if reference_low > 0:
            return normalized_value < (reference_low * 0.5)  # 50% below low
        else:
            return abs(normalized_value - reference_low) > abs(reference_low * 2)
    elif normalized_value > reference_high:
        return normalized_value > (reference_high * 2)  # 200% above high
    
    return False

def process_lab_results(input_file, output_file, flag_output_file):
    """Main processing function"""
    
    # Load and validate data
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    required_columns = ['patient_id', 'test_name', 'value', 'unit', 'reference_low', 'reference_high', 'timestamp']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        return
    
    # Convert timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Apply normalization and flagging
    df['normalized_value'] = df.apply(
        lambda row: normalize_lab_value(row['value'], row['unit'], row['test_name']), 
        axis=1
    )
    
    df['flag'] = df.apply(
        lambda row: flag_result(row['normalized_value'], row['reference_low'], row['reference_high']), 
        axis=1
    )
    
    df['is_critical'] = df.apply(
        lambda row: is_critical_result(row['normalized_value'], row['reference_low'], row['reference_high']), 
        axis=1
    )
    
    # Generate patient summaries
    patient_summaries = {}
    
    for patient_id in df['patient_id'].unique():
        patient_data = df[df['patient_id'] == patient_id]
        
        n_abnormal = len(patient_data[patient_data['flag'].isin(['low', 'high'])])
        n_critical = len(patient_data[patient_data['is_critical'] == True])
        most_recent_date = patient_data['timestamp'].max()
        
        tests = []
        for _, row in patient_data.iterrows():
            tests.append({
                'test_name': row['test_name'],
                'value': float(row['normalized_value']) if pd.notna(row['normalized_value']) else None,
                'flag': row['flag'],
                'is_critical': bool(row['is_critical']),
                'timestamp': row['timestamp'].isoformat() if pd.notna(row['timestamp']) else None
            })
        
        patient_summaries[str(patient_id)] = {
            'n_abnormal': int(n_abnormal),
            'n_critical': int(n_critical),
            'most_recent_test': most_recent_date.isoformat() if pd.notna(most_recent_date) else None,
            'tests': tests
        }
    
    # Save outputs
    try:
        df.to_csv(output_file, index=False)
        print(f"Normalized results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving output CSV: {e}")
        return
    
    try:
        with open(flag_output_file, 'w') as f:
            json.dump(patient_summaries, f, indent=2)
        print(f"Flag summary saved to: {flag_output_file}")
    except Exception as e:
        print(f"Error saving flag summary JSON: {e}")
        return
    
    # Print statistics
    total_patients = df['patient_id'].nunique()
    total_tests = len(df)
    abnormal_tests = len(df[df['flag'].isin(['low', 'high'])])
    critical_tests = len(df[df['is_critical'] == True])
    
    abnormal_rate = (abnormal_tests / total_tests * 100) if total_tests > 0 else 0
    critical_rate = (critical_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n=== Processing Summary ===")
    print(f"Total patients: {total_patients}")
    print(f"Total tests: {total_tests}")
    print(f"Abnormal rate: {abnormal_rate:.1f}% ({abnormal_tests}/{total_tests})")
    print(f"Critical rate: {critical_rate:.1f}% ({critical_tests}/{total_tests})")

def main():
    parser = argparse.ArgumentParser(description='Normalize and flag clinical laboratory test results')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--flag-output', required=True, help='Flag summary JSON file path')
    
    args = parser.parse_args()
    
    process_lab_results(args.input, args.output, args.flag_output)

if __name__ == "__main__":
    main()
