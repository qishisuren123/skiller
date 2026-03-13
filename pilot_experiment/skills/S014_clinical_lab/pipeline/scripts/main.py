#!/usr/bin/env python3
import argparse
import csv
import json
from datetime import datetime
from typing import Dict, List, Any

def normalize_value(value: float, test_name: str, unit: str) -> float:
    """Normalize lab values to SI units"""
    if test_name.lower().strip() == 'glucose' and unit.lower().strip() == 'mg/dl':
        return value * 0.0555  # Convert to mmol/L
    elif test_name.lower().strip() == 'creatinine' and unit.lower().strip() == 'mg/dl':
        return value * 88.4  # Convert to μmol/L
    return value  # No conversion needed

def normalize_reference(ref_value: float, test_name: str, unit: str) -> float:
    """Normalize reference ranges to match normalized values"""
    if test_name.lower().strip() == 'glucose' and unit.lower().strip() == 'mg/dl':
        return ref_value * 0.0555  # Convert to mmol/L
    elif test_name.lower().strip() == 'creatinine' and unit.lower().strip() == 'mg/dl':
        return ref_value * 88.4  # Convert to μmol/L
    return ref_value  # No conversion needed

def get_normalized_unit(test_name: str, original_unit: str) -> str:
    """Get the normalized unit for display"""
    if test_name.lower().strip() == 'glucose' and original_unit.lower().strip() == 'mg/dl':
        return 'mmol/L'
    elif test_name.lower().strip() == 'creatinine' and original_unit.lower().strip() == 'mg/dl':
        return 'μmol/L'
    return original_unit

def flag_result(value: float, ref_low: float, ref_high: float) -> str:
    """Flag results as normal, low, or high"""
    if value < ref_low:
        return "low"
    elif value > ref_high:
        return "high"
    return "normal"

def is_critical(value: float, ref_low: float, ref_high: float) -> bool:
    """Check if result is critical (>2x outside reference range)"""
    return value < (ref_low * 0.5) or value > (ref_high * 2.0)

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse timestamp with flexible format handling"""
    timestamp_str = timestamp_str.strip()
    formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse timestamp: {timestamp_str}")

def process_lab_results(input_file: str, output_file: str, flag_output: str):
    """Main processing function"""
    results = []
    patient_summary = {}
    error_count = 0
    
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            try:
                # Strip whitespace from all values
                patient_id = row['patient_id'].strip()
                test_name = row['test_name'].strip()
                value = float(row['value'].strip())
                unit = row['unit'].strip()
                ref_low = float(row['reference_low'].strip())
                ref_high = float(row['reference_high'].strip())
                timestamp = row['timestamp'].strip()
                
                # Validate data
                if not patient_id or not test_name:
                    raise ValueError("Missing patient_id or test_name")
                if ref_low >= ref_high:
                    raise ValueError(f"Invalid reference range: {ref_low} >= {ref_high}")
                
                # Normalize value and reference ranges
                normalized_value = normalize_value(value, test_name, unit)
                normalized_ref_low = normalize_reference(ref_low, test_name, unit)
                normalized_ref_high = normalize_reference(ref_high, test_name, unit)
                normalized_unit = get_normalized_unit(test_name, unit)
                
                # Flag result using normalized values and normalized reference ranges
                flag = flag_result(normalized_value, normalized_ref_low, normalized_ref_high)
                critical = is_critical(normalized_value, normalized_ref_low, normalized_ref_high)
                
                # Add to results with both original and normalized data
                result_row = {
                    'patient_id': patient_id,
                    'test_name': test_name,
                    'original_value': value,
                    'original_unit': unit,
                    'original_ref_low': ref_low,
                    'original_ref_high': ref_high,
                    'normalized_value': round(normalized_value, 4),
                    'normalized_unit': normalized_unit,
                    'normalized_ref_low': round(normalized_ref_low, 4),
                    'normalized_ref_high': round(normalized_ref_high, 4),
                    'timestamp': timestamp,
                    'flag': flag,
                    'is_critical': critical
                }
                results.append(result_row)
                
                # Update patient summary
                if patient_id not in patient_summary:
                    patient_summary[patient_id] = {
                        'n_abnormal': 0,
                        'n_critical': 0,
                        'tests': [],
                        'most_recent': timestamp
                    }
                
                # Update most recent date
                current_date = parse_timestamp(timestamp)
                most_recent_date = parse_timestamp(patient_summary[patient_id]['most_recent'])
                if current_date > most_recent_date:
                    patient_summary[patient_id]['most_recent'] = timestamp
                
                if flag != 'normal':
                    patient_summary[patient_id]['n_abnormal'] += 1
                if critical:
                    patient_summary[patient_id]['n_critical'] += 1
                
                patient_summary[patient_id]['tests'].append({
                    'test_name': test_name,
                    'flag': flag,
                    'is_critical': critical,
                    'timestamp': timestamp
                })
                
            except (ValueError, KeyError) as e:
                error_count += 1
                print(f"Warning: Skipping row {row_num} due to error: {e}")
                continue
            except Exception as e:
                error_count += 1
                print(f"Warning: Unexpected error in row {row_num}: {e}")
                continue
    
    # Write output CSV
    with open(output_file, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    # Write flag summary JSON
    with open(flag_output, 'w') as f:
        json.dump(patient_summary, f, indent=2)
    
    # Print statistics
    total_patients = len(patient_summary)
    total_tests = len(results)
    abnormal_tests = sum(1 for r in results if r['flag'] != 'normal')
    critical_tests = sum(1 for r in results if r['is_critical'])
    
    print(f"Total patients: {total_patients}")
    print(f"Total tests processed: {total_tests}")
    print(f"Abnormal rate: {abnormal_tests/total_tests:.2%}")
    print(f"Critical rate: {critical_tests/total_tests:.2%}")
    print(f"Errors encountered: {error_count}")

def main():
    parser = argparse.ArgumentParser(description='Normalize and flag clinical lab results')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output CSV file')
    parser.add_argument('--flag-output', required=True, help='Flag summary JSON file')
    
    args = parser.parse_args()
    process_lab_results(args.input, args.output, args.flag_output)

if __name__ == '__main__':
    main()
