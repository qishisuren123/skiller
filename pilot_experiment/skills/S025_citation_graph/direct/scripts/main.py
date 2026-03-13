import argparse
import pandas as pd
import numpy as np
import json
import os
from collections import Counter, defaultdict

def load_and_validate_data(edges_file, nodes_file):
    """Load CSV files and validate required columns."""
    try:
        edges_df = pd.read_csv(edges_file)
        nodes_df = pd.read_csv(nodes_file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"CSV file not found: {e}")
    
    # Validate required columns
    required_edge_cols = ['source_id', 'target_id', 'year']
    required_node_cols = ['node_id', 'title', 'field']
    
    if not all(col in edges_df.columns for col in required_edge_cols):
        raise ValueError(f"Edges CSV missing required columns: {required_edge_cols}")
    
    if not all(col in nodes_df.columns for col in required_node_cols):
        raise ValueError(f"Nodes CSV missing required columns: {required_node_cols}")
    
    return edges_df, nodes_df

def build_citation_graph(edges_df, nodes_df):
    """Build directed citation graph from edge list."""
    # Remove self-loops and duplicates
    edges_df = edges_df[edges_df['source_id'] != edges_df['target_id']].drop_duplicates(
        subset=['source_id', 'target_id'])
    
    # Create node lookup
    node_attrs = nodes_df.set_index('node_id').to_dict('index')
    
    # Build adjacency lists
    graph = defaultdict(set)
    reverse_graph = defaultdict(set)
    all_nodes = set(nodes_df['node_id'])
    
    for _, row in edges_df.iterrows():
        source, target = row['source_id'], row['target_id']
        graph[source].add(target)
        reverse_graph[target].add(source)
        
        # Add missing nodes with placeholder attributes
        if source not in all_nodes:
            node_attrs[source] = {'title': f'Unknown_{source}', 'field': 'Unknown'}
            all_nodes.add(source)
        if target not in all_nodes:
            node_attrs[target] = {'title': f'Unknown_{target}', 'field': 'Unknown'}
            all_nodes.add(target)
    
    return graph, reverse_graph, node_attrs, all_nodes

def compute_clustering_coefficient(node, graph, reverse_graph):
    """Compute clustering coefficient treating graph as undirected."""
    # Get all neighbors (in + out, treating as undirected)
    neighbors = graph[node] | reverse_graph[node]
    neighbors.discard(node)  # Remove self if present
    
    if len(neighbors) < 2:
        return 0.0
    
    # Count edges between neighbors
    edges_between_neighbors = 0
    neighbors_list = list(neighbors)
    
    for i, neighbor1 in enumerate(neighbors_list):
        for neighbor2 in neighbors_list[i+1:]:
            if (neighbor2 in graph[neighbor1] or neighbor1 in graph[neighbor2] or
                neighbor2 in reverse_graph[neighbor1] or neighbor1 in reverse_graph[neighbor2]):
                edges_between_neighbors += 1
    
    possible_edges = len(neighbors) * (len(neighbors) - 1) // 2
    return edges_between_neighbors / possible_edges if possible_edges > 0 else 0.0

def label_propagation(graph, reverse_graph, all_nodes, max_iter=10):
    """Community detection using label propagation."""
    labels = {node: node for node in all_nodes}
    
    for iteration in range(max_iter):
        new_labels = {}
        changed = False
        
        for node in all_nodes:
            # Get all neighbors (undirected)
            neighbors = list(graph[node] | reverse_graph[node])
            
            if neighbors:
                neighbor_labels = [labels[neighbor] for neighbor in neighbors]
                most_common_label = Counter(neighbor_labels).most_common(1)[0][0]
                new_labels[node] = most_common_label
            else:
                new_labels[node] = labels[node]
            
            if new_labels[node] != labels[node]:
                changed = True
        
        labels = new_labels
        if not changed:
            break
    
    return labels

