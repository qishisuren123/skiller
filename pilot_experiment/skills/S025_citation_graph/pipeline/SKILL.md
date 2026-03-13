# Citation Network Analysis CLI Development

## Overview
This skill helps build a robust Python CLI script for analyzing citation networks, including node-level metrics (clustering coefficients, community detection) and network-level statistics. The skill covers proper data validation, error handling, and performance considerations for large-scale networks.

## Workflow
1. **Set up argument parsing** with required input files (edges CSV, nodes CSV) and output directory
2. **Implement data validation and cleaning**:
   - Check for required columns in input files
   - Handle missing values, duplicates, and orphaned edges
   - Convert data types properly to avoid serialization issues
3. **Build the network graph** using NetworkX DiGraph for directed citation networks
4. **Compute node-level metrics**:
   - In-degree and out-degree (citation counts)
   - Clustering coefficients (treating graph as undirected)
   - Community detection using label propagation
5. **Calculate network-level metrics**:
   - Graph density, mean clustering coefficient
   - Degree distributions and hub identification
6. **Export results** in multiple formats (CSV, JSON) with proper type conversion
7. **Add performance optimizations** for large networks

## Common Pitfalls
- **Numpy type serialization errors**: Convert numpy.int64 to Python int before JSON serialization
- **Unhashable type errors**: Ensure consistent integer types throughout, especially in graph operations
- **Incorrect clustering coefficients**: Must properly handle undirected neighbor relationships in directed graphs
- **Label propagation instability**: Add tie-breaking rules and handle isolated nodes
- **Missing data handling**: Validate input files and gracefully handle missing nodes referenced in edges
- **Performance bottlenecks**: Pre-compute neighbor lists and use efficient data structures for large networks

## Error Handling
- Validate CSV file format and required columns before processing
- Handle file I/O errors with informative messages
- Check for empty datasets and malformed data
- Remove orphaned edges that reference non-existent nodes
- Provide fallback values for missing node attributes
- Add convergence checking for iterative algorithms

## Quick Reference
