# Chlorophyll Bloom Detection Analysis

Create a CLI script that analyzes chlorophyll-a concentration time series data to detect and characterize phytoplankton bloom events in marine ecosystems.

Your script should accept chlorophyll-a concentration data as input and identify bloom events using statistical thresholds and temporal criteria. The analysis should provide both summary statistics and detailed bloom characteristics.

## Requirements

1. **Data Processing**: Read chlorophyll-a concentration time series data (mg/m³) with timestamps and apply a 3-day moving average smoothing filter to reduce noise.

2. **Bloom Detection**: Identify bloom events using a dynamic threshold approach where blooms are defined as periods when chlorophyll concentrations exceed the 90th percentile of the dataset for at least 5 consecutive days.

3. **Bloom Characterization**: For each detected bloom, calculate key metrics including start/end dates, duration (days), peak concentration, integrated bloom magnitude (sum of concentrations above baseline during bloom period), and bloom intensity (peak concentration / baseline).

4. **Statistical Analysis**: Compute dataset statistics including mean baseline concentration (excluding bloom periods), total number of blooms, average bloom duration, seasonal bloom frequency (blooms per month), and the percentage of time in bloom state.

5. **Quality Control**: Flag and report any data gaps longer than 7 days, identify potential outliers (values > 5 standard deviations from mean), and calculate data completeness percentage.

6. **Output Generation**: Save results as a JSON file containing bloom events with their characteristics, summary statistics, and quality control metrics. Also generate a CSV file listing all detected bloom events with their key parameters.

## Command Line Interface
