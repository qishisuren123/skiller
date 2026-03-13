# Social Network Influence Analysis

## Overview
This skill helps analyze social network interaction data to identify influential users by computing weighted influence scores, network centrality measures, and combined influence metrics. It processes user interactions (likes, shares, comments) and generates comprehensive influence rankings with network statistics.

## Workflow
1. **Parse and validate interaction data** - Load CSV/JSON data containing user_id, target_user, interaction_type, and timestamp fields
2. **Calculate weighted influence scores** - Apply interaction weights (share=3, comment=2, like=1) to compute each user's outgoing influence
3. **Compute degree centrality** - Calculate normalized centrality based on total unique connections (incoming + outgoing)
4. **Generate combined influence metric** - Blend influence score (60%) and centrality (40%) for final ranking
5. **Analyze interaction patterns** - Compute summary statistics including interaction rates and type distributions
6. **Identify top influencers** - Rank users by combined metric and extract top N influencers
7. **Export results to JSON** - Save rankings, individual metrics, and network statistics

## Common Pitfalls
- **Self-interactions contamination**: Including users interacting with themselves inflates centrality scores. Solution: Filter out records where user_id == target_user
- **Timestamp parsing inconsistencies**: Mixed date formats cause analysis errors. Solution: Use pandas.to_datetime() with error handling and format inference
- **Zero-division in normalization**: Networks with single users cause division by zero. Solution: Check for min==max before normalizing and handle edge cases
- **Memory issues with large networks**: Loading massive interaction datasets crashes the program. Solution: Use chunked processing with pandas.read_csv(chunksize=10000)
- **Missing interaction types**: Undefined interaction types break weight calculations. Solution: Use defaultdict or .get() with fallback weights

## Error Handling
- Validate required columns exist in input data before processing
- Handle missing timestamps by using median timestamp or current date
- Skip malformed records and log warnings rather than crashing
- Implement graceful fallbacks for empty datasets (return empty results structure)
- Catch JSON serialization errors for non-serializable numpy types using custom encoder

## Quick Reference
