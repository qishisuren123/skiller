import argparse
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

class PhenologicalAnalyzer:
    def __init__(self, significance_level=0.05, min_segment_length=5):
        self.significance_level = significance_level
        self.min_segment_length = min_segment_length
        self.results = {}
    
    def load_and_validate_data(self, filepath):
        """Load and validate phenological time series data"""
        try:
            data = pd.read_csv(filepath)
            required_cols = ['year', 'doy', 'temperature', 'precipitation']
            
            if not all(col in data.columns for col in required_cols):
                raise ValueError(f"Missing required columns. Need: {required_cols}")
            
            # Validate data length
            if len(data) < 15:
                print("Warning: Less than 15 years of data. Results may be unreliable.")
            
            return data.sort_values('year')
        except Exception as e:
            raise ValueError(f"Error loading data: {e}")
    
    def preprocess_data(self, data):
        """Handle missing values and outliers"""
        # Interpolate missing values
        data = data.interpolate(method='linear', limit=3)
        
        # Detect outliers using IQR method
        Q1 = data['doy'].quantile(0.25)
        Q3 = data['doy'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Flag but don't remove outliers (they might be real shifts)
        outliers = (data['doy'] < lower_bound) | (data['doy'] > upper_bound)
        data['outlier_flag'] = outliers
        
        return data
    
    def pelt_changepoint_detection(self, data, penalty=10):
        """PELT algorithm for change-point detection"""
        values = data['doy'].values
        n = len(values)
        
        if n < 2 * self.min_segment_length:
            return []
        
        # Dynamic programming for PELT
        costs = np.full(n + 1, np.inf)
        costs[0] = -penalty
        changepoints = [[] for _ in range(n + 1)]
        
        for t in range(self.min_segment_length, n + 1):
            for s in range(0, t - self.min_segment_length + 1):
                if s == 0:
                    segment = values[:t]
                else:
                    segment = values[s:t]
                
                if len(segment) > 1:
                    segment_cost = len(segment) * np.log(np.var(segment) + 1e-10)
                    total_cost = costs[s] + segment_cost + penalty
                    
                    if total_cost < costs[t]:
                        costs[t] = total_cost
                        changepoints[t] = changepoints[s] + ([s] if s > 0 else [])
        
        detected_cps = changepoints[n]
        # Convert indices to years
        return [data.iloc[cp]['year'] for cp in detected_cps if cp < len(data)]
    
    def mann_kendall_test(self, data):
        """Modified Mann-Kendall test accounting for autocorrelation"""
        values = data['doy'].values
        n = len(values)
        
        # Calculate S statistic
        S = 0
        for i in range(n-1):
            for j in range(i+1, n):
                S += np.sign(values[j] - values[i])
        
        # Calculate variance accounting for ties
        unique_vals, counts = np.unique(values, return_counts=True)
        tie_adjustment = sum(count * (count - 1) * (2 * count + 5) for count in counts if count > 1)
        
        var_S = (n * (n - 1) * (2 * n + 5) - tie_adjustment) / 18
        
        # Calculate autocorrelation adjustment
        autocorr = np.corrcoef(values[:-1], values[1:])[0, 1]
        if not np.isnan(autocorr) and abs(autocorr) > 0.1:
            var_S *= (1 + 2 * autocorr * (n - 2) * (n - 3) / ((n - 1) * (n - 4)))
        
        # Calculate test statistic
        if S > 0:
            Z = (S - 1) / np.sqrt(var_S)
        elif S < 0:
            Z = (S + 1) / np.sqrt(var_S)
        else:
            Z = 0
        
        p_value = 2 * (1 - stats.norm.cdf(abs(Z)))
        
        # Calculate Sen's slope
        slopes = []
        for i in range(n-1):
            for j in range(i+1, n):
                if j != i:
                    slopes.append((values[j] - values[i]) / (j - i))
        
        sens_slope = np.median(slopes) if slopes else 0
        
        return {
            'statistic': S,
            'p_value': p_value,
            'z_score': Z,
            'sens_slope': sens_slope,
            'trend': 'increasing' if sens_slope > 0 else 'decreasing' if sens_slope < 0 else 'no trend'
        }
    
    def climate_correlation_analysis(self, data, max_lag=3):
        """Analyze correlations with climate variables including lag effects"""
        correlations = {}
        
        for climate_var in ['temperature', 'precipitation']:
            correlations[climate_var] = {}
            
            for lag in range(max_lag + 1):
                if lag == 0:
                    climate_data = data[climate_var].values
                    pheno_data = data['doy'].values
                else:
                    if len(data) <= lag:
                        continue
                    climate_data = data[climate_var].iloc[:-lag].values
                    pheno_data = data['doy'].iloc[lag:].values
                
                # Remove NaN pairs
                valid_mask = ~(np.isnan(climate_data) | np.isnan(pheno_data))
                if np.sum(valid_mask) < 5:  # Need minimum data points
                    continue
                
                climate_clean = climate_data[valid_mask]
                pheno_clean = pheno_data[valid_mask]
                
                # Pearson correlation
                pearson_r, pearson_p = stats.pearsonr(climate_clean, pheno_clean)
                
                # Spearman correlation
                spearman_r, spearman_p = stats.spearmanr(climate_clean, pheno_clean)
                
                correlations[climate_var][f'lag_{lag}'] = {
                    'pearson_r': pearson_r,
                    'pearson_p': pearson_p,
                    'spearman_r': spearman_r,
                    'spearman_p': spearman_p,
                    'n_observations': len(climate_clean)
                }
        
        return correlations
    
    def segmented_regression(self, data, changepoints):
        """Perform segmented regression analysis"""
        if not changepoints:
            return None
        
        years = data['year'].values
        doys = data['doy'].values
        
        def piecewise_linear(x, *params):
            """Piecewise linear function"""
            if len(params) != 2 * (len(changepoints) + 1):
                return np.full_like(x, np.inf)
            
            result = np.zeros_like(x)
            breakpoints = sorted(changepoints)
            
            # First segment
            slope, intercept = params[0], params[1]
            mask = x <= breakpoints[0] if breakpoints else np.ones_like(x, dtype=bool)
            result[mask] = slope * x[mask] + intercept
            
            # Middle segments
            for i, bp in enumerate(breakpoints[:-1]):
                slope, intercept = params[2*(i+1)], params[2*(i+1)+1]
                mask = (x > breakpoints[i]) & (x <= breakpoints[i+1])
                result[mask] = slope * x[mask] + intercept
            
            # Last segment
            if breakpoints:
                slope, intercept = params[-2], params[-1]
                mask = x > breakpoints[-1]
                result[mask] = slope * x[mask] + intercept
            
            return result
        
        # Initial parameter guess
        initial_params = []
        for i in range(len(changepoints) + 1):
            initial_params.extend([0, np.mean(doys)])  # slope, intercept
        
        try:
            from scipy.optimize import curve_fit
            popt, pcov = curve_fit(piecewise_linear, years, doys, p0=initial_params)
            
            # Calculate R-squared
            y_pred = piecewise_linear(years, *popt)
            ss_res = np.sum((doys - y_pred) ** 2)
            ss_tot = np.sum((doys - np.mean(doys)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            return {
                'parameters': popt.tolist(),
                'covariance': pcov.tolist(),
                'r_squared': r_squared,
                'rmse': np.sqrt(np.mean((doys - y_pred) ** 2))
            }
        except:
            return None
    
    def benjamini_hochberg_correction(self, p_values):
        """Apply Benjamini-Hochberg correction for multiple comparisons"""
        p_array = np.array(p_values)
        sorted_indices = np.argsort(p_array)
        sorted_p = p_array[sorted_indices]
        
        m = len(p_values)
        adjusted_p = np.zeros_like(sorted_p)
        
        for i in range(m-1, -1, -1):
            if i == m-1:
                adjusted_p[i] = sorted_p[i]
            else:
                adjusted_p[i] = min(sorted_p[i] * m / (i + 1), adjusted_p[i + 1])
        
        # Restore original order
        result = np.zeros_like(p_array)
        result[sorted_indices] = adjusted_p
        
        return result.tolist()
    
    def analyze(self, data):
        """Main analysis pipeline"""
        # Preprocess data
        data = self.preprocess_data(data)
        
        # Change-point detection
        changepoints = self.pelt_changepoint_detection(data)
        
        # Mann-Kendall trend test
        mk_results = self.mann_kendall_test(data)
        
        # Climate correlation analysis
        climate_correlations = self.climate_correlation_analysis(data)
        
        # Segmented regression
        segmented_results = self.segmented_regression(data, changepoints)
        
        # Collect p-values for multiple comparison correction
        p_values = [mk_results['p_value']]
        for climate_var in climate_correlations:
            for lag in climate_correlations[climate_var]:
                p_values.extend([
                    climate_correlations[climate_var][lag]['pearson_p'],
                    climate_correlations[climate_var][lag]['spearman_p']
                ])
        
        # Apply Benjamini-Hochberg correction
        adjusted_p = self.benjamini_hochberg_correction(p_values)
        
        self.results = {
            'changepoints': changepoints,
            'mann_kendall': mk_results,
            'climate_correlations': climate_correlations,
            'segmented_regression': segmented_results,
            'multiple_comparison_correction': {
                'method': 'benjamini_hochberg',
                'original_p_values': p_values,
                'adjusted_p_values': adjusted_p
            },
            'data_summary': {
                'n_years': len(data),
                'year_range': [int(data['year'].min()), int(data['year'].max())],
                'mean_doy': float(data['doy'].mean()),
                'std_doy': float(data['doy'].std()),
                'n_outliers': int(data['outlier_flag'].sum())
            }
        }
        
        return self.results
    
    def create_visualization(self, data, output_path):
        """Create visualization plots"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Main time series plot
        ax1.scatter(data['year'], data['doy'], alpha=0.7, s=50)
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Day of Year')
        ax1.set_title('Phenological Time Series with Detected Change-points')
        
        # Add change-points
        if 'changepoints' in self.results and self.results['changepoints']:
            for cp in self.results['changepoints']:
                ax1.axvline(x=cp, color='red', linestyle='--', alpha=0.7, label='Change-point')
        
        # Add trend line
        if 'mann_kendall' in self.results:
            slope = self.results['mann_kendall']['sens_slope']
            years = data['year'].values
            trend_line = slope * (years - years[0]) + data['doy'].iloc[0]
            ax1.plot(years, trend_line, 'r-', alpha=0.8, label=f"Trend (slope={slope:.3f})")
        
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Climate correlation heatmap
        climate_vars = ['temperature', 'precipitation']
        lags = [f'lag_{i}' for i in range(4)]
        
        corr_matrix = np.zeros((len(climate_vars), len(lags)))
        for i, var in enumerate(climate_vars):
            for j, lag in enumerate(lags):
                if var in self.results['climate_correlations'] and lag in self.results['climate_correlations'][var]:
                    corr_matrix[i, j] = self.results['climate_correlations'][var][lag]['pearson_r']
        
        im = ax2.imshow(corr_matrix, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
        ax2.set_xticks(range(len(lags)))
        ax2.set_xticklabels(lags)
        ax2.set_yticks(range(len(climate_vars)))
        ax2.set_yticklabels(climate_vars)
        ax2.set_title('Climate-Phenology Correlations by Lag')
        
        # Add correlation values as text
        for i in range(len(climate_vars)):
            for j in range(len(lags)):
                text = ax2.text(j, i, f'{corr_matrix[i, j]:.2f}',
                               ha="center", va="center", color="black")
        
        plt.colorbar(im, ax=ax2)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

def main():
    parser = argparse.ArgumentParser(description='Phenological Shift Detection Analysis')
    parser.add_argument('input_file', help='Input CSV file with phenological data')
    parser.add_argument('--output-json', default='phenology_results.json',
                       help='Output JSON file for results')
    parser.add_argument('--output-plot', default='phenology_plot.png',
                       help='Output plot file')
    parser.add_argument('--significance-level', type=float, default=0.05,
                       help='Statistical significance level')
    parser.add_argument('--min-segment-length', type=int, default=5,
                       help='Minimum segment length for change-point detection')
    parser.add_argument('--penalty', type=float, default=10,
                       help='Penalty parameter for PELT algorithm')
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = PhenologicalAnalyzer(
            significance_level=args.significance_level,
            min_segment_length=args.min_segment_length
        )
        
        # Load and analyze data
        print("Loading data...")
        data = analyzer.load_and_validate_data(args.input_file)
        
        print("Performing phenological shift analysis...")
        results = analyzer.analyze(data)
        
        # Save results
        print(f"Saving results to {args.output_json}")
        with open(args.output_json, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Create visualization
        print(f"Creating visualization: {args.output_plot}")
        analyzer.create_visualization(data, args.output_plot)
        
        # Print summary
        print("\n=== ANALYSIS SUMMARY ===")
        print(f"Data period: {results['data_summary']['year_range'][0]}-{results['data_summary']['year_range'][1]}")
        print(f"Number of years: {results['data_summary']['n_years']}")
        print(f"Change-points detected: {len(results['changepoints'])}")
        if results['changepoints']:
            print(f"Change-point years: {results['changepoints']}")
        
        mk = results['mann_kendall']
        print(f"Overall trend: {mk['trend']} (slope: {mk['sens_slope']:.3f} days/year)")
        print(f"Mann-Kendall p-value: {mk['p_value']:.4f}")
        
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