def compute_node_metrics(graph, reverse_graph, node_attrs, all_nodes):
    """Compute all node-level metrics."""
    communities = label_propagation(graph, reverse_graph, all_nodes)
    
    node_metrics = []
    for node in all_nodes:
        in_degree = len(reverse_graph[node])
        out_degree = len(graph[node])
        clustering = compute_clustering_coefficient(node, graph, reverse_graph)
        
        node_metrics.append({
            'node_id': node,
            'title': node_attrs[node]['title'],
            'field': node_attrs[node]['field'],
            'in_degree': in_degree,
            'out_degree': out_degree,
            'clustering_coefficient': clustering,
            'community': communities[node]
        })
    
    return node_metrics

def compute_network_metrics(graph, reverse_graph, all_nodes, node_metrics):
    """Compute network-level statistics."""
    n_nodes = len(all_nodes)
    n_edges = sum(len(targets) for targets in graph.values())
    density = n_edges / (n_nodes * (n_nodes - 1)) if n_nodes > 1 else 0.0
    
    # Degree distribution
    in_degrees = [len(reverse_graph[node]) for node in all_nodes]
    degree_dist = Counter(in_degrees)
    
    # Mean clustering
    clustering_values = [m['clustering_coefficient'] for m in node_metrics]
    mean_clustering = np.mean(clustering_values) if clustering_values else 0.0
    
    # Communities
    communities = set(m['community'] for m in node_metrics)
    n_communities = len(communities)
    
    # Top hubs
    sorted_nodes = sorted(node_metrics, key=lambda x: x['in_degree'], reverse=True)
    top_hubs = [{'node_id': node['node_id'], 'in_degree': node['in_degree'], 
                 'title': node['title']} for node in sorted_nodes[:10]]
    
    return {
        'n_nodes': n_nodes,
        'n_edges': n_edges,
        'density': density,
        'mean_clustering': mean_clustering,
        'n_communities': n_communities,
        'top_hubs': top_hubs
    }, degree_dist

def main():
    parser = argparse.ArgumentParser(description='Analyze citation network graph')
    parser.add_argument('--edges', required=True, help='Path to edges CSV file')
    parser.add_argument('--nodes', required=True, help='Path to nodes CSV file')
    parser.add_argument('--output', required=True, help='Output directory path')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Load and validate data
    edges_df, nodes_df = load_and_validate_data(args.edges, args.nodes)
    
    # Build graph
    graph, reverse_graph, node_attrs, all_nodes = build_citation_graph(edges_df, nodes_df)
    
    # Compute metrics
    node_metrics = compute_node_metrics(graph, reverse_graph, node_attrs, all_nodes)
    network_summary, degree_dist = compute_network_metrics(graph, reverse_graph, all_nodes, node_metrics)
    
    # Save results
    node_metrics_df = pd.DataFrame(node_metrics)
    node_metrics_df.to_csv(os.path.join(args.output, 'node_metrics.csv'), index=False)
    
    with open(os.path.join(args.output, 'network_summary.json'), 'w') as f:
        json.dump(network_summary, f, indent=2)
    
    degree_dist_df = pd.DataFrame([{'in_degree': k, 'count': v} for k, v in degree_dist.items()])
    degree_dist_df = degree_dist_df.sort_values('in_degree')
    degree_dist_df.to_csv(os.path.join(args.output, 'degree_distribution.csv'), index=False)
    
    # Print summary
    print(f"Network Analysis Complete:")
    print(f"Nodes: {network_summary['n_nodes']}")
    print(f"Edges: {network_summary['n_edges']}")
    print(f"Communities: {network_summary['n_communities']}")
    print(f"\nTop 5 Hubs:")
    for i, hub in enumerate(network_summary['top_hubs'][:5], 1):
        print(f"{i}. {hub['title']} (ID: {hub['node_id']}, Citations: {hub['in_degree']})")

if __name__ == "__main__":
    main()
