import os
import sys
import subprocess
import tempfile
import json
import numpy as np
import pandas as pd
import h5py
from scipy.spatial.distance import cdist

def create_data():
    """Generate synthetic lightning stroke data with realistic clustering"""
    np.random.seed(42)
    
    # Create 3-5 storm clusters
    n_clusters = np.random.randint(3, 6)
    n_strokes = np.random.randint(1000, 5001)
    
    # Generate cluster centers within 200x200 km area
    cluster_centers = np.random.uniform(-100, 100, (n_clusters, 2))
    
    strokes = []
    stroke_id = 1
    
    for i in range(n_strokes):
        # Assign to random cluster
        cluster_idx = np.random.randint(0, n_clusters)
        center = cluster_centers[cluster_idx]
        
        # Generate position with clustering (smaller std = tighter clusters)
        std = np.random.uniform(5, 20)  # km
        pos = np.random.normal(center, std)
        
        # Convert km to approximate lat/lon (rough conversion)
        lat = pos[1] / 111.0 + 40.0  # ~40°N base
        lon = pos[0] / (111.0 * np.cos(np.radians(40))) - 100.0  # ~100°W base
        
        # Generate timestamp (spread over several hours)
        timestamp = np.random.uniform(0, 3600000)  # 0-1 hour in ms
        
        # Generate peak current (typical range)
        peak_current = np.random.lognormal(3, 0.8)  # log-normal distribution
        
        strokes.append({
            'timestamp': timestamp,
            'latitude': lat,
            'longitude': lon,
            'peak_current': peak_current,
            'stroke_id': stroke_id
        })
        stroke_id += 1
    
    return pd.DataFrame(strokes)

def test_script():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test data
        stroke_data = create_data()
        input_file = os.path.join(tmpdir, 'strokes.csv')
        stroke_data.to_csv(input_file, index=False)
        
        # Define output files
        density_file = os.path.join(tmpdir, 'density.h5')
        stats_file = os.path.join(tmpdir, 'stats.json')
        
        # Test with various argument name patterns
        possible_args = [
            ['--input-data', input_file, '--output-density', density_file, '--output-stats', stats_file],
            ['--input_data', input_file, '--output_density', density_file, '--output_stats', stats_file],
            ['-i', input_file, '-d', density_file, '-s', stats_file],
        ]
        
        success = False
        for args in possible_args:
            try:
                result = subprocess.run([sys.executable, 'generated.py'] + args, 
                                      capture_output=True, text=True, cwd=tmpdir)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            # Try basic args
            result = subprocess.run([sys.executable, 'generated.py', 
                                   '--input-data', input_file,
                                   '--output-density', density_file,
                                   '--output-stats', stats_file], 
                                  capture_output=True, text=True, cwd=tmpdir)
        
        print(f"PASS: Script executed successfully: {result.returncode == 0}")
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return
        
        # Test output files exist
        print(f"PASS: Density file created: {os.path.exists(density_file)}")
        print(f"PASS: Stats file created: {os.path.exists(stats_file)}")
        
        if not (os.path.exists(density_file) and os.path.exists(stats_file)):
            return
        
        # Test HDF5 structure
        try:
            with h5py.File(density_file, 'r') as f:
                has_coords = 'latitude' in f and 'longitude' in f
                has_counts = 'flash_counts' in f
                has_density = 'density' in f
                has_attrs = len(f.attrs) > 0
                
                print(f"PASS: HDF5 has coordinate arrays: {has_coords}")
                print(f"PASS: HDF5 has flash counts: {has_counts}")
                print(f"PASS: HDF5 has density values: {has_density}")
                print(f"PASS: HDF5 has metadata attributes: {has_attrs}")
                
                if has_coords and has_counts:
                    lat_shape = f['latitude'].shape
                    count_shape = f['flash_counts'].shape
                    shapes_match = lat_shape == count_shape
                    print(f"PASS: Grid dimensions consistent: {shapes_match}")
                    
                    # Check for reasonable grid size
                    reasonable_size = 10 <= lat_shape[0] <= 100 and 10 <= lat_shape[1] <= 100
                    print(f"PASS: Reasonable grid size: {reasonable_size}")
                else:
                    print("PASS: Grid dimensions consistent: False")
                    print("PASS: Reasonable grid size: False")
                    
        except Exception as e:
            print("PASS: HDF5 has coordinate arrays: False")
            print("PASS: HDF5 has flash counts: False")
            print("PASS: HDF5 has density values: False")
            print("PASS: HDF5 has metadata attributes: False")
            print("PASS: Grid dimensions consistent: False")
            print("PASS: Reasonable grid size: False")
        
        # Test JSON structure
        try:
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            
            required_fields = ['total_flashes', 'mean_density', 'max_density', 
                             'peak_current_mean', 'peak_current_std', 'peak_current_max']
            has_required = all(field in stats for field in required_fields)
            print(f"PASS: Stats JSON has required fields: {has_required}")
            
            # Check for reasonable values
            if has_required:
                reasonable_values = (
                    stats['total_flashes'] > 0 and
                    stats['mean_density'] >= 0 and
                    stats['max_density'] >= stats['mean_density'] and
                    stats['peak_current_mean'] > 0
                )
                print(f"PASS: Statistical values are reasonable: {reasonable_values}")
            else:
                print("PASS: Statistical values are reasonable: False")
                
        except Exception as e:
            print("PASS: Stats JSON has required fields: False")
            print("PASS: Statistical values are reasonable: False")
        
        # Calculate scores
        try:
            # Score 1: Data processing completeness
            with h5py.File(density_file, 'r') as f:
                with open(stats_file, 'r') as sf:
                    stats = json.load(sf)
                
                components = [
                    'latitude' in f,
                    'longitude' in f, 
                    'flash_counts' in f,
                    'density' in f,
                    'total_flashes' in stats,
                    'mean_density' in stats
                ]
                completeness_score = sum(components) / len(components)
                print(f"SCORE: Data processing completeness: {completeness_score:.3f}")
                
                # Score 2: Flash grouping quality
                original_strokes = len(stroke_data)
                grouped_flashes = stats.get('total_flashes', 0)
                
                # Good grouping should reduce count (multiple strokes per flash)
                # but not too much (avoid over-grouping)
                if grouped_flashes > 0:
                    reduction_ratio = grouped_flashes / original_strokes
                    # Ideal ratio between 0.3-0.8 (reasonable grouping)
                    if 0.3 <= reduction_ratio <= 0.8:
                        grouping_score = 1.0
                    elif reduction_ratio > 0.8:
                        grouping_score = max(0, 2 - 2*reduction_ratio)  # penalty for under-grouping
                    else:
                        grouping_score = reduction_ratio / 0.3  # penalty for over-grouping
                else:
                    grouping_score = 0.0
                    
                print(f"SCORE: Flash grouping quality: {grouping_score:.3f}")
                
        except Exception as e:
            print("SCORE: Data processing completeness: 0.000")
            print("SCORE: Flash grouping quality: 0.000")

if __name__ == "__main__":
    test_script()
