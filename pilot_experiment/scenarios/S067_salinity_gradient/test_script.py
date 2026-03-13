import os
import sys
import json
import tempfile
import subprocess
import numpy as np
import pandas as pd
import h5py
from scipy import interpolate
import unittest

def create_data():
    """Generate synthetic CTD transect data for estuarine salinity gradient analysis"""
    np.random.seed(42)
    
    # Create 3 transects with varying salinity gradients
    transects = []
    river_mouth_lat, river_mouth_lon = 41.5, -71.3
    
    for transect_id in range(3):
        stations = []
        # 8 stations per transect, moving seaward
        for station_id in range(8):
            # Position stations along transect
            lat = river_mouth_lat + station_id * 0.01 + transect_id * 0.005
            lon = river_mouth_lon + station_id * 0.008
            
            # Depth profile (0 to 20m)
            depths = np.arange(0, 21, 0.5)
            n_depths = len(depths)
            
            # Create realistic salinity profile
            # Surface salinity increases seaward, bottom salinity higher
            surface_salinity = 5 + station_id * 3 + np.random.normal(0, 0.5)
            bottom_salinity = surface_salinity + 8 + station_id * 2
            
            # Add halocline at mid-depth for some stations
            salinity = np.linspace(surface_salinity, bottom_salinity, n_depths)
            if station_id in [3, 4, 5]:  # Create strong haloclines
                halocline_depth = 8 + np.random.normal(0, 1)
                halocline_idx = int(halocline_depth / 0.5)
                if halocline_idx < len(salinity) - 4:
                    # Sharp salinity increase
                    salinity[halocline_idx:halocline_idx+4] += np.array([0, 2, 4, 5])
            
            # Temperature profile (decreases with depth)
            surface_temp = 18 + np.random.normal(0, 1)
            temperature = surface_temp - depths * 0.3 + np.random.normal(0, 0.2, n_depths)
            
            # Calculate density from salinity and temperature (simplified)
            density = 1000 + 0.8 * salinity - 0.2 * temperature
            
            # Add some noise and occasional quality issues
            salinity += np.random.normal(0, 0.1, n_depths)
            temperature += np.random.normal(0, 0.1, n_depths)
            
            # Introduce quality issues in some profiles
            if station_id == 6 and transect_id == 1:
                # Large salinity jump (quality issue)
                salinity[10] += 3.0
            
            # Calculate conductivity from salinity and temperature
            conductivity = salinity * (1 + 0.02 * temperature)
            
            station_data = {
                'station_id': station_id,
                'latitude': lat,
                'longitude': lon,
                'depths': depths.tolist(),
                'salinity': salinity.tolist(),
                'temperature': temperature.tolist(),
                'conductivity': conductivity.tolist(),
                'density': density.tolist()
            }
            stations.append(station_data)
        
        transects.append({
            'transect_id': transect_id,
            'stations': stations
        })
    
    return {
        'transects': transects,
        'river_mouth_lat': river_mouth_lat,
        'river_mouth_lon': river_mouth_lon
    }

