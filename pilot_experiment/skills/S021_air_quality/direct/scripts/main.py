import argparse
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

# EPA AQI Breakpoints: (concentration_range, aqi_range)
AQI_BREAKPOINTS = {
    'pm25': [((0, 12.0), (0, 50)), ((12.1, 35.4), (51, 100)), ((35.5, 55.4), (101, 150)),
             ((55.5, 150.4), (151, 200)), ((150.5, 250.4), (201, 300)), ((250.5, 500.4), (301, 500))],
    'pm10': [((0, 54), (0, 50)), ((55, 154), (51, 100)), ((155, 254), (101, 150)),
             ((255, 354), (151, 200)), ((355, 424), (201, 300)), ((425, 604), (301, 500))],
    'o3': [((0, 54), (0, 50)), ((55, 70), (51, 100)), ((71, 85), (101, 150)),
           ((86, 105), (151, 200)), ((106, 200), (201, 300))],
    'no2': [((0, 53), (0, 50)), ((54, 100), (51, 100)), ((101, 360), (101, 150)),
            ((361, 649), (151, 200)), ((650, 1249), (201, 300)), ((1250, 2049), (301, 500))],
    'so2': [((0, 35), (0, 50)), ((36, 75), (51, 100)), ((76, 185), (101, 150)),
            ((186, 304), (151, 200)), ((305, 604), (201, 300)), ((605, 1004), (301, 500))],
    'co': [((0, 4.4), (0, 50)), ((4.5, 9.4), (51, 100)), ((9.5, 12.4), (101, 150)),
           ((12.5, 15.4), (151, 200)), ((15.5, 30.4), (201, 300)), ((30.5, 50.4), (301, 500))]
}

AQI_CATEGORIES = {
    (0, 50): 'Good',
    (51, 100): 'Moderate', 
    (101, 150): 'Unhealthy for Sensitive Groups',
    (151, 200): 'Unhealthy',
    (201, 300): 'Very Unhealthy',
    (301, 500): 'Hazardous'
}

def calculate_aqi_subindex(concentration, pollutant):
    """Calculate AQI sub-index using EPA breakpoint interpolation"""
    if pd.isna(concentration):
        return np.nan
    
    breakpoints = AQI_BREAKPOINTS[pollutant]
    for (c_lo, c_hi), (i_lo, i_hi) in breakpoints:
        if c_lo <= concentration <= c_hi:
            return ((i_hi - i_lo) / (c_hi - c_lo)) * (concentration - c_lo) + i_lo
    return np.nan  # Out of range

def get_aqi_category(aqi_value):
    """Get AQI category from numeric value"""
    if pd.isna(aqi_value):
        return 'Unknown'
    for (low, high), category in AQI_CATEGORIES.items():
        if low <= aqi_value <= high:
            return category
    return 'Hazardous'  # Above 500

def apply_averaging_rules(df):
    """Apply EPA averaging rules for each pollutant"""
    df = df.set_index('timestamp')
    daily_data = []
    
    for date in df.index.date:
        day_data = df[df.index.date == date]
        if len(day_data) < 18:  # Need at least 75% of hourly data
            continue
            
        daily_row = {'date': date}
        
        # 24-hour averages for PM2.5 and PM10
        daily_row['pm25_avg'] = day_data['pm25'].mean() if day_data['pm25'].count() >= 18 else np.nan
        daily_row['pm10_avg'] = day_data['pm10'].mean() if day_data['pm10'].count() >= 18 else np.nan
        
        # 8-hour rolling max for O3 and CO
        if len(day_data) >= 8:
            daily_row['o3_avg'] = day_data['o3'].rolling(window=8, min_periods=6).mean().max()
            daily_row['co_avg'] = day_data['co'].rolling(window=8, min_periods=6).mean().max()
        else:
            daily_row['o3_avg'] = np.nan
            daily_row['co_avg'] = np.nan
            
        # 1-hour max for NO2 and SO2
        daily_row['no2_avg'] = day_data['no2'].max()
        daily_row['so2_avg'] = day_data['so2'].max()
        
        daily_data.append(daily_row)
    
    return pd.DataFrame(daily_data)

