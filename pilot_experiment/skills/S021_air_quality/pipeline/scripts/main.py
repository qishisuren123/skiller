#!/usr/bin/env python3
import argparse
import pandas as pd
import json
import os
from datetime import datetime
from collections import defaultdict

# EPA AQI breakpoints: [concentration_low, concentration_high] -> [aqi_low, aqi_high]
AQI_BREAKPOINTS = {
    'pm25': [
        ([0, 12.0], [0, 50]),
        ([12.1, 35.4], [51, 100]),
        ([35.5, 55.4], [101, 150]),
        ([55.5, 150.4], [151, 200]),
        ([150.5, 250.4], [201, 300]),
        ([250.5, 500.4], [301, 500])
    ],
    'pm10': [
        ([0, 54], [0, 50]),
        ([55, 154], [51, 100]),
        ([155, 254], [101, 150]),
        ([255, 354], [151, 200]),
        ([355, 424], [201, 300]),
        ([425, 604], [301, 500])
    ],
    'o3': [
        ([0, 54], [0, 50]),
        ([55, 70], [51, 100]),
        ([71, 85], [101, 150]),
        ([86, 105], [151, 200]),
        ([106, 200], [201, 300])
    ],
    'no2': [
        ([0, 53], [0, 50]),
        ([54, 100], [51, 100]),
        ([101, 360], [101, 150]),
        ([361, 649], [151, 200]),
        ([650, 1249], [201, 300]),
        ([1250, 2049], [301, 500])
    ],
    'so2': [
        ([0, 35], [0, 50]),
        ([36, 75], [51, 100]),
        ([76, 185], [101, 150]),
        ([186, 304], [151, 200]),
        ([305, 604], [201, 300]),
        ([605, 1004], [301, 500])
    ],
    'co': [
        ([0, 4.4], [0, 50]),
        ([4.5, 9.4], [51, 100]),
        ([9.5, 12.4], [101, 150]),
        ([12.5, 15.4], [151, 200]),
        ([15.5, 30.4], [201, 300]),
        ([30.5, 50.4], [301, 500])
    ]
}

def calculate_aqi(concentration, pollutant):
    """Calculate AQI for a given pollutant concentration"""
    if pd.isna(concentration) or concentration is None:
        return None
    
    breakpoints = AQI_BREAKPOINTS[pollutant]
    
    for (c_low, c_high), (aqi_low, aqi_high) in breakpoints:
        if c_low <= concentration <= c_high:
            # Linear interpolation formula
            aqi = ((aqi_high - aqi_low) / (c_high - c_low)) * (concentration - c_low) + aqi_low
            return round(aqi)
    
    # If concentration exceeds all breakpoints, return max AQI
    return 500

def get_aqi_category(aqi):
    """Get AQI category from AQI value"""
    if aqi is None:
        return None
    if aqi <= 50:
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

