# Topic Frequency Analysis

Create a CLI script that analyzes topic frequency trends from a timestamped document corpus. The script should process synthetic document data and compute how frequently different topics appear over time periods.

## Requirements

Your script should use argparse and implement the following functionality:

1. **Data Processing**: Accept the number of documents to generate (default 1000) and a time period for aggregation ('daily', 'weekly', 'monthly'). Generate synthetic documents with timestamps, content, and topic labels.

2. **Topic Frequency Calculation**: Compute the frequency of each topic within each time period. Calculate both absolute counts and relative frequencies (proportions) for each topic.

3. **Trend Analysis**: Identify topics that are increasing, decreasing, or stable over time using simple linear trend analysis. Classify trends based on the slope of frequency over time.

4. **Statistical Summary**: Generate summary statistics including the most frequent topic overall, the topic with the highest variance in frequency, and the average number of topics per time period.

5. **JSON Output**: Save results to a JSON file containing time-series data for each topic, trend classifications, and summary statistics.

6. **Visualization**: Create and save a line plot showing topic frequency trends over time, with different colors for each topic and a legend.

## Command Line Interface