class TestSalinityGradientAnalysis(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data = create_data()
        
        # Save input data
        self.input_file = os.path.join(self.test_dir, 'ctd_data.json')
        with open(self.input_file, 'w') as f:
            json.dump(self.data, f)
        
        self.output_dir = os.path.join(self.test_dir, 'output')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Run the generated script
        cmd = [
            sys.executable, 'generated.py',
            '--input', self.input_file,
            '--output-dir', self.output_dir,
            '--transect-id', 'test_transect',
            '--river-mouth-lat', str(self.data['river_mouth_lat']),
            '--river-mouth-lon', str(self.data['river_mouth_lon'])
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.test_dir)
            self.return_code = result.returncode
            self.stdout = result.stdout
            self.stderr = result.stderr
        except Exception as e:
            self.return_code = -1
            self.stderr = str(e)

    def test_script_execution(self):
        """Test that script runs without errors"""
        self.assertEqual(self.return_code, 0, f"Script failed with error: {self.stderr}")

    def test_output_files_created(self):
        """Test that all required output files are created"""
        required_files = [
            'haloclines.json',
            'stratification.json', 
            'salt_wedge.json',
            'mixing_zones.json',
            'interpolated_field.h5',
            'quality_flags.json'
        ]
        
        for filename in required_files:
            filepath = os.path.join(self.output_dir, filename)
            self.assertTrue(os.path.exists(filepath), f"Missing output file: {filename}")

    def test_halocline_detection(self):
        """Test halocline detection results"""
        filepath = os.path.join(self.output_dir, 'haloclines.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                haloclines = json.load(f)
            
            self.assertIsInstance(haloclines, (list, dict))
            if isinstance(haloclines, list) and len(haloclines) > 0:
                halocline = haloclines[0]
                required_keys = ['depth_range', 'max_gradient', 'latitude', 'longitude']
                for key in required_keys:
                    self.assertIn(key, halocline, f"Missing key in halocline data: {key}")

    def test_stratification_analysis(self):
        """Test stratification parameter calculations"""
        filepath = os.path.join(self.output_dir, 'stratification.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                stratification = json.load(f)
            
            self.assertIsInstance(stratification, (list, dict))
            if isinstance(stratification, list) and len(stratification) > 0:
                station = stratification[0]
                self.assertIn('stratification_parameter', station)
                self.assertIn('classification', station)
                self.assertIn(['well-mixed', 'partially mixed', 'stratified'], 
                            station.get('classification', ''))

    def test_salt_wedge_mapping(self):
        """Test salt wedge intrusion analysis"""
        filepath = os.path.join(self.output_dir, 'salt_wedge.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                salt_wedge = json.load(f)
            
            self.assertIsInstance(salt_wedge, (list, dict))
            if isinstance(salt_wedge, dict):
                self.assertIn('penetration_distance', salt_wedge)
                self.assertIn('max_intrusion_depth', salt_wedge)

    def test_mixing_efficiency(self):
        """Test tidal mixing efficiency calculations"""
        filepath = os.path.join(self.output_dir, 'mixing_zones.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                mixing = json.load(f)
            
            self.assertIsInstance(mixing, (list, dict))
            if isinstance(mixing, list) and len(mixing) > 0:
                zone = mixing[0]
                self.assertIn('mixing_efficiency', zone)
                efficiency = zone.get('mixing_efficiency', 0)
                self.assertTrue(0 <= efficiency <= 1, "Mixing efficiency should be between 0 and 1")

    def test_interpolated_field_format(self):
        """Test interpolated salinity field output"""
        filepath = os.path.join(self.output_dir, 'interpolated_field.h5')
        if os.path.exists(filepath):
            with h5py.File(filepath, 'r') as f:
                self.assertIn('salinity', f.keys())
                salinity_field = f['salinity'][:]
                self.assertEqual(len(salinity_field.shape), 2, "Salinity field should be 2D")
                self.assertTrue(np.all(np.isfinite(salinity_field[~np.isnan(salinity_field)])))

    def test_quality_control_flags(self):
        """Test quality control flagging"""
        filepath = os.path.join(self.output_dir, 'quality_flags.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                quality_flags = json.load(f)
            
            self.assertIsInstance(quality_flags, (list, dict))
            # Should detect the artificial quality issue we introduced
            if isinstance(quality_flags, list):
                self.assertGreater(len(quality_flags), 0, "Should detect quality issues in test data")

    def test_halocline_gradient_threshold(self):
        """Test that detected haloclines meet gradient threshold"""
        filepath = os.path.join(self.output_dir, 'haloclines.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                haloclines = json.load(f)
            
            if isinstance(haloclines, list):
                for halocline in haloclines:
                    if 'max_gradient' in halocline:
                        self.assertGreaterEqual(halocline['max_gradient'], 0.5,
                                              "Halocline gradient should exceed 0.5 PSU/m")

    def test_stratification_parameter_range(self):
        """Test stratification parameter values are reasonable"""
        filepath = os.path.join(self.output_dir, 'stratification.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                stratification = json.load(f)
            
            if isinstance(stratification, list):
                for station in stratification:
                    if 'stratification_parameter' in station:
                        phi = station['stratification_parameter']
                        self.assertGreaterEqual(phi, 0, "Stratification parameter should be non-negative")
                        self.assertLess(phi, 1000, "Stratification parameter seems unreasonably high")

    def test_geographic_coordinates_valid(self):
        """Test that output coordinates are reasonable"""
        filepath = os.path.join(self.output_dir, 'haloclines.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                haloclines = json.load(f)
            
            if isinstance(haloclines, list):
                for halocline in haloclines:
                    if 'latitude' in halocline and 'longitude' in halocline:
                        lat = halocline['latitude']
                        lon = halocline['longitude']
                        self.assertTrue(40 < lat < 43, "Latitude should be reasonable for test region")
                        self.assertTrue(-73 < lon < -70, "Longitude should be reasonable for test region")

    def test_data_processing_completeness_score(self):
        """SCORE: Fraction of expected data processing steps completed"""
        expected_outputs = 6  # Number of required output files
        actual_outputs = 0
        
        output_files = [
            'haloclines.json', 'stratification.json', 'salt_wedge.json',
            'mixing_zones.json', 'interpolated_field.h5', 'quality_flags.json'
        ]
        
        for filename in output_files:
            if os.path.exists(os.path.join(self.output_dir, filename)):
                actual_outputs += 1
        
        score = actual_outputs / expected_outputs
        print(f"SCORE: {score:.3f}")

    def test_analysis_accuracy_score(self):
        """SCORE: Accuracy of oceanographic analysis based on validation checks"""
        accuracy_points = 0
        total_points = 5
        
        # Check halocline detection accuracy
        halocline_file = os.path.join(self.output_dir, 'haloclines.json')
        if os.path.exists(halocline_file):
            with open(halocline_file, 'r') as f:
                haloclines = json.load(f)
            if isinstance(haloclines, list) and len(haloclines) > 0:
                accuracy_points += 1
        
        # Check stratification classification
        strat_file = os.path.join(self.output_dir, 'stratification.json')
        if os.path.exists(strat_file):
            with open(strat_file, 'r') as f:
                stratification = json.load(f)
            if isinstance(stratification, list) and len(stratification) > 0:
                if 'classification' in stratification[0]:
                    accuracy_points += 1
        
        # Check salt wedge analysis
        wedge_file = os.path.join(self.output_dir, 'salt_wedge.json')
        if os.path.exists(wedge_file):
            with open(wedge_file, 'r') as f:
                salt_wedge = json.load(f)
            if 'penetration_distance' in salt_wedge:
                accuracy_points += 1
        
        # Check mixing efficiency
        mixing_file = os.path.join(self.output_dir, 'mixing_zones.json')
        if os.path.exists(mixing_file):
            with open(mixing_file, 'r') as f:
                mixing = json.load(f)
            if isinstance(mixing, list) and len(mixing) > 0:
                if 'mixing_efficiency' in mixing[0]:
                    accuracy_points += 1
        
        # Check interpolated field
        field_file = os.path.join(self.output_dir, 'interpolated_field.h5')
        if os.path.exists(field_file):
            try:
                with h5py.File(field_file, 'r') as f:
                    if 'salinity' in f.keys():
                        accuracy_points += 1
            except:
                pass
        
        score = accuracy_points / total_points
        print(f"SCORE: {score:.3f}")

if __name__ == '__main__':
    unittest.main()