def main():
    parser = argparse.ArgumentParser(description='Calculate AQI from hourly pollutant measurements')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    try:
        # Read input data
        print(f"Reading data from {args.input}")
        df = pd.read_csv(args.input)
        print(f"Data shape: {df.shape}")
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # Calculate appropriate averages for each pollutant
        daily_pm25 = df.groupby('date')['pm25'].mean()
        daily_pm10 = df.groupby('date')['pm10'].mean()
        
        # O3 and CO: 8-hour rolling maximum
        df_sorted = df.sort_values('timestamp')
        df_sorted['o3_8hr'] = df_sorted['o3'].rolling(window=8, min_periods=6).mean()
        df_sorted['co_8hr'] = df_sorted['co'].rolling(window=8, min_periods=6).mean()
        daily_o3 = df_sorted.groupby('date')['o3_8hr'].max()
        daily_co = df_sorted.groupby('date')['co_8hr'].max()
        
        # NO2 and SO2: 1-hour maximum
        daily_no2 = df.groupby('date')['no2'].max()
        daily_so2 = df.groupby('date')['so2'].max()
        
        # Calculate AQI for each pollutant
        daily_results = []
        monthly_data = defaultdict(list)
        all_dates = sorted(set(df['date']))
        
        for date in all_dates:
            pm25_conc = daily_pm25.loc[date] if date in daily_pm25.index else None
            pm10_conc = daily_pm10.loc[date] if date in daily_pm10.index else None
            o3_conc = daily_o3.loc[date] if date in daily_o3.index else None
            co_conc = daily_co.loc[date] if date in daily_co.index else None
            no2_conc = daily_no2.loc[date] if date in daily_no2.index else None
            so2_conc = daily_so2.loc[date] if date in daily_so2.index else None
            
            pm25_aqi = calculate_aqi(pm25_conc, 'pm25')
            pm10_aqi = calculate_aqi(pm10_conc, 'pm10')
            o3_aqi = calculate_aqi(o3_conc, 'o3')
            co_aqi = calculate_aqi(co_conc, 'co')
            no2_aqi = calculate_aqi(no2_conc, 'no2')
            so2_aqi = calculate_aqi(so2_conc, 'so2')
            
            # Find overall AQI and dominant pollutant
            aqi_values = {'pm25': pm25_aqi, 'pm10': pm10_aqi, 'o3': o3_aqi, 
                         'co': co_aqi, 'no2': no2_aqi, 'so2': so2_aqi}
            valid_aqis = {k: v for k, v in aqi_values.items() if v is not None}
            
            if valid_aqis:
                overall_aqi = max(valid_aqis.values())
                dominant_pollutant = max(valid_aqis, key=valid_aqis.get)
                category = get_aqi_category(overall_aqi)
            else:
                overall_aqi = None
                dominant_pollutant = None
                category = None
            
            result = {
                'date': str(date),
                'aqi': overall_aqi,
                'category': category,
                'dominant_pollutant': dominant_pollutant,
                'pm25_aqi': pm25_aqi,
                'pm10_aqi': pm10_aqi,
                'o3_aqi': o3_aqi,
                'no2_aqi': no2_aqi,
                'so2_aqi': so2_aqi,
                'co_aqi': co_aqi
            }
            
            daily_results.append(result)
            
            # Group by month for aggregation
            month_key = f"{date.year}-{date.month:02d}"
            if overall_aqi is not None:
                monthly_data[month_key].append(overall_aqi)
        
        # Write daily results to CSV
        daily_df = pd.DataFrame(daily_results)
        daily_output = os.path.join(args.output, 'daily_aqi.csv')
        daily_df.to_csv(daily_output, index=False)
        print(f"Daily AQI results written to {daily_output}")
        
        # Calculate monthly aggregations
        monthly_summary = {}
        for month, aqi_values in monthly_data.items():
            if aqi_values:
                monthly_summary[month] = {
                    'avg_aqi': round(sum(aqi_values) / len(aqi_values), 1),
                    'max_aqi': max(aqi_values),
                    'min_aqi': min(aqi_values),
                    'days_good': len([x for x in aqi_values if x <= 50]),
                    'days_moderate': len([x for x in aqi_values if 51 <= x <= 100]),
                    'days_unhealthy_sensitive': len([x for x in aqi_values if 101 <= x <= 150]),
                    'days_unhealthy': len([x for x in aqi_values if 151 <= x <= 200]),
                    'days_very_unhealthy': len([x for x in aqi_values if 201 <= x <= 300]),
                    'days_hazardous': len([x for x in aqi_values if x > 300]),
                    'total_days': len(aqi_values)
                }
        
        # Write monthly summary to JSON
        monthly_output = os.path.join(args.output, 'monthly_summary.json')
        with open(monthly_output, 'w') as f:
            json.dump(monthly_summary, f, indent=2)
        print(f"Monthly summary written to {monthly_output}")
        
        # Write overall summary
        all_valid_aqis = [r['aqi'] for r in daily_results if r['aqi'] is not None]
        if all_valid_aqis:
            overall_summary = {
                'total_days_processed': len(daily_results),
                'days_with_valid_aqi': len(all_valid_aqis),
                'overall_avg_aqi': round(sum(all_valid_aqis) / len(all_valid_aqis), 1),
                'overall_max_aqi': max(all_valid_aqis),
                'overall_min_aqi': min(all_valid_aqis),
                'processing_date': datetime.now().isoformat()
            }
            
            summary_output = os.path.join(args.output, 'summary.json')
            with open(summary_output, 'w') as f:
                json.dump(overall_summary, f, indent=2)
            print(f"Overall summary written to {summary_output}")
        
        print(f"Successfully processed {len(daily_results)} days of data")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
