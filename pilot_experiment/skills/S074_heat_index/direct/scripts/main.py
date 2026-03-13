#!/usr/bin/env python3
"""
Heat Index Analysis and Heat Wave Detection
Processes temperature and humidity data to detect heat wave events
"""

import argparse
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def calculate_heat_index(temp_f, humidity_pct):
    """Calculate heat index using full NWS formula with adjustments"""
    temp_f = np.asarray(temp_f)
    humidity_pct = np.asarray(humidity_pct)
    
    # Simple formula for temperatures below 80°F
    simple_mask = temp_f < 80
    hi = np.where(simple_mask,
                  0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (humidity_pct * 0.094)),
                  np.nan)
    
    # Rothfusz regression for temperatures >= 80°F
    complex_mask = temp_f >= 80
    hi_complex = (-42.379 + 2.04901523*temp_f + 10.14333127*humidity_pct 
                  - 0.22475541*temp_f*humidity_pct - 6.83783e-3*temp_f**2
                  - 5.481717e-2*humidity_pct**2 + 1.22874e-3*temp_f**2*humidity_pct
                  + 8.5282e-4*temp_f*humidity_pct**2 - 1.99e-6*temp_f**2*humidity_pct**2)
    
    hi = np.where(complex_mask, hi_complex, hi)
    
    # Adjustment for low humidity
    low_humid_mask = (humidity_pct < 13) & (temp_f >= 80) & (temp_f <= 112)
    adjustment1 = ((13 - humidity_pct) / 4) * np.sqrt((17 - np.abs(temp_f - 95)) / 17)
    hi = np.where(low_humid_mask, hi - adjustment1, hi)
    
    # Adjustment for high humidity
    high_humid_mask = (humidity_pct > 85) & (temp_f >= 80) & (temp_f <= 87)
    adjustment2 = ((humidity_pct - 85) / 10) * ((87 - temp_f) / 5)
    hi = np.where(high_humid_mask, hi + adjustment2, hi)
    
    return hi

def build_climatology(data, baseline_years, percentile):
    """Build climatological baseline with 15-day rolling window"""
    baseline_data = data[data.index.year <= (data.index.year.max() - (len(data.index.year.unique()) - baseline_years))]
    
    climatology = {}
    for day_of_year in range(1, 367):  # Include leap day
        # Create 15-day window around target day
        window_days = []
        for offset in range(-7, 8):
            target_day = day_of_year + offset
            if target_day <= 0:
                target_day += 366
            elif target_day > 366:
                target_day -= 366
            window_days.append(target_day)
        
        # Extract data for this window across all years
        window_data = []
        for year in baseline_data.index.year.unique():
            year_data = baseline_data[baseline_data.index.year == year]
            for wd in window_days:
                day_data = year_data[year_data.index.dayofyear == wd]
                if not day_data.empty:
                    window_data.extend(day_data.values)
        
        if len(window_data) > 10:  # Minimum data requirement
            climatology[day_of_year] = np.percentile(window_data, percentile)
        else:
            climatology[day_of_year] = np.nan
    
    return climatology

def detect_heat_waves(heat_index, climatology, min_duration):
    """Detect heat wave events based on climatological thresholds"""
    # Create threshold series
    thresholds = []
    for date in heat_index.index:
        day_of_year = date.dayofyear
        if day_of_year in climatology:
            thresholds.append(climatology[day_of_year])
        else:
            thresholds.append(np.nan)
    
    threshold_series = pd.Series(thresholds, index=heat_index.index)
    
    # Identify exceedances
    exceedances = heat_index > threshold_series
    
    # Find consecutive periods
    heat_waves = []
    in_event = False
    event_start = None
    
    for date, exceeds in exceedances.items():
        if exceeds and not in_event:
            # Start new event
            in_event = True
            event_start = date
        elif not exceeds and in_event:
            # End current event
            event_end = date - timedelta(days=1)
            duration = (event_end - event_start).days + 1
            
            if duration >= min_duration:
                heat_waves.append({
                    'start': event_start,
                    'end': event_end,
                    'duration': duration
                })
            
            in_event = False
    
    # Handle event ending at data end
    if in_event:
        event_end = heat_index.index[-1]
        duration = (event_end - event_start).days + 1
        if duration >= min_duration:
            heat_waves.append({
                'start': event_start,
                'end': event_end,
                'duration': duration
            })
    
    # Merge events separated by single days
    merged_events = []
    for i, event in enumerate(heat_waves):
        if i == 0:
            merged_events.append(event)
        else:
            prev_event = merged_events[-1]
            gap = (event['start'] - prev_event['end']).days - 1
            
            if gap == 1:  # Single day gap
                # Merge events
                merged_events[-1]['end'] = event['end']
                merged_events[-1]['duration'] = (event['end'] - prev_event['start']).days + 1
            else:
                merged_events.append(event)
    
    return merged_events, threshold_series

