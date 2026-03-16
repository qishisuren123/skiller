#!/usr/bin/env python3
"""
Flood Frequency Analysis Tool
Analyzes daily streamflow records and performs flood frequency analysis.
"""

import argparse
import pandas as pd
import numpy as np
from scipy import stats
import json
import os
import logging
from datetime import datetime

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Flood Frequency Analysis Tool')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--return-periods', default='10,50,100', 
                       help='Return periods in years (comma-separated)')
    return parser.parse_args()

def load_streamflow_data(filepath):
    """Load and validate streamflow data"""
    logging.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    
    logging.info(f"Columns found: {list(df.columns)}")
    logging.info(f"Data shape: {df.shape}")
    
    # Strip whitespace from column names (common issue)
    df.columns = df.columns.str.strip()
    
    # Validate required columns
    required_cols = ['date', 'discharge_cms', 'station_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Convert date column
    df['date'] = pd.to_datetime(df['date'])
    
    # Clean discharge data - remove negative, infinite, and NaN values
    initial_count = len(df)
    df = df[df['discharge_cms'] >= 0]  # Remove negative flows
    df = df[np.isfinite(df['discharge_cms'])]  # Remove inf and NaN
    df = df.dropna(subset=['date', 'discharge_cms', 'station_id'])
    
    removed_count = initial_count - len(df)
    if removed_count > 0:
        logging.warning(f"Removed {removed_count} records with invalid discharge values")
    
    logging.info(f"Loaded {len(df)} valid records for {df['station_id'].nunique()} stations")
    
    return df

def extract_annual_maxima(df, water_year=True):
    """Extract annual maximum discharge for each station"""
    annual_maxima = []
    
    stations = df['station_id'].unique()
    logging.info(f"Processing {len(stations)} stations: {stations}")
    
    for station in stations:
        station_data = df[df['station_id'] == station].copy()
        station_data = station_data.sort_values('date')
        
        if water_year:
            # Water year: Oct 1 - Sep 30
            station_data['water_year'] = station_data['date'].apply(
                lambda x: x.year if x.month < 10 else x.year + 1
            )
        else:
            station_data['water_year'] = station_data['date'].dt.year
            
        yearly_max = station_data.groupby('water_year')['discharge_cms'].max().reset_index()
        yearly_max['station_id'] = station
        yearly_max.rename(columns={'water_year': 'year', 'discharge_cms': 'max_discharge'}, inplace=True)
        
        logging.info(f"Station {station}: {len(yearly_max)} years of data")
        annual_maxima.append(yearly_max)
    
    if not annual_maxima:
        raise ValueError("No annual maxima data extracted")
    
    return pd.concat(annual_maxima, ignore_index=True)

def fit_gev_distribution(annual_max_series):
    """Fit GEV distribution to annual maxima"""
    # Remove any NaN and infinite values
    clean_data = annual_max_series.copy()
    clean_data = clean_data.dropna()
    clean_data = clean_data[np.isfinite(clean_data)]
    clean_data = clean_data[clean_data > 0]  # Remove zero or negative values
    
    logging.info(f"GEV fitting: {len(annual_max_series)} original values, {len(clean_data)} clean values")
    
    if len(clean_data) < 5:
        logging.warning(f"Insufficient clean data for GEV fitting ({len(clean_data)} values)")
        return None
    
    if len(clean_data) < 10:
        logging.warning(f"Limited data for GEV fitting ({len(clean_data)} values) - results may be unreliable")
    
    try:
        # Fit GEV distribution using scipy
        shape, loc, scale = stats.genextreme.fit(clean_data, method='MLE')
        
        # Validate fitted parameters
        if not np.isfinite([shape, loc, scale]).all():
            logging.error("GEV fitting produced non-finite parameters")
            return None
            
        if scale <= 0:
            logging.error(f"GEV fitting produced invalid scale parameter: {scale}")
            return None
        
        logging.info(f"GEV parameters - shape: {shape:.4f}, loc: {loc:.2f}, scale: {scale:.2f}")
        
        return {
            'shape': float(shape),
            'loc': float(loc), 
            'scale': float(scale)
        }
        
    except Exception as e:
        logging.error(f"GEV fitting failed: {str(e)}")
        return None

def calculate_return_period_flows(gev_params, return_periods):
    """Calculate flood discharge for specified return periods"""
    if gev_params is None:
        return {}
    
    flows = {}
    for T in return_periods:
        try:
            # Q_T = GEV.ppf(1 - 1/T)
            prob = 1 - 1/T
            Q_T = stats.genextreme.ppf(prob, gev_params['shape'], 
                                      gev_params['loc'], gev_params['scale'])
            
            if np.isfinite(Q_T) and Q_T > 0:
                flows[T] = float(Q_T)
            else:
                logging.warning(f"Invalid return period flow for T={T}: {Q_T}")
                
        except Exception as e:
            logging.error(f"Error calculating return period flow for T={T}: {str(e)}")
    
    return flows

def perform_baseflow_separation(df, alpha=0.925):
    """
    Perform baseflow separation using digital filter
    baseflow(t) = alpha * baseflow(t-1) + (1-alpha)/2 * (Q(t) + Q(t-1))
    then clip baseflow <= Q
    """
    baseflow_results = []
    
    for station in df['station_id'].unique():
        logging.info(f"Performing baseflow separation for station {station}")
        
        station_data = df[df['station_id'] == station].copy()
        station_data = station_data.sort_values('date').reset_index(drop=True)
        
        discharge_values = station_data['discharge_cms'].values
        n = len(discharge_values)
        baseflow = np.zeros(n)
        
        # Initialize first value
        baseflow[0] = discharge_values[0]
        
        # Apply digital filter
        for i in range(1, n):
            Q_curr = discharge_values[i]
            Q_prev = discharge_values[i-1]
            
            baseflow[i] = alpha * baseflow[i-1] + (1-alpha)/2 * (Q_curr + Q_prev)
            
            # Clip baseflow to not exceed total flow
            baseflow[i] = min(baseflow[i], Q_curr)
        
        # Calculate quickflow (surface runoff)
        quickflow = discharge_values - baseflow
        
        # Create result dataframe for this station
        station_result = station_data[['date', 'station_id', 'discharge_cms']].copy()
        station_result['baseflow_cms'] = baseflow
        station_result['quickflow_cms'] = quickflow
        
        baseflow_results.append(station_result)
    
    return pd.concat(baseflow_results, ignore_index=True)

def main():
    setup_logging()
    args = parse_arguments()
    
    # Parse return periods
    return_periods = [int(x.strip()) for x in args.return_periods.split(',')]
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load data
    df = load_streamflow_data(args.input)
    
    # Extract annual maxima
    annual_maxima = extract_annual_maxima(df)
    
    # Save annual maxima
    annual_maxima_path = os.path.join(args.output, 'annual_maxima.csv')
    annual_maxima.to_csv(annual_maxima_path, index=False)
    logging.info(f"Annual maxima saved to {annual_maxima_path}")
    
    # Perform flood frequency analysis
    flood_frequency = {}
    
    for station in annual_maxima['station_id'].unique():
        logging.info(f"Processing flood frequency for station {station}")
        station_maxima = annual_maxima[annual_maxima['station_id'] == station]['max_discharge']
        
        # Fit GEV distribution
        gev_params = fit_gev_distribution(station_maxima)
        
        # Calculate return period flows
        return_flows = calculate_return_period_flows(gev_params, return_periods)
        
        flood_frequency[station] = {
            'gev_params': gev_params,
            'return_periods': return_flows
        }
    
    # Save flood frequency results
    flood_freq_path = os.path.join(args.output, 'flood_frequency.json')
    with open(flood_freq_path, 'w') as f:
        json.dump(flood_frequency, f, indent=2)
    
    logging.info(f"Flood frequency analysis saved to {flood_freq_path}")
    
    # Perform baseflow separation
    logging.info("Starting baseflow separation")
    baseflow_data = perform_baseflow_separation(df)
    
    # Save baseflow results
    baseflow_path = os.path.join(args.output, 'baseflow.csv')
    baseflow_data.to_csv(baseflow_path, index=False)
    logging.info(f"Baseflow separation results saved to {baseflow_path}")
    
    # Print summary
    print(f"\nFlood Frequency Analysis Summary:")
    print(f"Number of stations: {len(df['station_id'].unique())}")
    print(f"Years of record: {annual_maxima['year'].min()}-{annual_maxima['year'].max()}")
    print(f"\n100-year flood estimates:")
    for station, results in flood_frequency.items():
        if results['gev_params'] is not None and 100 in results['return_periods']:
            print(f"Station {station}: {results['return_periods'][100]:.2f} cms")
        else:
            print(f"Station {station}: Unable to estimate (insufficient data)")
    
    # Print baseflow summary
    print(f"\nBaseflow Separation Summary:")
    for station in df['station_id'].unique():
        station_bf = baseflow_data[baseflow_data['station_id'] == station]
        avg_baseflow_ratio = (station_bf['baseflow_cms'] / station_bf['discharge_cms']).mean()
        print(f"Station {station}: Average baseflow ratio = {avg_baseflow_ratio:.3f}")

if __name__ == "__main__":
    main()
