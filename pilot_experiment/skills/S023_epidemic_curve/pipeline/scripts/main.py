import argparse
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import math
from scipy import stats

def validate_input_data(df):
    """Validate that the input DataFrame has all required columns and valid data"""
    required_columns = ['case_id', 'onset_date', 'age', 'gender', 'location', 'outcome']
    
    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    print(f"✓ All required columns present: {required_columns}")
    
    # Check for empty dataframe
    if len(df) == 0:
        raise ValueError("Input file contains no data rows")
    
    # Validate onset_date format
    try:
        df['onset_date'] = pd.to_datetime(df['onset_date'])
    except Exception as e:
        raise ValueError(f"Invalid date format in onset_date column. Expected YYYY-MM-DD format. Error: {e}")
    
    # Check for missing onset dates
    missing_dates = df['onset_date'].isna().sum()
    if missing_dates > 0:
        print(f"Warning: {missing_dates} rows have missing onset_date and will be excluded")
        df = df.dropna(subset=['onset_date'])
    
    # Validate age column
    if not pd.api.types.is_numeric_dtype(df['age']):
        try:
            df['age'] = pd.to_numeric(df['age'], errors='coerce')
        except:
            raise ValueError("Age column contains non-numeric values")
    
    invalid_ages = df['age'].isna().sum()
    if invalid_ages > 0:
        print(f"Warning: {invalid_ages} rows have invalid/missing age values")
    
    # Validate outcome column
    valid_outcomes = {'recovered', 'deceased', 'hospitalized'}
    invalid_outcomes = df[~df['outcome'].isin(valid_outcomes)]['outcome'].unique()
    if len(invalid_outcomes) > 0:
        print(f"Warning: Found invalid outcome values: {invalid_outcomes}")
        print(f"Expected: {valid_outcomes}")
    
    print(f"✓ Data validation complete. {len(df)} valid records found")
    return df

def build_epidemic_curve(df):
    # Create date range to fill in missing dates with zero cases
    date_range = pd.date_range(start=df['onset_date'].min(), 
                              end=df['onset_date'].max(), 
                              freq='D')
    
    daily_cases = df.groupby('onset_date').size().reset_index()
    daily_cases.columns = ['date', 'daily_cases']
    
    # Create complete date series
    complete_series = pd.DataFrame({'date': date_range})
    daily_cases = complete_series.merge(daily_cases, on='date', how='left')
    daily_cases['daily_cases'] = daily_cases['daily_cases'].fillna(0)
    
    daily_cases = daily_cases.sort_values('date')
    daily_cases['cumulative_cases'] = daily_cases['daily_cases'].cumsum()
    
    return daily_cases

def calculate_r0(epi_curve, serial_interval):
    # Use first 30% of outbreak duration for exponential growth fitting
    total_days = len(epi_curve)
    early_phase_days = max(int(total_days * 0.3), 5)  # At least 5 days
    
    early_data = epi_curve.head(early_phase_days).copy()
    
    # Filter out zero cumulative cases (can't take log of 0)
    early_data = early_data[early_data['cumulative_cases'] > 0]
    
    if len(early_data) < 3:
        print("Warning: Insufficient data points for R0 calculation (need at least 3 time points)")
        return None, 0.0, float('inf')
    
    # Check for single-day outbreak (no time variation)
    if len(early_data) == 1:
        print("Warning: All cases occurred on a single day - cannot calculate R0")
        return None, 0.0, float('inf')
    
    early_data = early_data.reset_index()
    days = early_data['index'].values  # Preserve original time spacing
    cumulative_cases = early_data['cumulative_cases'].values
    
    # Check if there's any time variation
    if len(np.unique(days)) < 2:
        print("Warning: No time variation in case data - cannot calculate R0")
        return None, 0.0, float('inf')
    
    # Check if there's any case count variation
    if len(np.unique(cumulative_cases)) < 2:
        print("Warning: No variation in cumulative cases over time - cannot calculate R0")
        return None, 0.0, float('inf')
    
    # Check for any remaining invalid values
    if np.any(cumulative_cases <= 0) or np.any(np.isnan(cumulative_cases)):
        print("Warning: Invalid case counts found")
        return None, 0.0, float('inf')
    
    # Fit exponential: ln(cases) = ln(a) + r*t
    log_cases = np.log(cumulative_cases)
    
    # Check if log transformation was successful
    if np.any(np.isnan(log_cases)) or np.any(np.isinf(log_cases)):
        print("Warning: Log transformation failed")
        return None, 0.0, float('inf')
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(days, log_cases)
    
    # Check for poor fit
    if r_value**2 < 0.5:
        print(f"Warning: Poor exponential fit (R² = {r_value**2:.3f}) - R0 estimate may be unreliable")
    
    growth_rate = slope
    doubling_time = math.log(2) / growth_rate if growth_rate > 0 else float('inf')
    R0 = 1 + growth_rate * serial_interval
    
    print(f"Debug: Growth rate = {growth_rate:.4f} per day, R² = {r_value**2:.3f}")
    
    return R0, growth_rate, doubling_time

