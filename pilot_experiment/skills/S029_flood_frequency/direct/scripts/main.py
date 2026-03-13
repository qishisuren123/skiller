import argparse
import pandas as pd
import numpy as np
from scipy.stats import genextreme
import json
import os
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze streamflow records for flood frequency analysis')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--return-periods', default='10,50,100', 
                       help='Comma-separated return periods in years (default: 10,50,100)')
    return parser.parse_args()

def load_streamflow_data(filepath):
    """Load and validate streamflow data"""
    df = pd.read_csv(filepath)
    required_cols = ['date', 'discharge_cms', 'station_id']
    
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in input file")
    
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['discharge_cms'] > 0].copy()  # Remove invalid discharge values
    df = df.dropna()
    
    return df.sort_values(['station_id', 'date'])

def extract_annual_maxima(df):
    """Extract annual maximum discharge using water year (Oct-Sep)"""
    annual_maxima = []
    
    for station_id in df['station_id'].unique():
        station_data = df[df['station_id'] == station_id].copy()
        
        # Assign water year (Oct 1 to Sep 30, labeled by ending calendar year)
        station_data['water_year'] = station_data['date'].apply(
            lambda x: x.year if x.month < 10 else x.year + 1
        )
        
        # Find annual maxima
        yearly_max = station_data.groupby('water_year')['discharge_cms'].max().reset_index()
        yearly_max['station_id'] = station_id
        yearly_max.rename(columns={'water_year': 'year', 'discharge_cms': 'max_discharge'}, inplace=True)
        
        annual_maxima.append(yearly_max[['station_id', 'year', 'max_discharge']])
    
    return pd.concat(annual_maxima, ignore_index=True)

def fit_gev_distribution(annual_maxima_series):
    """Fit GEV distribution to annual maxima series"""
    if len(annual_maxima_series) < 10:
        raise ValueError("Insufficient data for GEV fitting (minimum 10 years required)")
    
    try:
        # Fit GEV distribution
        shape, loc, scale = genextreme.fit(annual_maxima_series)
        return {'shape': shape, 'loc': loc, 'scale': scale}
    except Exception as e:
        raise RuntimeError(f"GEV fitting failed: {str(e)}")

def calculate_return_periods(gev_params, return_periods):
    """Calculate discharge for specified return periods"""
    results = {}
    for T in return_periods:
        exceedance_prob = 1 - 1/T
        discharge = genextreme.ppf(exceedance_prob, 
                                 gev_params['shape'], 
                                 loc=gev_params['loc'], 
                                 scale=gev_params['scale'])
        results[T] = float(discharge)
    return results

def baseflow_separation(discharge_series, alpha=0.925):
    """Perform baseflow separation using digital filter"""
    discharge = discharge_series.values
    baseflow = np.zeros_like(discharge)
    
    # Initialize first value
    baseflow[0] = discharge[0]
    
    # Apply digital filter
    for i in range(1, len(discharge)):
        filtered_value = alpha * baseflow[i-1] + (1-alpha)/2 * (discharge[i] + discharge[i-1])
        baseflow[i] = min(filtered_value, discharge[i])
    
    quickflow = discharge - baseflow
    return baseflow, quickflow

def main():
    args = parse_arguments()
    
    # Parse return periods
    return_periods = [int(x.strip()) for x in args.return_periods.split(',')]
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("Loading streamflow data...")
    df = load_streamflow_data(args.input)
    
    # Extract annual maxima
    print("Extracting annual maxima...")
    annual_maxima = extract_annual_maxima(df)
    
    # Save annual maxima
    annual_maxima.to_csv(output_dir / 'annual_maxima.csv', index=False)
    
    # Perform flood frequency analysis
    print("Performing flood frequency analysis...")
    flood_frequency_results = {}
    
    for station_id in annual_maxima['station_id'].unique():
        station_maxima = annual_maxima[annual_maxima['station_id'] == station_id]['max_discharge']
        
        try:
            gev_params = fit_gev_distribution(station_maxima)
            return_period_discharges = calculate_return_periods(gev_params, return_periods)
            
            flood_frequency_results[str(station_id)] = {
                'gev_params': gev_params,
                'return_periods': return_period_discharges
            }
        except Exception as e:
            print(f"Warning: Skipping station {station_id} - {str(e)}")
    
    # Save flood frequency results
    with open(output_dir / 'flood_frequency.json', 'w') as f:
        json.dump(flood_frequency_results, f, indent=2)
    
    # Perform baseflow separation
    print("Performing baseflow separation...")
    baseflow_results = []
    
    for station_id in df['station_id'].unique():
        station_data = df[df['station_id'] == station_id].copy()
        baseflow, quickflow = baseflow_separation(station_data['discharge_cms'])
        
        station_data['baseflow_cms'] = baseflow
        station_data['quickflow_cms'] = quickflow
        baseflow_results.append(station_data[['date', 'station_id', 'discharge_cms', 'baseflow_cms', 'quickflow_cms']])
    
    # Save baseflow results
    baseflow_df = pd.concat(baseflow_results, ignore_index=True)
    baseflow_df.to_csv(output_dir / 'baseflow.csv', index=False)
    
    # Print summary
    print("\n=== ANALYSIS SUMMARY ===")
    print(f"Number of stations analyzed: {len(flood_frequency_results)}")
    
    years_range = annual_maxima.groupby('station_id')['year'].agg(['min', 'max'])
    total_years = years_range['max'] - years_range['min'] + 1
    print(f"Years of record: {total_years.min()}-{total_years.max()} years per station")
    
    print("\nEstimated 100-year flood discharge (cms):")
    for station_id, results in flood_frequency_results.items():
        if 100 in results['return_periods']:
            q100 = results['return_periods'][100]
            print(f"  Station {station_id}: {q100:.1f} cms")
    
    print(f"\nResults saved to: {output_dir}")

if __name__ == "__main__":
    main()