def analyze_heat_wave_statistics(heat_waves, heat_index, threshold_series):
    """Calculate comprehensive statistics for each heat wave"""
    analyzed_events = []
    
    for event in heat_waves:
        event_data = heat_index[event['start']:event['end']]
        event_threshold = threshold_series[event['start']:event['end']]
        
        stats_dict = {
            'start_date': event['start'].strftime('%Y-%m-%d'),
            'end_date': event['end'].strftime('%Y-%m-%d'),
            'duration': event['duration'],
            'mean_heat_index': float(event_data.mean()),
            'max_heat_index': float(event_data.max()),
            'cumulative_excess_heat': float((event_data - event_threshold).sum()),
            'peak_day': event_data.idxmax().strftime('%Y-%m-%d')
        }
        
        analyzed_events.append(stats_dict)
    
    return analyzed_events

def calculate_return_periods(heat_waves, total_years):
    """Estimate return periods using extreme value statistics"""
    if len(heat_waves) == 0:
        return []
    
    # Extract maximum heat index for each event
    max_intensities = [event['max_heat_index'] for event in heat_waves]
    
    # Fit Gumbel distribution
    try:
        gumbel_params = stats.gumbel_r.fit(max_intensities)
        
        for i, event in enumerate(heat_waves):
            # Calculate return period
            exceedance_prob = 1 - stats.gumbel_r.cdf(event['max_heat_index'], *gumbel_params)
            return_period = 1 / (exceedance_prob * len(heat_waves) / total_years) if exceedance_prob > 0 else np.inf
            event['return_period_years'] = float(return_period)
    
    except:
        # Fallback to empirical method
        sorted_intensities = sorted(max_intensities, reverse=True)
        for event in heat_waves:
            rank = sorted_intensities.index(event['max_heat_index']) + 1
            return_period = total_years / rank
            event['return_period_years'] = float(return_period)
    
    return heat_waves

def calculate_trends(heat_waves, start_year, end_year):
    """Calculate decadal trends in heat wave characteristics"""
    if len(heat_waves) == 0:
        return {}
    
    # Create annual summaries
    annual_stats = {}
    for year in range(start_year, end_year + 1):
        annual_stats[year] = {
            'frequency': 0,
            'total_duration': 0,
            'mean_intensity': [],
            'max_intensity': 0
        }
    
    for event in heat_waves:
        year = datetime.strptime(event['start_date'], '%Y-%m-%d').year
        if year in annual_stats:
            annual_stats[year]['frequency'] += 1
            annual_stats[year]['total_duration'] += event['duration']
            annual_stats[year]['mean_intensity'].append(event['mean_heat_index'])
            annual_stats[year]['max_intensity'] = max(annual_stats[year]['max_intensity'], 
                                                    event['max_heat_index'])
    
    # Calculate trends
    years = list(annual_stats.keys())
    frequencies = [annual_stats[y]['frequency'] for y in years]
    durations = [annual_stats[y]['total_duration'] for y in years]
    
    trends = {}
    
    # Frequency trend
    if len(set(frequencies)) > 1:
        slope, intercept, r_value, p_value, std_err = stats.linregress(years, frequencies)
        trends['frequency'] = {
            'slope_per_decade': slope * 10,
            'p_value': p_value,
            'r_squared': r_value**2
        }
    
    # Duration trend
    if len(set(durations)) > 1:
        slope, intercept, r_value, p_value, std_err = stats.linregress(years, durations)
        trends['duration'] = {
            'slope_per_decade': slope * 10,
            'p_value': p_value,
            'r_squared': r_value**2
        }
    
    return trends

