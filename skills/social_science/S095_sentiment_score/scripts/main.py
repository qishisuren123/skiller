#!/usr/bin/env python3
import argparse
import json
import csv
import logging
import os
from collections import defaultdict
import statistics
import matplotlib.pyplot as plt
import numpy as np

# Simple sentiment lexicons
POSITIVE_WORDS = {
    'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 
    'like', 'enjoy', 'happy', 'satisfied', 'pleased', 'awesome', 'perfect',
    'outstanding', 'brilliant', 'superb', 'marvelous', 'delighted', 'thrilled'
}

NEGATIVE_WORDS = {
    'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'angry', 'sad',
    'disappointed', 'frustrated', 'annoyed', 'upset', 'disgusted', 'furious',
    'worst', 'pathetic', 'useless', 'stupid', 'ridiculous', 'unacceptable'
}

def calculate_sentiment_score(text):
    """Calculate sentiment score for a given text using lexicon-based approach."""
    if not text or not isinstance(text, str):
        return 0.0
        
    # More efficient text processing
    words = text.lower().replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ').split()
    
    positive_count = 0
    negative_count = 0
    
    # Single pass through words
    for word in words:
        if word in POSITIVE_WORDS:
            positive_count += 1
        elif word in NEGATIVE_WORDS:
            negative_count += 1
    
    total_sentiment_words = positive_count + negative_count
    if total_sentiment_words == 0:
        return 0.0
    
    return (positive_count - negative_count) / total_sentiment_words

def process_survey_data(input_file):
    """Process survey data from CSV file with optimized performance."""
    responses = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # Check if file is empty
            content = f.read()
            if not content.strip():
                raise ValueError("CSV file is empty")
            
            # Reset file pointer
            f.seek(0)
            reader = csv.DictReader(f)
            
            # Validate required columns
            required_columns = {'response_text', 'age_group', 'region'}
            if not required_columns.issubset(set(reader.fieldnames or [])):
                raise ValueError(f"CSV must contain columns: {required_columns}")
            
            # Process in batches for memory efficiency
            batch_size = 1000
            processed_count = 0
            
            for row in reader:
                try:
                    sentiment_score = calculate_sentiment_score(row['response_text'])
                    responses.append({
                        'response_text': row['response_text'],
                        'age_group': row['age_group'],
                        'region': row['region'],
                        'sentiment_score': sentiment_score
                    })
                    
                    processed_count += 1
                    if processed_count % batch_size == 0:
                        logging.info(f"Processed {processed_count} responses...")
                        
                except KeyError as e:
                    logging.warning(f"Row {processed_count + 2}: Missing required column {e}")
                    continue
                except Exception as e:
                    logging.warning(f"Row {processed_count + 2}: Error processing row - {e}")
                    continue
                    
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file '{input_file}' not found")
    except Exception as e:
        raise Exception(f"Error reading CSV file: {e}")
    
    if not responses:
        raise ValueError("No valid responses found in the CSV file")
    
    logging.info(f"Successfully processed {len(responses)} total responses")
    return responses

def group_by_demographics(responses):
    """Group responses by demographic categories using optimized approach."""
    age_groups = defaultdict(list)
    regions = defaultdict(list)
    
    # Single pass through responses
    for response in responses:
        score = response['sentiment_score']
        age_groups[response['age_group']].append(score)
        regions[response['region']].append(score)
    
    return age_groups, regions

def calculate_statistics(scores):
    """Calculate descriptive statistics for a list of scores."""
    if not scores:
        return {'mean': 0, 'median': 0, 'std': 0, 'count': 0}
    
    # Use numpy for faster calculations on large datasets
    scores_array = np.array(scores)
    
    return {
        'mean': float(np.mean(scores_array)),
        'median': float(np.median(scores_array)),
        'std': float(np.std(scores_array, ddof=1)) if len(scores) > 1 else 0,
        'count': len(scores)
    }

def create_visualization(age_stats, region_stats, output_file):
    """Create bar chart visualization of sentiment scores by demographics."""
    # Use Agg backend for better performance in headless environments
    plt.switch_backend('Agg')
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Age groups chart - sort age groups in logical order
    age_order = ['18-25', '26-40', '41-60', '60+']
    age_groups = [group for group in age_order if group in age_stats]
    age_means = [age_stats[group]['mean'] for group in age_groups]
    
    bars1 = ax1.bar(range(len(age_groups)), age_means, color='skyblue', alpha=0.7)
    ax1.set_title('Average Sentiment Score by Age Group')
    ax1.set_xlabel('Age Group')
    ax1.set_ylabel('Average Sentiment Score')
    ax1.set_xticks(range(len(age_groups)))
    ax1.set_xticklabels(age_groups)
    ax1.set_ylim(-1, 1)
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, mean_val in zip(bars1, age_means):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02 if height >= 0 else height - 0.05,
                f'{mean_val:.3f}', ha='center', va='bottom' if height >= 0 else 'top')
    
    # Regions chart
    regions = sorted(region_stats.keys())
    region_means = [region_stats[region]['mean'] for region in regions]
    
    bars2 = ax2.bar(range(len(regions)), region_means, color='lightcoral', alpha=0.7)
    ax2.set_title('Average Sentiment Score by Region')
    ax2.set_xlabel('Region')
    ax2.set_ylabel('Average Sentiment Score')
    ax2.set_xticks(range(len(regions)))
    ax2.set_xticklabels(regions)
    ax2.set_ylim(-1, 1)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, mean_val in zip(bars2, region_means):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.02 if height >= 0 else height - 0.05,
                f'{mean_val:.3f}', ha='center', va='bottom' if height >= 0 else 'top')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Visualization saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Sentiment Analysis for Survey Responses')
    parser.add_argument('input_file', help='Input CSV file with survey responses')
    parser.add_argument('--output-json', default='sentiment_results.json', 
                       help='Output JSON file for results')
    parser.add_argument('--output-csv', default='response_scores.csv',
                       help='Output CSV file with individual scores')
    parser.add_argument('--chart-output', default='sentiment_chart.png',
                       help='Output PNG file for visualization')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Process survey data
        logging.info(f"Processing survey data from {args.input_file}")
        responses = process_survey_data(args.input_file)
        
        # Group by demographics
        age_groups, regions = group_by_demographics(responses)
        
        # Calculate overall statistics
        all_scores = [r['sentiment_score'] for r in responses]
        overall_stats = calculate_statistics(all_scores)
        
        # Calculate demographic statistics
        age_stats = {group: calculate_statistics(scores) for group, scores in age_groups.items()}
        region_stats = {region: calculate_statistics(scores) for region, scores in regions.items()}
        
        # Prepare results
        results = {
            'overall_statistics': overall_stats,
            'age_group_statistics': age_stats,
            'region_statistics': region_stats,
            'individual_responses': responses
        }
        
        # Save JSON results
        with open(args.output_json, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save CSV results
        with open(args.output_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['response_text', 'age_group', 'region', 'sentiment_score'])
            writer.writeheader()
            writer.writerows(responses)
        
        # Create visualization
        create_visualization(age_stats, region_stats, args.chart_output)
        
        logging.info(f"Results saved to {args.output_json}, {args.output_csv}, and {args.chart_output}")
        
        # Print summary
        print(f"\nSentiment Analysis Summary:")
        print(f"Total responses: {overall_stats['count']}")
        print(f"Overall sentiment: {overall_stats['mean']:.3f} (±{overall_stats['std']:.3f})")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
