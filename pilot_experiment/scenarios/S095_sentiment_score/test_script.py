import subprocess
import tempfile
import os
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

def create_data():
    """Generate synthetic survey data for testing"""
    np.random.seed(42)
    
    # Positive and negative words for sentiment analysis
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'perfect', 'outstanding', 'brilliant']
    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'worst', 'disappointing', 'poor', 'useless', 'annoying']
    neutral_words = ['okay', 'fine', 'average', 'normal', 'standard', 'typical', 'regular', 'common', 'usual', 'moderate']
    
    age_groups = ['18-25', '26-40', '41-60', '60+']
    regions = ['North', 'South', 'East', 'West']
    
    return {
        'positive_words': positive_words,
        'negative_words': negative_words,
        'neutral_words': neutral_words,
        'age_groups': age_groups,
        'regions': regions
    }

def run_test():
    test_data = create_data()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Test arguments with variations
        json_file = 'results.json'
        csv_file = 'responses.csv'
        plot_file = 'sentiment_plot.png'
        num_responses = 50
        
        # Try different argument name variations
        cmd_variations = [
            ['python', 'generated.py', '--output-json', json_file, '--output-csv', csv_file, '--output-plot', plot_file, '--num-responses', str(num_responses)],
            ['python', 'generated.py', '--output_json', json_file, '--output_csv', csv_file, '--output_plot', plot_file, '--num_responses', str(num_responses)],
            ['python', 'generated.py', '--json', json_file, '--csv', csv_file, '--plot', plot_file, '--num-responses', str(num_responses)],
        ]
        
        success = False
        for cmd in cmd_variations:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed")
            return
        
        # Test 1: Check if JSON output file exists
        if os.path.exists(json_file):
            print("PASS: JSON output file created")
        else:
            print("FAIL: JSON output file not created")
            return
        
        # Test 2: Check if CSV output file exists
        if os.path.exists(csv_file):
            print("PASS: CSV output file created")
        else:
            print("FAIL: CSV output file not created")
            return
        
        # Test 3: Check if plot file exists
        if os.path.exists(plot_file):
            print("PASS: Plot file created")
        else:
            print("FAIL: Plot file not created")
        
        # Load and validate JSON results
        try:
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            print("PASS: JSON file is valid")
        except:
            print("FAIL: JSON file is invalid or corrupted")
            return
        
        # Test 4: Check JSON structure
        required_keys = ['individual_responses', 'demographic_summary', 'overall_statistics']
        if all(key in json_data for key in required_keys):
            print("PASS: JSON contains required top-level keys")
        else:
            print("FAIL: JSON missing required top-level keys")
        
        # Test 5: Check individual responses structure
        if 'individual_responses' in json_data and len(json_data['individual_responses']) > 0:
            response = json_data['individual_responses'][0]
            if all(key in response for key in ['text', 'sentiment_score', 'age_group', 'region']):
                print("PASS: Individual responses have correct structure")
            else:
                print("FAIL: Individual responses missing required fields")
        else:
            print("FAIL: No individual responses found")
        
        # Test 6: Check sentiment scores are in valid range
        sentiment_scores = [r['sentiment_score'] for r in json_data['individual_responses']]
        if all(-1 <= score <= 1 for score in sentiment_scores):
            print("PASS: All sentiment scores in valid range [-1, 1]")
        else:
            print("FAIL: Some sentiment scores outside valid range")
        
        # Test 7: Check demographic summary exists
        if 'demographic_summary' in json_data and len(json_data['demographic_summary']) > 0:
            print("PASS: Demographic summary present")
        else:
            print("FAIL: Demographic summary missing or empty")
        
        # Test 8: Check overall statistics
        if 'overall_statistics' in json_data:
            stats = json_data['overall_statistics']
            required_stats = ['mean', 'median', 'std', 'count']
            if all(stat in stats for stat in required_stats):
                print("PASS: Overall statistics complete")
            else:
                print("FAIL: Overall statistics incomplete")
        else:
            print("FAIL: Overall statistics missing")
        
        # Load and validate CSV
        try:
            csv_data = pd.read_csv(csv_file)
            print("PASS: CSV file is valid")
        except:
            print("FAIL: CSV file is invalid or corrupted")
            return
        
        # Test 9: Check CSV columns
        expected_cols = ['text', 'sentiment_score', 'age_group', 'region']
        if all(col in csv_data.columns for col in expected_cols):
            print("PASS: CSV has required columns")
        else:
            print("FAIL: CSV missing required columns")
        
        # Test 10: Check CSV data consistency with JSON
        if len(csv_data) == len(json_data['individual_responses']):
            print("PASS: CSV and JSON have consistent number of responses")
        else:
            print("FAIL: CSV and JSON response counts don't match")
        
        # Test 11: Check for demographic groups
        age_groups_present = csv_data['age_group'].unique()
        regions_present = csv_data['region'].unique()
        if len(age_groups_present) > 1 and len(regions_present) > 1:
            print("PASS: Multiple demographic groups present")
        else:
            print("FAIL: Insufficient demographic diversity")
        
        # Test 12: Check plot file is valid image
        try:
            from PIL import Image
            img = Image.open(plot_file)
            img.verify()
            print("PASS: Plot file is valid image")
        except:
            print("FAIL: Plot file is not a valid image")
        
        # Test 13: Check number of responses matches request
        actual_responses = len(json_data['individual_responses'])
        if abs(actual_responses - num_responses) <= 5:  # Allow small tolerance
            print("PASS: Number of responses approximately matches request")
        else:
            print("FAIL: Number of responses significantly different from request")
        
        # SCORE 1: Sentiment score distribution quality
        sentiment_range = max(sentiment_scores) - min(sentiment_scores)
        score1 = min(1.0, sentiment_range / 1.5)  # Good if range covers significant portion of [-1,1]
        print(f"SCORE: {score1:.3f}")
        
        # SCORE 2: Data completeness and structure quality
        completeness_factors = [
            len(json_data.get('individual_responses', [])) > 0,
            len(json_data.get('demographic_summary', {})) > 0,
            'overall_statistics' in json_data,
            len(csv_data) > 0,
            os.path.exists(plot_file),
            len(age_groups_present) >= 2,
            len(regions_present) >= 2
        ]
        score2 = sum(completeness_factors) / len(completeness_factors)
        print(f"SCORE: {score2:.3f}")

if __name__ == "__main__":
    run_test()
