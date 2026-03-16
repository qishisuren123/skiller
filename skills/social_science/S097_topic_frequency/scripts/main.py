import argparse
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random
from collections import defaultdict
import logging
from scipy import stats

def generate_synthetic_documents(num_docs):
    """Generate synthetic documents with timestamps and topic labels"""
    topics = ['machine_learning', 'climate_change', 'genomics', 'quantum_computing', 
              'neuroscience', 'renewable_energy', 'artificial_intelligence', 'biotechnology']
    
    documents = []
    start_date = datetime(2023, 1, 1)
    
    for i in range(num_docs):
        # Generate random timestamp within a year
        random_days = random.randint(0, 365)
        timestamp = start_date + timedelta(days=random_days)
        
        # Assign topic with some bias towards certain topics over time
        topic_weights = [1.0] * len(topics)
        # Add time-based bias
        month_factor = timestamp.month / 12.0
        topic_weights[0] = 1.0 + month_factor  # ML increases over time
        topic_weights[1] = 1.5 - month_factor  # Climate decreases over time
        
        topic = random.choices(topics, weights=topic_weights)[0]
        
        documents.append({
            'id': i,
            'timestamp': timestamp,
            'topic': topic,
            'content': f"Document about {topic} - sample content {i}"
        })
    
    return documents

def calculate_topic_frequencies(df, period):
    """Calculate topic frequencies over time periods - optimized version"""
    print(f"Processing {len(df)} documents for {period} analysis...")
    
    # Create a copy to avoid modifying original
    df_work = df[['timestamp', 'topic']].copy()
    
    # Group by time period more efficiently
    if period == 'daily':
        df_work['period'] = df_work['timestamp'].dt.date
    elif period == 'weekly':
        df_work['period'] = df_work['timestamp'].dt.to_period('W')
    else:  # monthly
        df_work['period'] = df_work['timestamp'].dt.to_period('M')
    
    # Use crosstab for faster counting
    topic_counts = pd.crosstab(df_work['period'], df_work['topic'], margins=False)
    
    # Calculate relative frequencies more efficiently
    row_sums = topic_counts.sum(axis=1)
    topic_proportions = topic_counts.div(row_sums, axis=0)
    
    # Fill any NaN values with 0
    topic_proportions = topic_proportions.fillna(0)
    
    print(f"Generated frequency data for {len(topic_counts)} time periods")
    return topic_counts, topic_proportions

def analyze_trends(topic_data):
    """Analyze trends for each topic using linear regression"""
    trends = {}
    
    for topic in topic_data.columns:
        frequencies = topic_data[topic].values
        time_points = np.arange(len(frequencies))
        
        # Skip if all frequencies are zero
        if np.sum(frequencies) == 0:
            trends[topic] = {
                'slope': 0.0,
                'r_squared': 0.0,
                'p_value': 1.0,
                'trend_class': 'stable'
            }
            continue
        
        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(time_points, frequencies)
        
        # Classify trend
        if abs(slope) < 0.01:  # threshold for stability
            trend_class = 'stable'
        elif slope > 0:
            trend_class = 'increasing'
        else:
            trend_class = 'decreasing'
        
        trends[topic] = {
            'slope': float(slope),
            'r_squared': float(r_value**2),
            'p_value': float(p_value),
            'trend_class': trend_class
        }
    
    return trends

def generate_summary_statistics(df, topic_counts, topic_proportions):
    """Generate summary statistics"""
    # Most frequent topic overall
    overall_counts = df['topic'].value_counts()
    most_frequent_topic = overall_counts.index[0]
    
    # Topic with highest variance in frequency
    topic_variances = topic_proportions.var()
    highest_variance_topic = topic_variances.idxmax()
    
    # Average number of topics per time period
    topics_per_period = (topic_counts > 0).sum(axis=1)
    avg_topics_per_period = topics_per_period.mean()
    
    summary = {
        'most_frequent_topic': most_frequent_topic,
        'most_frequent_count': int(overall_counts.iloc[0]),
        'highest_variance_topic': highest_variance_topic,
        'highest_variance_value': float(topic_variances.max()),
        'avg_topics_per_period': float(avg_topics_per_period),
        'total_time_periods': len(topic_counts),
        'total_documents': len(df)
    }
    
    return summary

