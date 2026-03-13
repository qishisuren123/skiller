import subprocess
import tempfile
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

def create_data():
    """Generate test parameters for mobility analysis"""
    return {
        'users': [50, 100, 200],
        'trips_per_user': [20, 30, 50],
        'seeds': [42, 123, 456]
    }

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate haversine distance between two points"""
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def test_mobility_analysis():
    test_data = create_data()
    results = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        for i, (users, trips, seed) in enumerate(zip(test_data['users'], 
                                                   test_data['trips_per_user'], 
                                                   test_data['seeds'])):
            
            json_file = f"mobility_{i}.json"
            csv_file = f"hourly_{i}.csv"
            
            # Test different argument patterns
            arg_patterns = [
                ['--users', str(users), '--trips-per-user', str(trips), '--seed', str(seed), 
                 '--json-output', json_file, '--csv-output', csv_file],
                ['--num-users', str(users), '--trips', str(trips), '--random-seed', str(seed),
                 '--output-json', json_file, '--output-csv', csv_file],
                ['-u', str(users), '-t', str(trips), '-s', str(seed), 
                 '-j', json_file, '-c', csv_file]
            ]
            
            success = False
            for args in arg_patterns:
                try:
                    result = subprocess.run(['python', 'generated.py'] + args, 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        success = True
                        break
                except:
                    continue
            
            # Test 1: Script execution
            results.append(("PASS" if success else "FAIL", 
                           f"Script execution with {users} users, {trips} trips/user"))
            
            if not success:
                results.extend([("FAIL", f"Remaining tests skipped for case {i}")] * 4)
                continue
            
            # Test 2: JSON output file exists
            json_exists = os.path.exists(json_file)
            results.append(("PASS" if json_exists else "FAIL", 
                           f"JSON output file created: {json_file}"))
            
            # Test 3: CSV output file exists  
            csv_exists = os.path.exists(csv_file)
            results.append(("PASS" if csv_exists else "FAIL",
                           f"CSV output file created: {csv_file}"))
            
            if json_exists:
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    # Test 4: JSON structure
                    required_keys = ['zone_statistics', 'temporal_patterns', 'mobility_metrics', 'flow_analysis']
                    has_structure = all(key in data for key in required_keys)
                    results.append(("PASS" if has_structure else "FAIL",
                                   "JSON contains required sections"))
                    
                    # Test 5: Zone statistics
                    zones_valid = ('top_destinations' in data['zone_statistics'] and 
                                 len(data['zone_statistics']['top_destinations']) > 0)
                    results.append(("PASS" if zones_valid else "FAIL",
                                   "Zone statistics with destinations"))
                    
                    # Test 6: Temporal patterns
                    temporal_valid = ('hourly_distribution' in data['temporal_patterns'] and
                                    'peak_hours' in data['temporal_patterns'])
                    results.append(("PASS" if temporal_valid else "FAIL",
                                   "Temporal patterns analysis"))
                    
                    # Test 7: Mobility metrics
                    metrics_keys = ['avg_trip_distance', 'avg_mobility_radius', 'trip_purpose_distribution']
                    metrics_valid = all(key in data['mobility_metrics'] for key in metrics_keys)
                    results.append(("PASS" if metrics_valid else "FAIL",
                                   "Mobility metrics calculated"))
                    
                    # Test 8: Flow analysis
                    flow_valid = ('top_routes' in data['flow_analysis'] and 
                                len(data['flow_analysis']['top_routes']) <= 10)
                    results.append(("PASS" if flow_valid else "FAIL",
                                   "Flow analysis with top routes"))
                    
                except Exception as e:
                    results.extend([("FAIL", f"JSON parsing error: {str(e)}")] * 5)
            else:
                results.extend([("FAIL", "JSON file missing")] * 5)
            
            if csv_exists:
                try:
                    df = pd.read_csv(csv_file)
                    
                    # Test 9: CSV structure
                    required_cols = ['hour', 'trip_count', 'avg_duration', 'avg_distance']
                    csv_structure = all(col in df.columns for col in required_cols)
                    results.append(("PASS" if csv_structure else "FAIL",
                                   "CSV has required columns"))
                    
                    # Test 10: CSV data validity
                    valid_hours = df['hour'].between(0, 23).all()
                    positive_counts = (df['trip_count'] >= 0).all()
                    csv_valid = valid_hours and positive_counts and len(df) <= 24
                    results.append(("PASS" if csv_valid else "FAIL",
                                   "CSV data validity"))
                    
                except Exception as e:
                    results.extend([("FAIL", f"CSV parsing error: {str(e)}")] * 2)
            else:
                results.extend([("FAIL", "CSV file missing")] * 2)
        
        # Additional validation tests
        if len([r for r in results if r[0] == "PASS"]) > 0:
            # Test 11: Peak hours identification
            try:
                with open("mobility_0.json", 'r') as f:
                    data = json.load(f)
                peak_hours = data['temporal_patterns'].get('peak_hours', [])
                peak_valid = isinstance(peak_hours, list) and len(peak_hours) > 0
                results.append(("PASS" if peak_valid else "FAIL",
                               "Peak hours identified"))
            except:
                results.append(("FAIL", "Peak hours analysis failed"))
            
            # Test 12: Distance calculations
            try:
                avg_distance = data['mobility_metrics']['avg_trip_distance']
                distance_valid = isinstance(avg_distance, (int, float)) and avg_distance > 0
                results.append(("PASS" if distance_valid else "FAIL",
                               "Distance calculations"))
            except:
                results.append(("FAIL", "Distance calculation failed"))
            
            # Test 13: Trip purpose distribution
            try:
                purpose_dist = data['mobility_metrics']['trip_purpose_distribution']
                purpose_valid = (isinstance(purpose_dist, dict) and 
                               abs(sum(purpose_dist.values()) - 100.0) < 1.0)
                results.append(("PASS" if purpose_valid else "FAIL",
                               "Trip purpose distribution sums to 100%"))
            except:
                results.append(("FAIL", "Trip purpose distribution failed"))
        else:
            results.extend([("FAIL", "Validation tests skipped")] * 3)
        
        # Calculate scores
        pass_count = len([r for r in results if r[0] == "PASS"])
        total_tests = len(results)
        
        # Score 1: Overall completion rate
        completion_score = pass_count / total_tests if total_tests > 0 else 0
        
        # Score 2: Data quality score
        quality_indicators = 0
        quality_total = 0
        
        try:
            if os.path.exists("mobility_0.json"):
                with open("mobility_0.json", 'r') as f:
                    data = json.load(f)
                
                # Check temporal coverage
                if 'hourly_distribution' in data['temporal_patterns']:
                    hourly_dist = data['temporal_patterns']['hourly_distribution']
                    if len(hourly_dist) >= 20:  # Good temporal coverage
                        quality_indicators += 1
                    quality_total += 1
                
                # Check spatial analysis depth
                if 'top_destinations' in data['zone_statistics']:
                    destinations = data['zone_statistics']['top_destinations']
                    if len(destinations) >= 5:  # Good spatial analysis
                        quality_indicators += 1
                    quality_total += 1
                
                # Check flow analysis completeness
                if 'top_routes' in data['flow_analysis']:
                    routes = data['flow_analysis']['top_routes']
                    if len(routes) >= 5:  # Good flow analysis
                        quality_indicators += 1
                    quality_total += 1
        except:
            pass
        
        quality_score = quality_indicators / max(quality_total, 1)
        
        print(f"SCORE: {completion_score:.3f}")
        print(f"SCORE: {quality_score:.3f}")
        
        for status, description in results:
            print(f"{status}: {description}")

if __name__ == "__main__":
    test_mobility_analysis()
