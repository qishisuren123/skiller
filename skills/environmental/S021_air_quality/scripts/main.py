#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import logging
from collections import defaultdict, Counter

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_aqi_subindex(concentration, breakpoints):
    """Calculate AQI sub-index for a given concentration using EPA breakpoints"""
    if pd.isna(concentration):
        return np.nan
    
    for i, (c_low, c_high, aqi_low, aqi_high) in enumerate(breakpoints):
        if c_low <= concentration <= c_high:
            # Linear interpolation formula
            aqi = ((aqi_high - aqi_low) / (c_high - c_low)) * (concentration - c_low) + aqi_low
            return round(aqi)
    
    # If concentration exceeds all breakpoints, return maximum AQI
    return 500

def get_aqi_breakpoints():
    """Define EPA AQI breakpoints for each pollutant"""
    return {
        'pm25': [(0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150), 
                 (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500.4, 301, 500)],
        'pm10': [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150), 
                 (255, 354, 151, 200), (355, 424, 201, 300), (425, 604, 301, 500)],
        'o3': [(0, 54, 0, 50), (55, 70, 51, 100), (71, 85, 101, 150), 
               (86, 105, 151, 200), (106, 200, 201, 300)],
        'no2': [(0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150), 
                (361, 649, 151, 200), (650, 1249, 201, 300), (1250, 2049, 301, 500)],
        'so2': [(0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150), 
                (186, 304, 151, 200), (305, 604, 201, 300), (605, 1004, 301, 500)],
        'co': [(0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150), 
               (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300), (30.5, 50.4, 301, 500)]
    }

def get_aqi_category(aqi):
    """Get AQI category based on value"""
    if pd.isna(aqi):
        return "No Data"
    elif aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

def generate_monthly_summary(daily_df, output_dir):
    """Generate monthly summary statistics"""
    logging.info("Generating monthly summary")
    
    # Convert date to datetime for grouping
    daily_df_copy = daily_df.copy()
    daily_df_copy['date'] = pd.to_datetime(daily_df_copy['date'])
    daily_df_copy['month'] = daily_df_copy['date'].dt.to_period('M')
    
    monthly_summary = {}
    
    for month in daily_df_copy['month'].unique():
        month_data = daily_df_copy[daily_df_copy['month'] == month].dropna(subset=['aqi'])
        
        if len(month_data) == 0:
            continue
            
        # Calculate statistics
        mean_aqi = month_data['aqi'].mean()
        max_aqi = month_data['aqi'].max()
        
        # Count days in each category
        category_counts = month_data['category'].value_counts().to_dict()
        
        # Count dominant pollutant frequency
        pollutant_counts = month_data['dominant_pollutant'].value_counts().to_dict()
        
        monthly_summary[str(month)] = {
            'mean_aqi': round(mean_aqi, 1),
            'max_aqi': int(max_aqi),
            'category_counts': category_counts,
            'dominant_pollutant_counts': pollutant_counts
        }
    
    # Save monthly summary
    monthly_output = os.path.join(output_dir, 'monthly_summary.json')
    with open(monthly_output, 'w') as f:
        json.dump(monthly_summary, f, indent=2)
    
    logging.info(f"Monthly summary saved to {monthly_output}")
    return monthly_summary

def generate_exceedance_report(daily_df, output_dir):
    """Generate exceedance report for days with AQI > 100"""
    logging.info("Generating exceedance report")
    
    # Work with a copy and ensure date is in proper format
    daily_df_copy = daily_df.copy()
    daily_df_copy['date'] = pd.to_datetime(daily_df_copy['date'])
    
    valid_days = daily_df_copy.dropna(subset=['aqi'])
    exceedance_days = valid_days[valid_days['aqi'] > 100]
    
    total_days = len(valid_days)
    exceedance_count = len(exceedance_days)
    exceedance_rate = (exceedance_count / total_days * 100) if total_days > 0 else 0
    
    # Get exceedance dates - now this will work with datetime objects
    exceedance_dates = exceedance_days['date'].dt.strftime('%Y-%m-%d').tolist()
    
    # Find worst day
    if len(valid_days) > 0:
        worst_day_idx = valid_days['aqi'].idxmax()
        worst_day = valid_days.loc[worst_day_idx]
        worst_day_date = worst_day['date'].strftime('%Y-%m-%d')
        worst_aqi = int(worst_day['aqi'])
    else:
        worst_day_date = "No Data"
        worst_aqi = 0
    
    exceedance_report = {
        'total_days': total_days,
        'exceedance_days': exceedance_count,
        'exceedance_rate': round(exceedance_rate, 1),
        'exceedance_dates': exceedance_dates,
        'worst_day': worst_day_date,
        'worst_aqi': worst_aqi
    }
    
    # Save exceedance report
    exceedance_output = os.path.join(output_dir, 'exceedance_report.json')
    with open(exceedance_output, 'w') as f:
        json.dump(exceedance_report, f, indent=2)
    
    logging.info(f"Exceedance report saved to {exceedance_output}")
    return exceedance_report

