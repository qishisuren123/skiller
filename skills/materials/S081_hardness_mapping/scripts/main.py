#!/usr/bin/env python3
"""
Hardness Mapping from Indentation Data
Processes hardness measurements and generates 2D maps using advanced interpolation
"""

import argparse
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import RBFInterpolator
from scipy.spatial.distance import cdist
from scipy.stats import pearsonr
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
from sklearn.metrics import mean_squared_error
from sklearn.cluster import KMeans
import h5py
from pathlib import Path
import warnings
import time
from tqdm import tqdm
warnings.filterwarnings('ignore')

class HardnessMapper:
    def __init__(self, padding_factor=0.1):
        self.padding_factor = padding_factor
        self.data = None
        self.grid_x = None
        self.grid_y = None
        self.results = {}
        self.statistics = {}
        
    def load_data(self, filepath):
        """Load and validate hardness data"""
        logging.info(f"Loading data from {filepath}")
        
        # Convert to Path object if string
        filepath = Path(filepath)
        
        # Try different file formats based on extension
        if filepath.suffix.lower() == '.csv':
            df = pd.read_csv(str(filepath))
        elif filepath.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(str(filepath))
        else:
            # Assume space/tab delimited for .txt and other formats
            df = pd.read_csv(str(filepath), delim_whitespace=True)
        
        # Expected columns: X, Y, Hardness (flexible naming)
        x_col = next((col for col in df.columns if 'x' in col.lower()), None)
        y_col = next((col for col in df.columns if 'y' in col.lower()), None)
        h_col = next((col for col in df.columns if any(h in col.lower() for h in ['hard', 'h', 'gpa'])), None)
        
        if not all([x_col, y_col, h_col]):
            logging.error(f"Available columns: {list(df.columns)}")
            raise ValueError("Could not identify X, Y, and Hardness columns")
        
        logging.info(f"Using columns: X='{x_col}', Y='{y_col}', Hardness='{h_col}'")
        
        # Clean data
        initial_count = len(df)
        df = df[[x_col, y_col, h_col]].dropna()
        df = df[np.isfinite(df[x_col]) & np.isfinite(df[y_col]) & np.isfinite(df[h_col])]
        df = df[df[h_col] > 0]  # Hardness should be positive
        
        valid_count = len(df)
        logging.info(f"Processed {valid_count}/{initial_count} valid data points")
        
        if valid_count == 0:
            raise ValueError("No valid data points found after cleaning")
        
        self.data = {
            'x': df[x_col].values,
            'y': df[y_col].values, 
            'hardness': df[h_col].values
        }
        
        return valid_count
    
    def create_adaptive_grid(self, base_resolution=50):
        """Create adaptive grid based on data density"""
        x_min, x_max = self.data['x'].min(), self.data['x'].max()
        y_min, y_max = self.data['y'].min(), self.data['y'].max()
        
        # Add padding
        x_range = x_max - x_min
        y_range = y_max - y_min
        x_min -= x_range * self.padding_factor
        x_max += x_range * self.padding_factor
        y_min -= y_range * self.padding_factor
        y_max += y_range * self.padding_factor
        
        # Create base grid
        x_grid = np.linspace(x_min, x_max, base_resolution)
        y_grid = np.linspace(y_min, y_max, base_resolution)
        self.grid_x, self.grid_y = np.meshgrid(x_grid, y_grid)
        
        logging.info(f"Created {base_resolution}x{base_resolution} grid")
        
    def rbf_interpolation(self, kernel='thin_plate_spline'):
        """Radial Basis Function interpolation"""
        logging.info("Performing RBF interpolation")
        
        points = np.column_stack([self.data['x'], self.data['y']])
        values = self.data['hardness']
        
        rbf = RBFInterpolator(points, values, kernel=kernel)
        grid_points = np.column_stack([self.grid_x.ravel(), self.grid_y.ravel()])
        
        interpolated = rbf(grid_points).reshape(self.grid_x.shape)
        
        # Simple uncertainty based on distance to nearest points
        distances = cdist(grid_points, points)
        min_distances = np.min(distances, axis=1)
        uncertainty = min_distances.reshape(self.grid_x.shape)
        
        self.results['rbf'] = {
            'hardness': interpolated,
            'uncertainty': uncertainty
        }
        
    def idw_interpolation(self, power=2):
        """Inverse Distance Weighting interpolation"""
        logging.info("Performing IDW interpolation")
        
        points = np.column_stack([self.data['x'], self.data['y']])
        values = self.data['hardness']
        grid_points = np.column_stack([self.grid_x.ravel(), self.grid_y.ravel()])
        
        distances = cdist(grid_points, points)
        distances[distances == 0] = 1e-10
        
        weights = 1.0 / (distances ** power)
        interpolated = np.sum(weights * values, axis=1) / np.sum(weights, axis=1)
        
        uncertainty = 1.0 / np.sum(weights, axis=1)
        
        self.results['idw'] = {
            'hardness': interpolated.reshape(self.grid_x.shape),
            'uncertainty': uncertainty.reshape(self.grid_x.shape)
        }
        
    def kriging_interpolation(self, max_points=500, chunk_size=1000):
        """Optimized Kriging using Gaussian Process with subsampling"""
        logging.info("Performing Kriging interpolation")
        
        points = np.column_stack([self.data['x'], self.data['y']])
        values = self.data['hardness']
        n_points = len(points)
        
        if n_points > max_points:
            logging.info(f"Subsampling {n_points} points to {max_points} for Kriging")
            
            kmeans = KMeans(n_clusters=max_points, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(points)
            
            selected_indices = []
            for i in range(max_points):
                cluster_mask = clusters == i
                if np.sum(cluster_mask) > 0:
                    cluster_points = points[cluster_mask]
                    cluster_center = kmeans.cluster_centers_[i]
                    distances_to_center = cdist([cluster_center], cluster_points)[0]
                    closest_idx = np.argmin(distances_to_center)
                    original_idx = np.where(cluster_mask)[0][closest_idx]
                    selected_indices.append(original_idx)
            
            train_points = points[selected_indices]
            train_values = values[selected_indices]
        else:
            train_points = points
            train_values = values
        
        kernel = RBF(length_scale=1.0) + WhiteKernel(noise_level=0.1)
        gp = GaussianProcessRegressor(kernel=kernel, alpha=1e-6)
        
        logging.info("Training Gaussian Process...")
        start_time = time.time()
        gp.fit(train_points, train_values)
        train_time = time.time() - start_time
        logging.info(f"GP training completed in {train_time:.2f} seconds")
        
        grid_points = np.column_stack([self.grid_x.ravel(), self.grid_y.ravel()])
        n_grid = len(grid_points)
        
        if n_grid > chunk_size:
            logging.info(f"Processing {n_grid} grid points in chunks of {chunk_size}")
            mean_chunks = []
            std_chunks = []
            
            for i in tqdm(range(0, n_grid, chunk_size), desc="Kriging prediction"):
                end_idx = min(i + chunk_size, n_grid)
                chunk_points = grid_points[i:end_idx]
                chunk_mean, chunk_std = gp.predict(chunk_points, return_std=True)
                mean_chunks.append(chunk_mean)
                std_chunks.append(chunk_std)
            
            mean = np.concatenate(mean_chunks)
            std = np.concatenate(std_chunks)
        else:
            mean, std = gp.predict(grid_points, return_std=True)
        
        self.results['kriging'] = {
            'hardness': mean.reshape(self.grid_x.shape),
            'uncertainty': std.reshape(self.grid_x.shape)
        }
    
    def calculate_statistics(self):
        """Generate comprehensive statistics"""
        logging.info("Calculating statistics")
        
        hardness = self.data['hardness']
        self.statistics['basic'] = {
            'mean': np.mean(hardness),
            'std': np.std(hardness),
            'min': np.min(hardness),
            'max': np.max(hardness),
            'median': np.median(hardness),
            'q25': np.percentile(hardness, 25),
            'q75': np.percentile(hardness, 75)
        }
        
        methods = list(self.results.keys())
        correlations = {}
        rmse_values = {}
        
        for i, method1 in enumerate(methods):
            for method2 in methods[i+1:]:
                h1 = self.results[method1]['hardness'].ravel()
                h2 = self.results[method2]['hardness'].ravel()
                
                valid_mask = np.isfinite(h1) & np.isfinite(h2)
                if np.sum(valid_mask) > 0:
                    corr, _ = pearsonr(h1[valid_mask], h2[valid_mask])
                    rmse = np.sqrt(mean_squared_error(h1[valid_mask], h2[valid_mask]))
                    correlations[f"{method1}_vs_{method2}"] = corr
                    rmse_values[f"{method1}_vs_{method2}"] = rmse
        
        self.statistics['method_comparison'] = {
            'correlations': correlations,
            'rmse': rmse_values
        }
        
    def spatial_autocorrelation(self, max_distance=None):
        """Calculate spatial autocorrelation"""
        logging.info("Calculating spatial autocorrelation")
        
        if max_distance is None:
            points = np.column_stack([self.data['x'], self.data['y']])
            distances = cdist(points, points)
            max_distance = np.max(distances) / 4
        
        n_bins = 20
        distance_bins = np.linspace(0, max_distance, n_bins)
        autocorr = []
        
        points = np.column_stack([self.data['x'], self.data['y']])
        values = self.data['hardness']
        distances = cdist(points, points)
        
        for i in range(len(distance_bins)-1):
            d_min, d_max = distance_bins[i], distance_bins[i+1]
            
            mask = (distances >= d_min) & (distances < d_max) & (distances > 0)
            
            if np.sum(mask) > 0:
                pairs = np.where(mask)
                values1 = values[pairs[0]]
                values2 = values[pairs[1]]
                
                if len(values1) > 1:
                    corr, _ = pearsonr(values1, values2)
                    autocorr.append(corr)
                else:
                    autocorr.append(0)
            else:
                autocorr.append(0)
        
        self.statistics['spatial_autocorr'] = {
            'distances': distance_bins[:-1],
            'correlation': np.array(autocorr)
        }
    
    def save_results(self, output_dir):
        """Save results to HDF5 and generate visualizations"""
        output_dir = Path(output_dir)
        
        h5_file = output_dir / 'hardness_results.h5'
        logging.info(f"Saving results to {h5_file}")
        
        with h5py.File(h5_file, 'w') as f:
            data_group = f.create_group('original_data')
            data_group.create_dataset('x', data=self.data['x'])
            data_group.create_dataset('y', data=self.data['y'])
            data_group.create_dataset('hardness', data=self.data['hardness'])
            
            grid_group = f.create_group('grid')
            grid_group.create_dataset('x', data=self.grid_x)
            grid_group.create_dataset('y', data=self.grid_y)
            
            for method, result in self.results.items():
                method_group = f.create_group(f'interpolation_{method}')
                method_group.create_dataset('hardness', data=result['hardness'])
                method_group.create_dataset('uncertainty', data=result['uncertainty'])
            
            stats_group = f.create_group('statistics')
            for key, value in self.statistics['basic'].items():
                stats_group.attrs[key] = value
        
        self.create_visualizations(output_dir)
    
    def create_visualizations(self, output_dir):
        """Create visualization plots"""
        logging.info("Creating visualizations")
        
        plt.figure(figsize=(10, 6))
        plt.hist(self.data['hardness'], bins=30, alpha=0.7, edgecolor='black')
        plt.xlabel('Hardness (GPa)')
        plt.ylabel('Frequency')
        plt.title('Hardness Distribution')
        plt.grid(True, alpha=0.3)
        plt.savefig(output_dir / 'hardness_histogram.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        if 'spatial_autocorr' in self.statistics:
            plt.figure(figsize=(10, 6))
            plt.plot(self.statistics['spatial_autocorr']['distances'], 
                    self.statistics['spatial_autocorr']['correlation'], 'o-')
            plt.xlabel('Distance (μm)')
            plt.ylabel('Spatial Correlation')
            plt.title('Spatial Autocorrelation')
            plt.grid(True, alpha=0.3)
            plt.savefig(output_dir / 'spatial_autocorrelation.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        for method, result in self.results.items():
            fig, axes = plt.subplots(1, 2, figsize=(15, 6))
            
            im1 = axes[0].contourf(self.grid_x, self.grid_y, result['hardness'], 
                                  levels=20, cmap='viridis')
            axes[0].scatter(self.data['x'], self.data['y'], c='red', s=10, alpha=0.7)
            axes[0].set_xlabel('X (μm)')
            axes[0].set_ylabel('Y (μm)')
            axes[0].set_title(f'{method.upper()} - Hardness Map')
            plt.colorbar(im1, ax=axes[0], label='Hardness (GPa)')
            
            im2 = axes[1].contourf(self.grid_x, self.grid_y, result['uncertainty'], 
                                  levels=20, cmap='plasma')
            axes[1].set_xlabel('X (μm)')
            axes[1].set_ylabel('Y (μm)')
            axes[1].set_title(f'{method.upper()} - Uncertainty Map')
            plt.colorbar(im2, ax=axes[1], label='Uncertainty')
            
            plt.tight_layout()
            plt.savefig(output_dir / f'{method}_maps.png', dpi=300, bbox_inches='tight')
            plt.close()

def main():
    parser = argparse.ArgumentParser(description='Hardness Mapping from Indentation Data')
    parser.add_argument('input_file', help='Input data file (CSV, Excel, or text)')
    parser.add_argument('-o', '--output', default='hardness_maps', help='Output directory')
    parser.add_argument('--resolution', type=int, default=50, help='Grid resolution')
    parser.add_argument('--padding', type=float, default=0.1, help='Grid padding factor')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    mapper = HardnessMapper(padding_factor=args.padding)
    valid_points = mapper.load_data(args.input_file)
    
    if valid_points < 3:
        logging.error("Need at least 3 valid data points for interpolation")
        return
    
    mapper.create_adaptive_grid(args.resolution)
    
    mapper.rbf_interpolation()
    mapper.idw_interpolation() 
    mapper.kriging_interpolation()
    
    mapper.calculate_statistics()
    mapper.spatial_autocorrelation()
    
    mapper.save_results(output_dir)
    
    logging.info("Analysis complete! Check output directory for results.")

if __name__ == '__main__':
    main()