def save_results_to_json(topic_counts, topic_proportions, trends, summary, output_file):
    """Save all results to JSON file - optimized version"""
    print("Saving results to JSON...")
    
    # Convert DataFrames to dictionaries more efficiently
    counts_dict = {}
    proportions_dict = {}
    
    # Convert index to strings once
    if hasattr(topic_counts.index[0], 'strftime'):
        time_strings = [ts.strftime('%Y-%m-%d') for ts in topic_counts.index]
    else:
        time_strings = [str(ts) for ts in topic_counts.index]
    
    for topic in topic_counts.columns:
        counts_dict[topic] = dict(zip(time_strings, topic_counts[topic].astype(int).tolist()))
        proportions_dict[topic] = dict(zip(time_strings, topic_proportions[topic].astype(float).tolist()))
    
    results = {
        'summary_statistics': summary,
        'trend_analysis': trends,
        'time_series_data': {
            'absolute_counts': counts_dict,
            'relative_frequencies': proportions_dict
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {output_file}")

def create_visualization(topic_proportions, period, output_prefix):
    """Create and save line plot of topic frequency trends"""
    print("Creating visualization...")
    
    plt.figure(figsize=(12, 8))
    
    # Plot each topic as a separate line
    for topic in topic_proportions.columns:
        plt.plot(topic_proportions.index, topic_proportions[topic], 
                marker='o', linewidth=2, markersize=4, label=topic)
    
    plt.title(f'Topic Frequency Trends Over Time ({period.capitalize()})', fontsize=16)
    plt.xlabel('Time Period', fontsize=12)
    plt.ylabel('Relative Frequency (Proportion)', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    plot_filename = f"{output_prefix}_trends.png"
    plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Visualization saved to {plot_filename}")

def main():
    parser = argparse.ArgumentParser(description='Analyze topic frequency trends')
    parser.add_argument('--num-docs', type=int, default=1000, 
                       help='Number of documents to generate')
    parser.add_argument('--period', choices=['daily', 'weekly', 'monthly'], 
                       default='monthly', help='Time period for aggregation')
    parser.add_argument('--output', default='topic_analysis.json', 
                       help='Output JSON file')
    
    args = parser.parse_args()
    
    # Generate synthetic data
    documents = generate_synthetic_documents(args.num_docs)
    print(f"Generated {len(documents)} documents")
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(documents)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Calculate frequencies
    topic_counts, topic_proportions = calculate_topic_frequencies(df, args.period)
    print(f"\nTopic frequencies by {args.period}:")
    print(topic_counts.head())
    
    # Analyze trends
    trends = analyze_trends(topic_proportions)
    print(f"\nTrend analysis:")
    for topic, trend_info in trends.items():
        print(f"{topic}: {trend_info['trend_class']} (slope: {trend_info['slope']:.4f})")
    
    # Generate summary statistics
    summary = generate_summary_statistics(df, topic_counts, topic_proportions)
    print(f"\nSummary Statistics:")
    print(f"Most frequent topic: {summary['most_frequent_topic']} ({summary['most_frequent_count']} docs)")
    print(f"Highest variance topic: {summary['highest_variance_topic']} (var: {summary['highest_variance_value']:.4f})")
    print(f"Average topics per period: {summary['avg_topics_per_period']:.2f}")
    
    # Save results to JSON
    save_results_to_json(topic_counts, topic_proportions, trends, summary, args.output)
    
    # Create visualization
    output_prefix = args.output.replace('.json', '')
    create_visualization(topic_proportions, args.period, output_prefix)

if __name__ == "__main__":
    main()
