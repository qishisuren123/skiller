# Example 1: Basic usage with sample data
"""
# edges.csv content:
source_id,target_id,year
1,2,2020
2,3,2021
3,1,2022

# nodes.csv content:
node_id,title,field
1,"Paper A","Computer Science"
2,"Paper B","Mathematics"
3,"Paper C","Computer Science"

# Command:
python main.py --edges edges.csv --nodes nodes.csv --output results/

# Output files created:
# results/node_metrics.csv - Node-level statistics
# results/network_summary.json - Network overview
# results/degree_distribution.csv - Degree frequency distribution
"""

# Example 2: Processing large citation network
"""
import pandas as pd

# Create sample large dataset
edges_data = []
for i in range(1000):
    for j in range(3):  # Each paper cites 3 others on average
        target = (i + j + 1) % 1000 + 1
        if target != i + 1:  # Avoid self-citations
            edges_data.append({'source_id': i+1, 'target_id': target, 'year': 2020 + (i % 5)})

nodes_data = [{'node_id': i+1, 'title': f'Research Paper {i+1}', 
               'field': ['CS', 'Math', 'Physics', 'Biology'][i % 4]} for i in range(1000)]

pd.DataFrame(edges_data).to_csv('large_edges.csv', index=False)
pd.DataFrame(nodes_data).to_csv('large_nodes.csv', index=False)

# Analysis command:
# python main.py --edges large_edges.csv --nodes large_nodes.csv --output large_analysis/
"""
