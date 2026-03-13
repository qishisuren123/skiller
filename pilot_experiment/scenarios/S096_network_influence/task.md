# Social Network Influence Analysis

Create a CLI script that analyzes social network interaction data to identify influential users and compute network influence metrics.

Your script should process synthetic social network data representing user interactions (likes, shares, comments) and compute various influence measures to identify key influencers in the network.

## Requirements

1. **Data Processing**: Parse interaction data containing user IDs, interaction types, timestamps, and target users. Handle three interaction types: 'like', 'share', and 'comment' with different influence weights (share=3, comment=2, like=1).

2. **Influence Score Calculation**: For each user, compute a weighted influence score based on their outgoing interactions. Users who generate more high-value interactions (shares, comments) should have higher influence scores.

3. **Network Centrality**: Calculate degree centrality for each user based on their total connections (both incoming and outgoing interactions). Normalize centrality scores to range [0, 1].

4. **Top Influencers Identification**: Identify the top N influencers based on a combined metric that weighs influence score (60%) and centrality (40%). Output should rank users by this combined score.

5. **Interaction Analysis**: Compute summary statistics including total interactions per type, average interactions per user, and the interaction rate (interactions per day) for the time period covered.

6. **Output Generation**: Save results to a JSON file containing top influencers list, individual user metrics, and network summary statistics.

## Command Line Interface
