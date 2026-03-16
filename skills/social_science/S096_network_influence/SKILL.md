---
name: network_influence
description: "# Social Network Influence Analysis

Create a CLI script that analyzes social network interaction data to identify influential users and compute network influence metrics.

Your script should process "
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: social_science
---

# Network Influence

## Overview
A comprehensive CLI tool for analyzing social network interaction data to identify influential users and compute network metrics. The script processes CSV data containing user interactions (likes, shares, comments) and calculates weighted influence scores, degree centrality, and combined influence rankings.

## When to Use
- Analyzing social media engagement patterns
- Identifying key influencers in online communities
- Computing network centrality metrics for research
- Ranking users by combined influence and connectivity
- Processing large-scale interaction datasets (500K+ records)

## Inputs
CSV file with required columns:
- `user_id`: Identifier for the user performing the interaction
- `interaction_type`: Type of interaction (like, share, comment)
- `timestamp`: ISO format timestamp (e.g., "2024-01-15T10:30:45Z")
- `target_user`: Identifier for the user being interacted with

## Workflow
1. Execute `scripts/main.py` with input CSV file path
2. Script parses and validates interaction data with ISO timestamp handling
3. Calculates weighted influence scores (share=3, comment=2, like=1)
4. Computes degree centrality using optimized pandas operations
5. Normalizes influence scores to [0,1] range for fair combination
6. Generates combined scores (60% influence, 40% centrality)
7. Produces interaction statistics and top influencer rankings
8. Outputs detailed JSON results and console summary
9. Reference `references/workflow.md` for detailed steps
10. Check `references/pitfalls.md` for common error patterns

## Error Handling
The script includes comprehensive error handling for data parsing issues, timestamp format problems, and performance optimization. When the system encounters malformed data, it logs detailed error messages and gracefully handles missing values. The error handling covers ISO timestamp parsing failures, pandas concat operations with None values, and memory issues with large datasets.

## Common Pitfalls
- ISO timestamp parsing failures with Z suffix
- Scale mismatch between influence scores and centrality scores
- Performance bottlenecks with large datasets in centrality calculations
- Pandas concat errors when groupby operations return None values

## Output Format
JSON file containing:
- `top_influencers`: Ranked list with combined scores and breakdowns
- `user_metrics`: Individual scores for all users (raw, normalized, centrality, combined)
- `network_summary`: Interaction statistics, time periods, and averages
Console displays summary statistics and top N influencers with score breakdowns.