def calculate_daily_aqi(daily_df):
    """Calculate daily AQI and determine dominant pollutant"""
    results = []
    
    for _, row in daily_df.iterrows():
        aqi_values = {}
        pollutants = ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']
        
        for pollutant in pollutants:
            concentration = row[f'{pollutant}_avg']
            aqi_values[f'{pollutant}_aqi'] = calculate_aqi_subindex(concentration, pollutant)
        
        # Find overall AQI (maximum sub-index)
        valid_aqis = {k: v for k, v in aqi_values.items() if not pd.isna(v)}
        if valid_aqis:
            max_aqi = max(valid_aqis.values())
            dominant_pollutant = max(valid_aqis, key=valid_aqis.get).replace('_aqi', '')
        else:
            max_aqi = np.nan
            dominant_pollutant = 'Unknown'
        
        result = {
            'date': row['date'],
            'aqi': max_aqi,
            'category': get_aqi_category(max_aqi),
            'dominant_pollutant': dominant_pollutant,
            **aqi_values
        }
        results.append(result)
    
    return pd.DataFrame(results)

def generate_monthly_summary(daily_aqi_df):
    """Generate monthly aggregation statistics"""
    daily_aqi_df['month'] = pd.to_datetime(daily_aqi_df['date']).dt.to_period('M')
    monthly_summary = {}
    
    for month, group in daily_aqi_df.groupby('month'):
        valid_aqis = group['aqi'].dropna()
        
        # Category counts
        category_counts = group['category'].value_counts().to_dict()
        
        # Dominant pollutant frequency
        pollutant_counts = group['dominant_pollutant'].value_counts().to_dict()
        
        monthly_summary[str(month)] = {
            'mean_aqi': float(valid_aqis.mean()) if len(valid_aqis) > 0 else None,
            'max_aqi': float(valid_aqis.max()) if len(valid_aqis) > 0 else None,
            'category_counts': category_counts,
            'dominant_pollutant_counts': pollutant_counts
        }
    
    return monthly_summary

def generate_exceedance_report(daily_aqi_df):
    """Generate exceedance report for AQI > 100"""
    valid_days = daily_aqi_df.dropna(subset=['aqi'])
    exceedance_days = valid_days[valid_days['aqi'] > 100]
    
    worst_day = valid_days.loc[valid_days['aqi'].idxmax()] if len(valid_days) > 0 else None
    
    report = {
        'total_days': len(valid_days),
        'exceedance_days': len(exceedance_days),
        'exceedance_rate': len(exceedance_days) / len(valid_days) if len(valid_days) > 0 else 0,
        'exceedance_dates': exceedance_days['date'].dt.strftime('%Y-%m-%d').tolist(),
        'worst_day': worst_day['date'].strftime('%Y-%m-%d') if worst_day is not None else None,
        'worst_aqi': float(worst_day['aqi']) if worst_day is not None else None
    }
    
    return report

def main():
    parser = argparse.ArgumentParser(description='Calculate Air Quality Index from hourly pollutant data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    args = parser.parse_args()
    
    # Load and validate data
    try:
        df = pd.read_csv(args.input)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        required_cols = ['timestamp', 'pm25', 'pm10', 'o3', 'no2', 'so2', 'co']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Expected: {required_cols}")
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process data
    print("Applying averaging rules...")
    daily_df = apply_averaging_rules(df)
    
    print("Calculating daily AQI...")
    daily_aqi_df = calculate_daily_aqi(daily_df)
    
    print("Generating monthly summary...")
    monthly_summary = generate_monthly_summary(daily_aqi_df)
    
    print("Generating exceedance report...")
    exceedance_report = generate_exceedance_report(daily_aqi_df)
    
    # Save outputs
    daily_aqi_df.to_csv(output_dir / 'daily_aqi.csv', index=False)
    
    with open(output_dir / 'monthly_summary.json', 'w') as f:
        json.dump(monthly_summary, f, indent=2)
    
    with open(output_dir / 'exceedance_report.json', 'w') as f:
        json.dump(exceedance_report, f, indent=2)
    
    # Print summary statistics
    valid_aqis = daily_aqi_df['aqi'].dropna()
    print(f"\nSummary Statistics:")
    print(f"Total days: {exceedance_report['total_days']}")
    print(f"Mean AQI: {valid_aqis.mean():.1f}" if len(valid_aqis) > 0 else "Mean AQI: N/A")
    print(f"Exceedance rate: {exceedance_report['exceedance_rate']:.1%}")
    print(f"Worst day: {exceedance_report['worst_day']} (AQI: {exceedance_report['worst_aqi']:.0f})")

if __name__ == "__main__":
    main()