def process_aqi_data(input_file, output_dir):
    """Main processing function"""
    logging.info(f"Reading data from {input_file}")
    
    # Read CSV data
    df = pd.read_csv(input_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    logging.info(f"Data shape: {df.shape}")
    logging.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Get breakpoints
    breakpoints = get_aqi_breakpoints()
    
    # Calculate daily averages
    daily_data = []
    
    for date in df['date'].unique():
        day_data = df[df['date'] == date].copy()
        
        # Calculate appropriate averages with better handling
        pm25_24hr = day_data['pm25'].mean() if len(day_data) >= 18 else np.nan
        pm10_24hr = day_data['pm10'].mean() if len(day_data) >= 18 else np.nan
        
        # For 8-hour averages, need at least 8 consecutive hours
        if len(day_data) >= 8:
            o3_8hr = day_data['o3'].rolling(window=8, min_periods=6).mean().max()
            co_8hr = day_data['co'].rolling(window=8, min_periods=6).mean().max()
        else:
            o3_8hr = np.nan
            co_8hr = np.nan
            
        # 1-hour max values
        no2_1hr = day_data['no2'].max() if not day_data['no2'].isna().all() else np.nan
        so2_1hr = day_data['so2'].max() if not day_data['so2'].isna().all() else np.nan
        
        # Calculate sub-indices
        pm25_aqi = calculate_aqi_subindex(pm25_24hr, breakpoints['pm25'])
        pm10_aqi = calculate_aqi_subindex(pm10_24hr, breakpoints['pm10'])
        o3_aqi = calculate_aqi_subindex(o3_8hr, breakpoints['o3'])
        no2_aqi = calculate_aqi_subindex(no2_1hr, breakpoints['no2'])
        so2_aqi = calculate_aqi_subindex(so2_1hr, breakpoints['so2'])
        co_aqi = calculate_aqi_subindex(co_8hr, breakpoints['co'])
        
        # Overall AQI is maximum of all sub-indices
        sub_indices = [pm25_aqi, pm10_aqi, o3_aqi, no2_aqi, so2_aqi, co_aqi]
        valid_indices = [x for x in sub_indices if not pd.isna(x)]
        
        if valid_indices:
            aqi = max(valid_indices)
            # Find dominant pollutant
            pollutant_names = ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']
            dominant_idx = sub_indices.index(aqi)
            dominant_pollutant = pollutant_names[dominant_idx]
        else:
            aqi = np.nan
            dominant_pollutant = "No Data"
        
        daily_data.append({
            'date': date,
            'aqi': aqi,
            'category': get_aqi_category(aqi),
            'dominant_pollutant': dominant_pollutant,
            'pm25_aqi': pm25_aqi,
            'pm10_aqi': pm10_aqi,
            'o3_aqi': o3_aqi,
            'no2_aqi': no2_aqi,
            'so2_aqi': so2_aqi,
            'co_aqi': co_aqi
        })
    
    # Create daily DataFrame
    daily_df = pd.DataFrame(daily_data)
    
    # Save daily AQI
    daily_output = os.path.join(output_dir, 'daily_aqi.csv')
    daily_df.to_csv(daily_output, index=False)
    logging.info(f"Daily AQI saved to {daily_output}")
    
    # Generate monthly summary and exceedance report
    monthly_summary = generate_monthly_summary(daily_df, output_dir)
    exceedance_report = generate_exceedance_report(daily_df, output_dir)
    
    return daily_df, monthly_summary, exceedance_report

def main():
    parser = argparse.ArgumentParser(description='Calculate Air Quality Index from pollutant data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    
    args = parser.parse_args()
    
    setup_logging()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Process data
    daily_df, monthly_summary, exceedance_report = process_aqi_data(args.input, args.output)
    
    # Print summary statistics
    valid_days = daily_df.dropna(subset=['aqi'])
    total_days = len(daily_df)
    
    if len(valid_days) > 0:
        mean_aqi = valid_days['aqi'].mean()
        exceedance_days = exceedance_report['exceedance_days']
        exceedance_rate = exceedance_report['exceedance_rate']
        worst_day = exceedance_report['worst_day']
        worst_aqi = exceedance_report['worst_aqi']
        
        print(f"Total days: {total_days}")
        print(f"Mean AQI: {mean_aqi:.1f}")
        print(f"Exceedance rate: {exceedance_rate}%")
        print(f"Worst day: {worst_day} (AQI: {worst_aqi})")
    else:
        print("No valid AQI data found!")

if __name__ == "__main__":
    main()
