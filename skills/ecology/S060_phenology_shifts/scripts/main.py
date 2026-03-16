#!/usr/bin/env python3
"""
Phenological Shift Detection Analysis Tool
Analyzes long-term ecological observation data to detect temporal shifts in biological events.
"""

import argparse
import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.optimize import minimize
import ruptures as rpt
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import warnings
warnings.filterwarnings('ignore')

class PhenologicalAnalyzer:
    def __init__(self, significance_level=0.05):
        self.significance_level = significance_level
        self.results = {}
        
    def load_data(self, filepath):
        """Load and validate phenological time series data"""
        logging.info(f"Loading data from {filepath}")
        
        # Convert to Path object if it's a string
        filepath = Path(filepath)
        
        # Support multiple formats
        if filepath.suffix == '.csv':
            data = pd.read_csv(filepath)
        elif filepath.suffix in ['.xlsx', '.xls']:
            data = pd.read_excel(filepath)
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel files.")
        
        # Flexible column mapping - handle different naming conventions
        column_mapping = {}
        
        # Map temperature columns
        temp_cols = [col for col in data.columns if 'temp' in col.lower()]
        if temp_cols:
            column_mapping[temp_cols[0]] = 'temperature'
        
        # Map precipitation columns  
        precip_cols = [col for col in data.columns if 'precip' in col.lower()]
        if precip_cols:
            column_mapping[precip_cols[0]] = 'precipitation'
            
        # Rename columns if mapping found
        if column_mapping:
            data = data.rename(columns=column_mapping)
            logging.info(f"Mapped columns: {column_mapping}")
            
        # Validate required columns
        required_cols = ['year', 'doy', 'temperature', 'precipitation']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        return data.sort_values('year')
    
    def preprocess_data(self, data):
        """Handle missing values and outliers using robust methods"""
        logging.info("Preprocessing data: handling missing values and outliers")
        
        # Remove rows where year or DOY is missing (critical variables)
        data = data.dropna(subset=['year', 'doy'])
        
        # Handle climate data missing values with interpolation
        for col in ['temperature', 'precipitation']:
            if data[col].isna().any():
                data[col] = data[col].interpolate(method='linear')
        
        # Outlier detection using IQR method for DOY
        Q1 = data['doy'].quantile(0.25)
        Q3 = data['doy'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Flag but don't remove outliers - they might be real phenological shifts
        data['outlier'] = (data['doy'] < lower_bound) | (data['doy'] > upper_bound)
        logging.info(f"Identified {data['outlier'].sum()} potential outliers")
        
        return data
    
    def pelt_changepoint_detection(self, series, penalty=10):
        """Implement PELT algorithm for change-point detection"""
        logging.info("Running PELT change-point detection")
        
        # Use ruptures library for PELT implementation
        algo = rpt.Pelt(model="rbf", min_size=3).fit(series.values.reshape(-1, 1))
        changepoints = algo.predict(pen=penalty)
        
        # Convert to actual years - fix the indexing issue
        if changepoints:
            changepoints = changepoints[:-1]  # Remove end point (which is len(series))
            # Convert array indices to actual years using iloc
            changepoint_years = []
            for cp_idx in changepoints:
                if cp_idx < len(series):  # Safety check
                    actual_year = series.iloc[cp_idx:cp_idx+1].index[0]  # Get year at this position
                    changepoint_years.append(actual_year)
                    logging.info(f"Changepoint detected at array index {cp_idx} -> year {actual_year}")
        else:
            changepoint_years = []
            
        logging.info(f"Found {len(changepoint_years)} changepoints: {changepoint_years}")
        return changepoint_years
    
    def segmented_regression(self, series, changepoints):
        """Perform segmented regression analysis with breakpoint uncertainty"""
        logging.info("Performing segmented regression analysis")
        
        if not changepoints:
            # No changepoints - simple linear regression
            years = np.array(series.index)
            values = series.values
            
            X = years.reshape(-1, 1)
            reg = LinearRegression().fit(X, values)
            
            # Calculate confidence intervals
            predictions = reg.predict(X)
            mse = mean_squared_error(values, predictions)
            
            return {
                'segments': [{
                    'start_year': int(years[0]),
                    'end_year': int(years[-1]),
                    'slope': float(reg.coef_[0]),
                    'intercept': float(reg.intercept_),
                    'r_squared': float(reg.score(X, values)),
                    'n_points': len(values)
                }],
                'breakpoints': [],
                'overall_mse': float(mse)
            }
        
        # Multiple segments
        segments = []
        
        # Create segment boundaries
        years = np.array(series.index)
        segment_starts = [years[0]] + changepoints
        segment_ends = changepoints + [years[-1]]
        
        total_mse = 0
        total_points = 0
        
        for i, (start_year, end_year) in enumerate(zip(segment_starts, segment_ends)):
            # Get data for this segment
            segment_data = series[(series.index >= start_year) & (series.index <= end_year)]
            
            if len(segment_data) < 3:  # Need minimum points for regression
                continue
                
            seg_years = np.array(segment_data.index)
            seg_values = segment_data.values
            
            # Fit linear regression
            X = seg_years.reshape(-1, 1)
            reg = LinearRegression().fit(X, seg_values)
            
            predictions = reg.predict(X)
            segment_mse = mean_squared_error(seg_values, predictions)
            
            # Calculate standard errors for slope
            n = len(seg_values)
            if n > 2:
                residuals = seg_values - predictions
                mse_seg = np.sum(residuals**2) / (n - 2)
                x_mean = np.mean(seg_years)
                slope_se = np.sqrt(mse_seg / np.sum((seg_years - x_mean)**2))
                
                # 95% confidence interval for slope
                t_val = stats.t.ppf(0.975, n-2)
                slope_ci = [
                    float(reg.coef_[0] - t_val * slope_se),
                    float(reg.coef_[0] + t_val * slope_se)
                ]
            else:
                slope_ci = [None, None]
            
            segments.append({
                'segment_id': i + 1,
                'start_year': int(start_year),
                'end_year': int(end_year),
                'slope': float(reg.coef_[0]),
                'slope_ci_95': slope_ci,
                'intercept': float(reg.intercept_),
                'r_squared': float(reg.score(X, seg_values)),
                'n_points': int(n),
                'mse': float(segment_mse)
            })
            
            total_mse += segment_mse * n
            total_points += n
        
        return {
            'segments': segments,
            'breakpoints': [{'year': int(year)} for year in changepoints],
            'overall_mse': float(total_mse / total_points) if total_points > 0 else 0
        }
    
    def mann_kendall_test(self, series):
        """Perform Mann-Kendall trend test"""
        logging.info("Performing Mann-Kendall trend test")
        
        n = len(series)
        s = 0
        
        for i in range(n-1):
            for j in range(i+1, n):
                if series.iloc[j] > series.iloc[i]:
                    s += 1
                elif series.iloc[j] < series.iloc[i]:
                    s -= 1
        
        # Calculate variance
        var_s = n * (n - 1) * (2 * n + 5) / 18
        
        # Calculate Z statistic
        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
        else:
            z = 0
            
        # Two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        
        return {
            'statistic': s,
            'z_score': z,
            'p_value': p_value,
            'trend': 'increasing' if z > 0 else 'decreasing' if z < 0 else 'no trend'
        }
    
    def climate_correlation_analysis(self, phenology_data, max_lag=3):
        """Calculate correlations with climate variables including lag analysis"""
        logging.info("Performing climate correlation analysis")
        
        correlations = {}
        all_p_values = []
        
        for climate_var in ['temperature', 'precipitation']:
            correlations[climate_var] = {}
            
            for lag in range(max_lag + 1):
                # Create lagged climate data
                if lag == 0:
                    climate_series = phenology_data[climate_var]
                    pheno_series = phenology_data['doy']
                else:
                    # Shift climate data backwards (earlier years)
                    lagged_data = phenology_data.copy()
                    lagged_data[f'{climate_var}_lag{lag}'] = lagged_data[climate_var].shift(lag)
                    
                    # Remove NaN values created by shifting
                    valid_data = lagged_data.dropna(subset=[f'{climate_var}_lag{lag}', 'doy'])
                    
                    if len(valid_data) < 3:  # Need minimum data points
                        continue
                        
                    climate_series = valid_data[f'{climate_var}_lag{lag}']
                    pheno_series = valid_data['doy']
                
                # Calculate both Pearson and Spearman correlations
                if len(climate_series) >= 3:
                    pearson_r, pearson_p = stats.pearsonr(climate_series, pheno_series)
                    spearman_r, spearman_p = stats.spearmanr(climate_series, pheno_series)
                    
                    correlations[climate_var][f'lag_{lag}'] = {
                        'pearson': {'r': pearson_r, 'p_value': pearson_p},
                        'spearman': {'r': spearman_r, 'p_value': spearman_p}
                    }
                    
                    # Collect p-values for multiple comparison correction
                    all_p_values.extend([pearson_p, spearman_p])
        
        # Apply Benjamini-Hochberg correction
        if all_p_values:
            rejected, corrected_p_values, _, _ = multipletests(all_p_values, method='fdr_bh')
            
            # Update correlations with corrected p-values
            p_idx = 0
            for climate_var in ['temperature', 'precipitation']:
                for lag_key in correlations[climate_var]:
                    correlations[climate_var][lag_key]['pearson']['p_value_corrected'] = corrected_p_values[p_idx]
                    correlations[climate_var][lag_key]['spearman']['p_value_corrected'] = corrected_p_values[p_idx + 1]
                    p_idx += 2
        
        return correlations
    
    def analyze(self, data):
        """Main analysis pipeline"""
        logging.info("Starting phenological shift analysis")
        
        # Preprocess data
        clean_data = self.preprocess_data(data)
        
        # Set up time series with year as index
        ts_data = clean_data.set_index('year')['doy']
        
        # 1. PELT Change-point detection
        changepoints = self.pelt_changepoint_detection(ts_data)
        
        # 2. Segmented regression analysis
        segmented_results = self.segmented_regression(ts_data, changepoints)
        
        # 3. Mann-Kendall trend test
        mk_results = self.mann_kendall_test(ts_data)
        
        # 4. Climate correlation analysis with multiple comparison correction
        climate_correlations = self.climate_correlation_analysis(clean_data)
        
        # Store results
        self.results = {
            'changepoints': changepoints,
            'segmented_regression': segmented_results,
            'mann_kendall': mk_results,
            'climate_correlations': climate_correlations,
            'data_summary': {
                'n_observations': len(clean_data),
                'year_range': [int(clean_data['year'].min()), int(clean_data['year'].max())],
                'mean_doy': float(clean_data['doy'].mean()),
                'std_doy': float(clean_data['doy'].std()),
                'n_outliers': int(clean_data['outlier'].sum())
            }
        }
        
        return self.results

def main():
    parser = argparse.ArgumentParser(description='Phenological Shift Detection Analysis')
    parser.add_argument('input_file', type=str, help='Input data file (CSV or Excel)')
    parser.add_argument('-o', '--output', type=Path, default='phenology_results.json',
                       help='Output JSON file path')
    parser.add_argument('--significance', type=float, default=0.05,
                       help='Significance threshold for statistical tests')
    parser.add_argument('--penalty', type=float, default=10,
                       help='Penalty parameter for PELT algorithm')
    parser.add_argument('--max-lag', type=int, default=3,
                       help='Maximum lag years for climate correlation analysis')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Initialize analyzer
        analyzer = PhenologicalAnalyzer(significance_level=args.significance)
        
        # Load and analyze data
        data = analyzer.load_data(args.input_file)
        results = analyzer.analyze(data)
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Analysis complete. Results saved to {args.output}")
        print(f"Detected {len(results['changepoints'])} change-points")
        print(f"Mann-Kendall trend: {results['mann_kendall']['trend']} (p={results['mann_kendall']['p_value']:.4f})")
        print(f"Segmented regression: {len(results['segmented_regression']['segments'])} segments")
        
    except Exception as e:
        logging.error(f"Analysis failed: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
