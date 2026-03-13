# Urban Mobility Pattern Analysis

Create a CLI script that analyzes urban mobility patterns from anonymized trip data to identify commuting behaviors, popular destinations, and temporal movement trends.

Your script should accept trip data parameters and generate comprehensive mobility analytics including spatial clustering, temporal patterns, and movement flow statistics.

## Requirements

1. **Data Generation**: Generate synthetic trip data with the following fields: trip_id, user_id, start_lat, start_lon, end_lat, end_lon, start_time (hour 0-23), duration_minutes, trip_type (work/leisure/shopping/other). Create data for specified number of users and trips per user.

2. **Spatial Analysis**: Identify popular origin and destination zones by clustering trip endpoints using a grid-based approach. Calculate the top destination zones by trip frequency and average the coordinates within each grid cell (use 0.01 degree grid resolution).

3. **Temporal Patterns**: Analyze trip timing patterns by calculating hourly trip distributions, identifying peak hours (hours with >10% of daily trips), and computing average trip duration by hour of day.

4. **Mobility Metrics**: Calculate key mobility indicators including: average trip distance (using Haversine formula), mobility radius (95th percentile of distances from each user's centroid), and trip purpose distribution percentages.

5. **Flow Analysis**: Generate origin-destination flow matrices between grid zones, identifying the top 10 most frequent routes with their trip counts and average durations.

6. **Output Generation**: Save results to JSON file containing: zone statistics, temporal patterns, mobility metrics, and flow analysis. Also generate a CSV file with hourly aggregated statistics (hour, trip_count, avg_duration, avg_distance).

Use argparse to handle command-line arguments for number of users, trips per user, random seed, and output file paths.
