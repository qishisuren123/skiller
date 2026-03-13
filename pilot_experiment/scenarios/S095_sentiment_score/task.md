# Sentiment Score Analysis for Survey Responses

Create a CLI script that analyzes sentiment scores for open-ended survey responses using a simple lexicon-based approach. Your script should process synthetic survey data and generate sentiment analysis results.

## Requirements

1. **Input Processing**: Accept survey response data via command-line arguments, including response text and respondent demographics (age group, region).

2. **Sentiment Calculation**: Implement a basic sentiment scoring system using predefined positive and negative word lists. Calculate sentiment scores ranging from -1 (most negative) to +1 (most positive) for each response.

3. **Demographic Analysis**: Group responses by demographic categories and calculate average sentiment scores for each group (age groups: 18-25, 26-40, 41-60, 60+; regions: North, South, East, West).

4. **Statistical Summary**: Generate descriptive statistics including mean, median, standard deviation, and count of responses for overall sentiment and each demographic group.

5. **Output Generation**: Save results to a JSON file containing individual response scores and demographic group summaries. Also create a CSV file with response-level data including original text, sentiment score, and demographics.

6. **Visualization**: Generate a simple bar chart showing average sentiment scores by demographic groups and save as PNG file.

## Command Line Interface
