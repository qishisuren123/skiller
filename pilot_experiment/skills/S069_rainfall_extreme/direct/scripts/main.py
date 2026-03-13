import argparse
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def parse_precipitation_data(data_string, start_year):
    """Parse comma-separated precipitation data and create date index."""
    precip_values = np.array([float(x) for x in data_string.split(',')])
    
    # Filter out missing data (negative values)
    valid_mask = precip_values >= 0
    
    # Create date range
    start_date = datetime(start_year, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(len(precip_values))]
    
    return precip_values, dates, valid_mask

def extract_annual_maxima(precip_data, dates, valid_mask):
    """Extract annual maximum precipitation for complete years."""
    # Create DataFrame with valid data only
    valid_precip = precip_data[valid_mask]
    valid_dates = np.array(dates)[valid_mask]
    
    df = pd.DataFrame({
        'precip': valid_precip,
        'date': pd.to_datetime(valid_dates)
    })
    
    df['year'] = df['date'].dt.year
    
    # Count days per year to identify complete years
    days_per_year = df.groupby('year').size()
    complete_years = days_per_year[days_per_year >= 365].index
    
    # Filter to complete years only
    df_complete = df[df['year'].isin(complete_years)]
    
    # Extract annual maxima
    annual_maxima = df_complete.groupby('year')['precip'].max()
    
    return annual_maxima.values, complete_years.tolist()

def calculate_return_periods(annual_maxima):
    """Calculate return periods using Weibull plotting position."""
    n = len(annual_maxima)
    
    # Sort in descending order and assign ranks
    sorted_indices = np.argsort(annual_maxima)[::-1]
    sorted_maxima = annual_maxima[sorted_indices]
    ranks = np.arange(1, n + 1)
    
    # Weibull plotting position formula
    return_periods = (n + 1) / ranks
    
    return sorted_maxima, return_periods

def find_return_period_threshold(sorted_maxima, return_periods, target_period):
    """Find precipitation threshold for a given return period using interpolation."""
    if target_period <= return_periods[-1]:
        # Interpolate within observed range
        threshold = np.interp(target_period, return_periods[::-1], sorted_maxima[::-1])
    elif target_period >= return_periods[0]:
        # Extrapolate beyond observed range
        threshold = np.interp(target_period, return_periods[::-1], sorted_maxima[::-1])
    else:
        # Linear interpolation
        threshold = np.interp(target_period, return_periods[::-1], sorted_maxima[::-1])
    
    return threshold

def identify_extreme_events(precip_data, dates, valid_mask, threshold):
    """Identify all daily events exceeding the threshold."""
    extreme_events = []
    
    for i, (precip, date, is_valid) in enumerate(zip(precip_data, dates, valid_mask)):
        if is_valid and precip > threshold:
            extreme_events.append({
                'date': date.strftime('%Y-%m-%d'),
                'precipitation_mm': float(precip)
            })
    
    return extreme_events

def calculate_statistics(annual_maxima, precip_data, valid_mask):
    """Calculate statistical summary."""
    valid_precip = precip_data[valid_mask]
    
    stats = {
        'mean_annual_maximum_mm': float(np.mean(annual_maxima)),
        'std_annual_maximum_mm': float(np.std(annual_maxima, ddof=1)),
        'percentile_95_daily_mm': float(np.percentile(valid_precip, 95)),
        'total_years_analyzed': len(annual_maxima),
        'total_valid_days': len(valid_precip)
    }
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='Analyze rainfall return periods from daily precipitation data')
    parser.add_argument('--input-data', required=True, help='Comma-separated daily precipitation values (mm/day)')
    parser.add_argument('--start-year', type=int, default=2000, help='Starting year for the time series')
    parser.add_argument('--output', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    try:
        # Parse input data
        precip_data, dates, valid_mask = parse_precipitation_data(args.input_data, args.start_year)
        print(f"Loaded {len(precip_data)} daily precipitation records")
        print(f"Valid data points: {np.sum(valid_mask)}")
        
        # Extract annual maxima
        annual_maxima, complete_years = extract_annual_maxima(precip_data, dates, valid_mask)
        
        if len(annual_maxima) < 10:
            print(f"Warning: Only {len(annual_maxima)} complete years available. Results may be unreliable.")
        
        print(f"Extracted annual maxima for {len(annual_maxima)} complete years: {complete_years[0]}-{complete_years[-1]}")
        
        # Calculate return periods
        sorted_maxima, return_periods = calculate_return_periods(annual_maxima)
        
        # Find 10-year return period threshold
        threshold_10yr = find_return_period_threshold(sorted_maxima, return_periods, 10.0)
        print(f"10-year return period threshold: {threshold_10yr:.2f} mm/day")
        
        # Identify extreme events
        extreme_events = identify_extreme_events(precip_data, dates, valid_mask, threshold_10yr)
        print(f"Identified {len(extreme_events)} extreme events exceeding 10-year return period")
        
        # Calculate statistics
        statistics = calculate_statistics(annual_maxima, precip_data, valid_mask)
        
        # Prepare output
        results = {
            'annual_maxima': {
                'values_mm': sorted_maxima.tolist(),
                'return_periods_years': return_periods.tolist(),
                'years_analyzed': complete_years
            },
            'extreme_events': {
                'threshold_10yr_mm': float(threshold_10yr),
                'events': extreme_events
            },
            'statistics': statistics,
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'start_year': args.start_year,
                'method': 'Annual Maximum Series with Weibull plotting position'
            }
        }
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {args.output}")
        print(f"Mean annual maximum: {statistics['mean_annual_maximum_mm']:.2f} mm/day")
        print(f"95th percentile daily precipitation: {statistics['percentile_95_daily_mm']:.2f} mm/day")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
