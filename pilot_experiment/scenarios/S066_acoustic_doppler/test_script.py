import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import subprocess
import tempfile
import os
import sys
from scipy import signal
from scipy.stats import median_abs_deviation

def create_data():
    """Generate synthetic ADCP data with realistic oceanographic characteristics"""
    np.random.seed(42)
    
    # Depth configuration
    n_bins = 50
    depths = np.linspace(5, 200, n_bins)  # 5m to 200m depth
    n_profiles = 100
    
    # Generate realistic velocity profiles with tidal and turbulent components
    time = np.linspace(0, 24, n_profiles)  # 24 hours
    
    # Base current structure (surface intensified)
    u_base = 0.3 * np.exp(-depths/50) * np.cos(2*np.pi*time/12.42)[:, np.newaxis]  # M2 tidal component
    v_base = 0.2 * np.exp(-depths/40) * np.sin(2*np.pi*time/12.42)[:, np.newaxis]
    w_base = 0.02 * np.random.randn(n_profiles, n_bins)  # Vertical velocities
    
    # Add realistic shear and turbulence
    for i in range(n_profiles):
        # Add wind-driven surface layer
        surface_mask = depths < 30
        u_base[i, surface_mask] += 0.1 * np.exp(-depths[surface_mask]/10)
        v_base[i, surface_mask] += 0.05 * np.exp(-depths[surface_mask]/15)
        
        # Add random turbulent fluctuations
        u_base[i, :] += 0.05 * np.random.randn(n_bins)
        v_base[i, :] += 0.05 * np.random.randn(n_bins)
    
    # Generate correlation and echo intensity data
    correlations = np.random.uniform(0.4, 0.95, (n_profiles, n_bins, 4))  # 4 beams
    echo_intensity = 80 + 20 * np.exp(-depths/100) + 5 * np.random.randn(n_profiles, n_bins)
    
    # Introduce realistic bad data
    # Velocity spikes (5% of data)
    spike_mask = np.random.random((n_profiles, n_bins)) < 0.05
    u_base[spike_mask] += np.random.uniform(-0.5, 0.5, np.sum(spike_mask))
    v_base[spike_mask] += np.random.uniform(-0.5, 0.5, np.sum(spike_mask))
    
    # Low correlation regions (10% of data)
    low_corr_mask = np.random.random((n_profiles, n_bins)) < 0.1
    correlations[low_corr_mask, :] = np.random.uniform(0.2, 0.6, (np.sum(low_corr_mask), 4))
    
    # Weak echo regions (deep water, 15% of deep bins)
    deep_mask = depths > 150
    weak_echo_mask = np.random.random((n_profiles, np.sum(deep_mask))) < 0.15
    echo_intensity[:, deep_mask][weak_echo_mask] = np.random.uniform(30, 50, np.sum(weak_echo_mask))
    
    return {
        'u_velocity': u_base,
        'v_velocity': v_base, 
        'w_velocity': w_base,
        'correlations': correlations,
        'echo_intensity': echo_intensity,
        'depths': depths,
        'time': time
    }

