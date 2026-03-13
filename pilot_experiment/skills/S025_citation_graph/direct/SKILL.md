# Citation Network Analysis

## Overview
This skill enables analysis of academic citation networks by computing node-level metrics (degrees, clustering, communities) and network-level statistics from CSV edge and node data, outputting comprehensive metrics and summaries.

## Workflow
1. Parse command-line arguments for edges CSV, nodes CSV, and output directory paths
2. Load and validate CSV files, ensuring required columns exist and data integrity
3. Build directed graph from edge list, adding node attributes from nodes CSV
4. Compute node-level metrics: in/out degrees, clustering coefficients (undirected), and community labels via label propagation
5. Calculate network-level statistics: density, degree distribution, mean clustering, and identify top hubs
6. Export results to three files: node_metrics.csv, network_summary.json, and degree_distribution.csv
7. Print summary statistics including node/edge counts, top hubs, and community count

## Common Pitfalls
- **Missing nodes in edge list**: Edges may reference node_ids not in nodes CSV - create placeholder nodes with empty attributes rather than failing
- **Self-loops and duplicate edges**: Citation data often contains self-citations and duplicate entries - remove self-loops and deduplicate edges before analysis
- **Clustering coefficient for isolated nodes**: Nodes with degree < 2 have undefined clustering - return 0.0 for these cases
- **Community convergence**: Label propagation may not converge in 10 iterations - track label changes and stop early if no changes occur
- **Empty output directory**: Ensure output directory exists before writing files - create it if missing to avoid file write errors

## Error Handling
- Validate CSV file existence and readability before processing
- Check for required columns in both CSV files and provide clear error messages
- Handle nodes referenced in edges but missing from nodes CSV by creating minimal node entries
- Catch JSON serialization errors when writing network summary
- Implement graceful handling of disconnected graph components in clustering calculations

## Quick Reference