def calculate_cfr_by_age(df):
    # Define age bins - using right=False to include left edge, exclude right
    df = df.copy()  # Don't modify original dataframe
    df['age_group'] = pd.cut(df['age'], bins=[0, 19, 41, 61, float('inf')], 
                            labels=['0-18', '19-40', '41-60', '61+'], 
                            right=False, include_lowest=True)
    
    cfr_by_age = {}
    for age_group in ['0-18', '19-40', '41-60', '61+']:
        group_data = df[df['age_group'] == age_group]
        deaths = len(group_data[group_data['outcome'] == 'deceased'])
        total = len(group_data)
        
        if total > 0:
            cfr = deaths / total
            cfr_by_age[age_group] = cfr
            print(f"Debug: Age group {age_group}: {deaths} deaths out of {total} cases (CFR: {cfr:.3f})")
        else:
            cfr_by_age[age_group] = 0.0
            print(f"Debug: Age group {age_group}: No cases")
    
    return cfr_by_age

def calculate_case_distribution_by_location(df):
    """Calculate case counts and proportions by location"""
    location_counts = df['location'].value_counts()
    total_cases = len(df)
    
    distribution = {}
    for location, count in location_counts.items():
        distribution[location] = {
            'cases': int(count),
            'proportion': count / total_cases
        }
    
    return distribution

def perform_analysis(df, epi_curve, serial_interval):
    # Calculate R0
    R0, growth_rate, doubling_time = calculate_r0(epi_curve, serial_interval)
    
    # Find peak date
    peak_idx = epi_curve['daily_cases'].idxmax()
    peak_date = epi_curve.loc[peak_idx, 'date']
    
    # Calculate CFR by age groups
    cfr_by_age = calculate_cfr_by_age(df)
    
    # Calculate case distribution by location (not attack rate)
    case_distribution_by_location = calculate_case_distribution_by_location(df)
    
    # Calculate overall CFR
    total_deaths = len(df[df['outcome'] == 'deceased'])
    total_cases = len(df)
    overall_cfr = total_deaths / total_cases if total_cases > 0 else 0.0
    
    return {
        'R0': R0,
        'growth_rate': growth_rate,
        'doubling_time': doubling_time,
        'peak_date': peak_date,
        'total_cases': total_cases,
        'overall_CFR': overall_cfr,
        'CFR_by_age': cfr_by_age,
        'case_distribution_by_location': case_distribution_by_location
    }

def main():
    parser = argparse.ArgumentParser(description='Analyze disease outbreak case report data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--serial-interval', type=float, default=5.0, 
                       help='Serial interval in days (default: 5.0)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Read and validate data
    try:
        print(f"Reading data from: {args.input}")
        df = pd.read_csv(args.input)
        print(f"Loaded {len(df)} rows from CSV")
        
        # Validate input data structure and content
        df = validate_input_data(df)
        
        if len(df) == 0:
            print("Error: No valid data remaining after validation")
            return
            
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found")
        return
    except ValueError as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"Error reading/validating CSV file: {e}")
        return
    
    # Build epidemic curve
    epi_curve = build_epidemic_curve(df)
    epi_curve.to_csv(os.path.join(args.output, 'epi_curve.csv'), index=False)
    
    # Calculate analysis metrics
    analysis = perform_analysis(df, epi_curve, args.serial_interval)
    
    # Save analysis results
    with open(os.path.join(args.output, 'analysis.json'), 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    # Print summary
    r0_str = f"{analysis['R0']:.2f}" if analysis['R0'] is not None else "Unable to calculate"
    print(f"\n=== OUTBREAK ANALYSIS RESULTS ===")
    print(f"R0 estimate: {r0_str}")
    print(f"Peak date: {analysis['peak_date']}")
    print(f"Overall CFR: {analysis['overall_CFR']:.3f}")
    print(f"Total cases: {analysis['total_cases']}")
    
    if analysis['doubling_time'] != float('inf'):
        print(f"Doubling time: {analysis['doubling_time']:.1f} days")
    else:
        print("Doubling time: Unable to calculate")

if __name__ == "__main__":
    main()
