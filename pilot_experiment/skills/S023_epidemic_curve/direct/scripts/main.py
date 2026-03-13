#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze disease outbreak case report data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--serial-interval', type=float, default=5.0, 
                       help='Mean generation time in days for R0 estimation (default: 5.0)')
    return parser.parse_args()

def load_and_validate_data(input_file):
    """Load CSV data and validate required columns"""
    try:
        df = pd.read_csv(input_file)
        required_cols = ['case_id', 'onset_date', 'age', 'gender', 'location', 'outcome']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Parse dates and handle errors
        df['onset_date'] = pd.to_datetime(df['onset_date'], errors='coerce')
        df = df.dropna(subset=['onset_date'])  # Remove invalid dates
        
        if len(df) < 10:
            raise ValueError("Insufficient data: need at least 10 valid cases")
        
        return df
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")

def generate_epidemic_curve(df):
    """Generate daily and cumulative case counts"""
    # Group by onset date and count cases
    daily_cases = df.groupby('onset_date').size().reset_index(name='daily_cases')
    daily_cases = daily_cases.sort_values('onset_date')
    
    # Fill missing dates with zero cases
    date_range = pd.date_range(start=daily_cases['onset_date'].min(), 
                              end=daily_cases['onset_date'].max(), freq='D')
    full_range = pd.DataFrame({'onset_date': date_range})
    daily_cases = full_range.merge(daily_cases, on='onset_date', how='left').fillna(0)
    
    # Calculate cumulative cases
    daily_cases['cumulative_cases'] = daily_cases['daily_cases'].cumsum()
    daily_cases['date'] = daily_cases['onset_date'].dt.strftime('%Y-%m-%d')
    
    return daily_cases[['date', 'daily_cases', 'cumulative_cases']]

def estimate_r0_and_growth_rate(epidemic_curve, serial_interval):
    """Estimate R0 using exponential growth method"""
    cumulative_cases = epidemic_curve['cumulative_cases'].values
    
    # Use first 30% of outbreak duration for early growth phase
    early_phase_length = max(5, int(0.3 * len(cumulative_cases)))  # Minimum 5 points
    early_cases = cumulative_cases[:early_phase_length]
    
    # Fit exponential model: log(cases) = rt + constant
    days = np.arange(len(early_cases))
    log_cases = np.log(early_cases + 1)  # Add 1 to avoid log(0)
    
    # Remove any infinite or NaN values
    valid_mask = np.isfinite(log_cases)
    if np.sum(valid_mask) < 3:
        raise ValueError("Insufficient valid data points for growth rate estimation")
    
    slope, intercept = np.polyfit(days[valid_mask], log_cases[valid_mask], 1)
    growth_rate = slope
    
    # Calculate R0 and doubling time
    R0 = 1 + growth_rate * serial_interval
    doubling_time = np.log(2) / growth_rate if growth_rate > 0 else float('inf')
    
    return R0, growth_rate, doubling_time

def calculate_cfr_by_age(df):
    """Calculate Case Fatality Rate by age groups"""
    # Define age bins
    age_bins = [0, 18, 40, 60, float('inf')]
    age_labels = ['0-18', '19-40', '41-60', '61+']
    
    # Clean age data
    df_clean = df.dropna(subset=['age', 'outcome'])
    df_clean = df_clean[df_clean['age'] >= 0]  # Remove negative ages
    
    # Create age groups
    df_clean['age_group'] = pd.cut(df_clean['age'], bins=age_bins, labels=age_labels, right=False)
    
    # Calculate CFR by age group
    cfr_by_age = {}
    for age_group in age_labels:
        group_data = df_clean[df_clean['age_group'] == age_group]
        if len(group_data) > 0:
            deaths = len(group_data[group_data['outcome'] == 'deceased'])
            total_cases = len(group_data)
            cfr_by_age[age_group] = deaths / total_cases
        else:
            cfr_by_age[age_group] = 0.0
    
    return cfr_by_age

def calculate_attack_rate_by_location(df):
    """Calculate attack rate (case count) by location"""
    location_counts = df['location'].value_counts().to_dict()
    return location_counts

def main():
    args = parse_arguments()
    
    try:
        # Create output directory
        os.makedirs(args.output, exist_ok=True)
        
        # Load and validate data
        print("Loading case report data...")
        df = load_and_validate_data(args.input)
        print(f"Loaded {len(df)} valid cases")
        
        # Generate epidemic curve
        print("Generating epidemic curve...")
        epidemic_curve = generate_epidemic_curve(df)
        
        # Find peak date
        peak_idx = epidemic_curve['daily_cases'].idxmax()
        peak_date = epidemic_curve.iloc[peak_idx]['date']
        
        # Estimate R0 and growth parameters
        print("Estimating R0 and growth rate...")
        R0, growth_rate, doubling_time = estimate_r0_and_growth_rate(epidemic_curve, args.serial_interval)
        
        # Calculate CFR by age group
        print("Calculating case fatality rates...")
        cfr_by_age = calculate_cfr_by_age(df)
        
        # Calculate attack rate by location
        attack_rate_by_location = calculate_attack_rate_by_location(df)
        
        # Calculate overall statistics
        total_cases = len(df)
        total_deaths = len(df[df['outcome'] == 'deceased'])
        overall_cfr = total_deaths / total_cases if total_cases > 0 else 0.0
        
        # Save epidemic curve
        epi_curve_path = os.path.join(args.output, 'epi_curve.csv')
        epidemic_curve.to_csv(epi_curve_path, index=False)
        print(f"Epidemic curve saved to {epi_curve_path}")
        
        # Prepare analysis results
        analysis_results = {
            'R0': float(R0),
            'peak_date': peak_date,
            'CFR_by_age': cfr_by_age,
            'total_cases': int(total_cases),
            'doubling_time': float(doubling_time),
            'growth_rate': float(growth_rate),
            'attack_rate_by_location': attack_rate_by_location
        }
        
        # Save analysis results
        analysis_path = os.path.join(args.output, 'analysis.json')
        with open(analysis_path, 'w') as f:
            json.dump(analysis_results, f, indent=2)
        print(f"Analysis results saved to {analysis_path}")
        
        # Print summary
        print("\n=== OUTBREAK ANALYSIS SUMMARY ===")
        print(f"R0 estimate: {R0:.2f}")
        print(f"Peak date: {peak_date}")
        print(f"Overall CFR: {overall_cfr:.1%}")
        print(f"Total cases: {total_cases}")
        print(f"Doubling time: {doubling_time:.1f} days")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