def main():
    parser = argparse.ArgumentParser(description='Heat Index Analysis and Heat Wave Detection')
    parser.add_argument('--temp-data', required=True, help='Temperature data CSV file')
    parser.add_argument('--humidity-data', required=True, help='Humidity data CSV file')
    parser.add_argument('--output-timeseries', required=True, help='Output heat index time series CSV')
    parser.add_argument('--output-heatwaves', required=True, help='Output heat wave events JSON')
    parser.add_argument('--baseline-years', type=int, default=30, help='Years for baseline climatology')
    parser.add_argument('--heatwave-threshold', type=float, default=90, help='Percentile threshold')
    parser.add_argument('--min-duration', type=int, default=3, help='Minimum heat wave duration (days)')
    
    args = parser.parse_args()
    
    try:
        # Load data
        print("Loading temperature and humidity data...")
        temp_data = pd.read_csv(args.temp_data, parse_dates=[0], index_col=0)
        humidity_data = pd.read_csv(args.humidity_data, parse_dates=[0], index_col=0)
        
        # Align datasets
        common_dates = temp_data.index.intersection(humidity_data.index)
        temp_aligned = temp_data.loc[common_dates].iloc[:, 0]
        humidity_aligned = humidity_data.loc[common_dates].iloc[:, 0]
        
        print(f"Processing {len(common_dates)} days of data...")
        
        # Calculate heat index
        print("Calculating heat index...")
        heat_index = calculate_heat_index(temp_aligned.values, humidity_aligned.values)
        heat_index_series = pd.Series(heat_index, index=common_dates)
        
        # Build climatology
        print("Building climatological baseline...")
        climatology = build_climatology(heat_index_series, args.baseline_years, args.heatwave_threshold)
        
        # Detect heat waves
        print("Detecting heat wave events...")
        heat_waves, threshold_series = detect_heat_waves(heat_index_series, climatology, args.min_duration)
        
        # Analyze statistics
        print(f"Analyzing {len(heat_waves)} heat wave events...")
        analyzed_events = analyze_heat_wave_statistics(heat_waves, heat_index_series, threshold_series)
        
        # Calculate return periods
        total_years = len(heat_index_series.index.year.unique())
        analyzed_events = calculate_return_periods(analyzed_events, total_years)
        
        # Calculate trends
        start_year = heat_index_series.index.year.min()
        end_year = heat_index_series.index.year.max()
        trends = calculate_trends(analyzed_events, start_year, end_year)
        
        # Save time series
        print("Saving outputs...")
        output_df = pd.DataFrame({
            'heat_index': heat_index_series,
            'threshold': threshold_series,
            'temperature': temp_aligned,
            'humidity': humidity_aligned
        })
        output_df.to_csv(args.output_timeseries)
        
        # Save heat wave analysis
        output_data = {
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'data_period': f"{start_year}-{end_year}",
                'baseline_years': args.baseline_years,
                'threshold_percentile': args.heatwave_threshold,
                'min_duration_days': args.min_duration,
                'total_events': len(analyzed_events)
            },
            'heat_wave_events': analyzed_events,
            'trends': trends,
            'summary_statistics': {
                'mean_duration': np.mean([e['duration'] for e in analyzed_events]) if analyzed_events else 0,
                'mean_intensity': np.mean([e['mean_heat_index'] for e in analyzed_events]) if analyzed_events else 0,
                'max_intensity_observed': max([e['max_heat_index'] for e in analyzed_events]) if analyzed_events else 0
            }
        }
        
        with open(args.output_heatwaves, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"Analysis complete. Found {len(analyzed_events)} heat wave events.")
        print(f"Time series saved to: {args.output_timeseries}")
        print(f"Heat wave analysis saved to: {args.output_heatwaves}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