def test_script():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Generate test data
        data = create_data()
        
        # Save data as numpy files
        np.save('u_velocity.npy', data['u_velocity'])
        np.save('v_velocity.npy', data['v_velocity'])
        np.save('w_velocity.npy', data['w_velocity'])
        np.save('correlations.npy', data['correlations'])
        np.save('echo_intensity.npy', data['echo_intensity'])
        np.save('depths.npy', data['depths'])
        
        # Test the generated script
        cmd = [
            sys.executable, 'generated.py',
            '--u-velocity', 'u_velocity.npy',
            '--v-velocity', 'v_velocity.npy', 
            '--w-velocity', 'w_velocity.npy',
            '--correlations', 'correlations.npy',
            '--echo-intensity', 'echo_intensity.npy',
            '--depths', 'depths.npy',
            '--correlation-threshold', '0.7',
            '--shear-threshold', '0.1',
            '--output-json', 'qc_results.json',
            '--output-plot', 'velocity_profiles.png'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"FAIL: Script execution failed: {result.stderr}")
                return
        except Exception as e:
            print(f"FAIL: Script execution error: {e}")
            return
        
        # Test outputs exist
        if not os.path.exists('qc_results.json'):
            print("FAIL: JSON output file not created")
            return
        print("PASS: JSON output file created")
        
        if not os.path.exists('velocity_profiles.png'):
            print("FAIL: Plot output file not created")
            return
        print("PASS: Plot output file created")
        
        # Load and validate JSON results
        try:
            with open('qc_results.json', 'r') as f:
                results = json.load(f)
        except:
            print("FAIL: Could not load JSON results")
            return
        print("PASS: JSON results loaded successfully")
        
        # Test required JSON fields
        required_fields = ['depth_averaged_u', 'depth_averaged_v', 'max_velocity', 
                          'data_quality_percent', 'shear_statistics']
        for field in required_fields:
            if field not in results:
                print(f"FAIL: Missing required field: {field}")
                return
        print("PASS: All required JSON fields present")
        
        # Test data quality percentage is reasonable
        quality_pct = results['data_quality_percent']
        if not (0 <= quality_pct <= 100):
            print(f"FAIL: Data quality percentage out of range: {quality_pct}")
            return
        print("PASS: Data quality percentage in valid range")
        
        # Test depth-averaged velocities are reasonable
        u_avg = results['depth_averaged_u']
        v_avg = results['depth_averaged_v']
        if not (-1 <= u_avg <= 1 and -1 <= v_avg <= 1):
            print(f"FAIL: Unrealistic depth-averaged velocities: u={u_avg}, v={v_avg}")
            return
        print("PASS: Depth-averaged velocities are realistic")
        
        # Test maximum velocity is reasonable
        max_vel = results['max_velocity']
        if not (0 <= max_vel <= 2):
            print(f"FAIL: Unrealistic maximum velocity: {max_vel}")
            return
        print("PASS: Maximum velocity is realistic")
        
        # Test shear statistics structure
        if 'mean_shear' not in results['shear_statistics']:
            print("FAIL: Missing mean_shear in shear_statistics")
            return
        print("PASS: Shear statistics properly structured")
        
        # Test that some data was flagged (quality < 100%)
        if quality_pct >= 99:
            print("FAIL: Quality control too lenient - should flag some bad data")
            return
        print("PASS: Quality control flagged some bad data")
        
        # Test correlation filtering worked
        original_size = data['u_velocity'].size
        remaining_pct = quality_pct / 100
        flagged_points = int(original_size * (1 - remaining_pct))
        if flagged_points < original_size * 0.05:  # Should flag at least 5%
            print("FAIL: Too few data points flagged by QC")
            return
        print("PASS: Appropriate amount of data flagged")
        
        # Test uncertainty estimates present
        if 'uncertainty' not in results:
            print("FAIL: Missing uncertainty estimates")
            return
        print("PASS: Uncertainty estimates included")
        
        # Test plot file size (should contain actual plot)
        plot_size = os.path.getsize('velocity_profiles.png')
        if plot_size < 10000:  # Less than 10KB suggests empty/minimal plot
            print("FAIL: Plot file too small - likely empty")
            return
        print("PASS: Plot file has reasonable size")
        
        # Calculate quality score based on data processing accuracy
        expected_bad_data_pct = 30  # Approximately 30% bad data injected
        actual_flagged_pct = 100 - quality_pct
        quality_accuracy = 1 - abs(expected_bad_data_pct - actual_flagged_pct) / 50
        quality_score = max(0, min(1, quality_accuracy))
        
        # Calculate completeness score based on output completeness
        completeness_items = [
            'depth_averaged_u' in results,
            'depth_averaged_v' in results,
            'max_velocity' in results,
            'data_quality_percent' in results,
            'shear_statistics' in results,
            'uncertainty' in results,
            os.path.exists('velocity_profiles.png'),
            plot_size > 10000
        ]
        completeness_score = sum(completeness_items) / len(completeness_items)
        
        print(f"SCORE: quality_control_accuracy: {quality_score:.3f}")
        print(f"SCORE: output_completeness: {completeness_score:.3f}")

if __name__ == "__main__":
    test_script()
