#!/usr/bin/env python3
import argparse
import json
import numpy as np
from datetime import datetime, timedelta
import logging

def parse_precipitation_data(data_string, start_year=2000):
    """Parse comma-separated precipitation data into daily values with dates"""
    # Split by comma and clean each value
    raw_values = data_string.split(',')
    values = []
    
    for x in raw_values:
        try:
            # Strip whitespace and newlines, then convert to float
            cleaned = x.strip()
            if cleaned:  # Skip empty strings
                val = float(cleaned)
                values.append(val if val >= 0 else np.nan)
            else:
                values.append(np.nan)
        except ValueError:
            # If conversion fails, treat as missing data
            values.append(np.nan)
    
    # Create date range starting from January 1st of start_year
    start_date = datetime(start_year, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(len(values))]
    
    return dates, values

def extract_annual_maxima(dates, precip_values):
    """Extract maximum daily precipitation for each complete year"""
    # Group data by year
    yearly_data = {}
    for date, precip in zip(dates, precip_values):
        if not np.isnan(precip):  # Skip missing data
            year = date.year
            if year not in yearly_data:
                yearly_data[year] = []
            yearly_data[year].append(precip)
    
    # Extract annual maxima for complete years only
    annual_maxima = {}
    for year, values in yearly_data.items():
        # Consider year complete if it has at least 300 days of data
        if len(values) >= 300:
            annual_maxima[year] = float(max(values))
    
    return annual_maxima

def calculate_return_periods(annual_maxima):
    """Calculate return periods using Weibull plotting position"""
    values = list(annual_maxima.values())
    years = list(annual_maxima.keys())
    
    # Sort values in descending order and get ranks
    sorted_indices = np.argsort(values)[::-1]
    n = len(values)
    
    return_periods = {}
    for rank, idx in enumerate(sorted_indices, 1):
        year = years[idx]
        value = values[idx]
        return_period = (n + 1) / rank
        return_periods[int(year)] = {
            'value': float(value),
            'return_period': float(return_period)
        }
    
    return return_periods

def linear_interpolate(x, x1, y1, x2, y2):
    """Manual linear interpolation between two points"""
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

def calculate_threshold_for_return_period(return_periods, target_return_period):
    """Calculate precipitation threshold for a specific return period using interpolation/extrapolation"""
    # Extract return periods and corresponding precipitation values
    rp_values = []
    precip_values = []
    
    for year_data in return_periods.values():
        rp_values.append(year_data['return_period'])
        precip_values.append(year_data['value'])
    
    # Sort by return period (ascending)
    sorted_pairs = sorted(zip(rp_values, precip_values))
    rp_sorted = [pair[0] for pair in sorted_pairs]
    precip_sorted = [pair[1] for pair in sorted_pairs]
    
    # Handle edge cases with extrapolation
    if target_return_period <= min(rp_sorted):
        # Target is smaller than minimum - return corresponding minimum precipitation
        return min(precip_sorted)
    elif target_return_period >= max(rp_sorted):
        # Target exceeds maximum - extrapolate using last two points
        if len(rp_sorted) >= 2:
            return linear_interpolate(
                target_return_period,
                rp_sorted[-2], precip_sorted[-2],
                rp_sorted[-1], precip_sorted[-1]
            )
        else:
            return max(precip_sorted)
    
    # Find the two points to interpolate between
    for i in range(len(rp_sorted) - 1):
        if rp_sorted[i] <= target_return_period <= rp_sorted[i + 1]:
            # Linear interpolation between points i and i+1
            return linear_interpolate(
                target_return_period,
                rp_sorted[i], precip_sorted[i],
                rp_sorted[i + 1], precip_sorted[i + 1]
            )
    
    # Fallback
    return max(precip_sorted)

def identify_extreme_events(dates, precip_values, threshold):
    """Identify extreme events exceeding the threshold"""
    extreme_events = []
    for date, precip in zip(dates, precip_values):
        if not np.isnan(precip) and precip >= threshold:
            extreme_events.append({
                'date': date.strftime('%Y-%m-%d'),
                'precipitation': float(precip)
            })
    return extreme_events

def main():
    parser = argparse.ArgumentParser(description='Rainfall Return Period Analysis')
    parser.add_argument('--input-data', required=True, 
                       help='Comma-separated daily precipitation values (mm/day)')
    parser.add_argument('--output', required=True,
                       help='Output JSON file path')
    parser.add_argument('--start-year', type=int, default=2000,
                       help='Starting year for the time series (default: 2000)')
    
    args = parser.parse_args()
    
    # Parse input data
    dates, precip_values = parse_precipitation_data(args.input_data, args.start_year)
    
    # Extract annual maxima
    annual_maxima = extract_annual_maxima(dates, precip_values)
    
    # Calculate return periods
    return_periods = calculate_return_periods(annual_maxima)
    
    # Calculate 10-year return period threshold using interpolation/extrapolation
    ten_year_threshold = calculate_threshold_for_return_period(return_periods, 10.0)
    
    # Identify extreme events
    extreme_events = identify_extreme_events(dates, precip_values, ten_year_threshold)
    
    # Basic statistics
    valid_precip = [p for p in precip_values if not np.isnan(p)]
    stats = {
        'mean_annual_maximum': float(np.mean(list(annual_maxima.values()))),
        'std_annual_maximum': float(np.std(list(annual_maxima.values()))),
        'precip_95th_percentile': float(np.percentile(valid_precip, 95))
    }
    
    # Prepare output
    results = {
        'annual_maxima': {int(k): float(v) for k, v in annual_maxima.items()},
        'return_periods': return_periods,
        'extreme_events': extreme_events,
        'statistics': stats,
        'ten_year_threshold': float(ten_year_threshold)
    }
    
    # Save to JSON
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis complete. Results saved to {args.output}")
    print(f"10-year return period threshold: {ten_year_threshold:.2f} mm/day")
    print(f"Found {len(extreme_events)} extreme events")

if __name__ == "__main__":
    main()
