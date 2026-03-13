#!/usr/bin/env python3
import argparse
import pandas as pd
import networkx as nx
import json
import os
from collections import defaultdict, Counter

def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze citation network graph')
    parser.add_argument('--edges', required=True, help='Path to edges CSV file')
    parser.add_argument('--nodes', required=True, help='Path to nodes CSV file')
    parser.add_argument('--output', required=True, help='Output directory')
    return parser.parse_args()

def validate_and_clean_data(edges_df, nodes_df):
    """Validate input data and handle edge cases"""
    print("Validating input data...")
    
    # Check required columns
    required_edge_cols = ['source_id', 'target_id', 'year']
    required_node_cols = ['node_id', 'title', 'field']
    
    missing_edge_cols = [col for col in required_edge_cols if col not in edges_df.columns]
    missing_node_cols = [col for col in required_node_cols if col not in nodes_df.columns]
    
    if missing_edge_cols:
        raise ValueError(f"Missing required columns in edges file: {missing_edge_cols}")
    if missing_node_cols:
        raise ValueError(f"Missing required columns in nodes file: {missing_node_cols}")
    
    # Remove rows with missing values in key columns
    initial_edges = len(edges_df)
    initial_nodes = len(nodes_df)
    
    edges_df = edges_df.dropna(subset=['source_id', 'target_id'])
    nodes_df = nodes_df.dropna(subset=['node_id'])
    
    if len(edges_df) < initial_edges:
        print(f"Warning: Removed {initial_edges - len(edges_df)} edges with missing source/target IDs")
    if len(nodes_df) < initial_nodes:
        print(f"Warning: Removed {initial_nodes - len(nodes_df)} nodes with missing node IDs")
    
    # Convert IDs to integers, handling conversion errors
    try:
        edges_df['source_id'] = pd.to_numeric(edges_df['source_id'], errors='coerce').astype('Int64')
        edges_df['target_id'] = pd.to_numeric(edges_df['target_id'], errors='coerce').astype('Int64')
        nodes_df['node_id'] = pd.to_numeric(nodes_df['node_id'], errors='coerce').astype('Int64')
    except Exception as e:
        raise ValueError(f"Error converting IDs to integers: {e}")
    
    # Remove edges with invalid IDs
    edges_df = edges_df.dropna(subset=['source_id', 'target_id'])
    nodes_df = nodes_df.dropna(subset=['node_id'])
    
    # Remove duplicate nodes and edges
    duplicate_nodes = nodes_df.duplicated(subset=['node_id'])
    if duplicate_nodes.any():
        print(f"Warning: Found {duplicate_nodes.sum()} duplicate nodes, keeping first occurrence")
        nodes_df = nodes_df.drop_duplicates(subset=['node_id'], keep='first')
    
    duplicate_edges = edges_df.duplicated(subset=['source_id', 'target_id'])
    if duplicate_edges.any():
        print(f"Warning: Found {duplicate_edges.sum()} duplicate edges, keeping first occurrence")
        edges_df = edges_df.drop_duplicates(subset=['source_id', 'target_id'], keep='first')
    
    # Remove self-loops
    self_loops = edges_df['source_id'] == edges_df['target_id']
    if self_loops.any():
        print(f"Warning: Found {self_loops.sum()} self-loops, removing them")
        edges_df = edges_df[~self_loops]
    
    # Check for orphaned edges
    valid_node_ids = set(nodes_df['node_id'])
    invalid_sources = ~edges_df['source_id'].isin(valid_node_ids)
    invalid_targets = ~edges_df['target_id'].isin(valid_node_ids)
    invalid_edges = invalid_sources | invalid_targets
    
    if invalid_edges.any():
        print(f"Warning: Found {invalid_edges.sum()} edges referencing non-existent nodes, removing them")
        edges_df = edges_df[~invalid_edges]
    
    # Final conversion to standard int
    edges_df['source_id'] = edges_df['source_id'].astype(int)
    edges_df['target_id'] = edges_df['target_id'].astype(int)
    nodes_df['node_id'] = nodes_df['node_id'].astype(int)
    
    print(f"Final data: {len(nodes_df)} nodes, {len(edges_df)} edges")
    return edges_df, nodes_df

def load_data(edges_file, nodes_file):
    """Load and validate edges and nodes data from CSV files"""
    try:
        edges_df = pd.read_csv(edges_file)
        nodes_df = pd.read_csv(nodes_file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Input file not found: {e}")
    except pd.errors.EmptyDataError as e:
        raise ValueError(f"Input file is empty: {e}")
    except Exception as e:
        raise ValueError(f"Error reading CSV files: {e}")
    
    if edges_df.empty:
        raise ValueError("Edges file is empty")
    if nodes_df.empty:
        raise ValueError("Nodes file is empty")
    
    return validate_and_clean_data(edges_df, nodes_df)

def build_graph(edges_df, nodes_df):
    """Build directed citation graph"""
    G = nx.DiGraph()
    
    # Add nodes with attributes
    for _, row in nodes_df.iterrows():
        title = row['title'] if pd.notna(row['title']) else f"Node_{row['node_id']}"
        field = row['field'] if pd.notna(row['field']) else "Unknown"
        G.add_node(int(row['node_id']), title=str(title), field=str(field))
    
    # Add edges
    for _, row in edges_df.iterrows():
        year = row['year'] if pd.notna(row['year']) else None
        G.add_edge(int(row['source_id']), int(row['target_id']), year=year)
    
    return G

def compute_clustering_coefficient(G, node):
    """Compute clustering coefficient for a node (treating graph as undirected)"""
    predecessors = set(G.predecessors(node))
    successors = set(G.successors(node))
    neighbors = list(predecessors.union(successors))
    
    if len(neighbors) < 2:
        return 0.0
    
    # Count edges between neighbors
    edges_between_neighbors = 0
    for i in range(len(neighbors)):
        for j in range(i + 1, len(neighbors)):
            neighbor1, neighbor2 = neighbors[i], neighbors[j]
            if G.has_edge(neighbor1, neighbor2) or G.has_edge(neighbor2, neighbor1):
                edges_between_neighbors += 1
    
    possible_edges = len(neighbors) * (len(neighbors) - 1) // 2
    return edges_between_neighbors / possible_edges

def label_propagation_communities(G, max_iterations=10):
    """Simple label propagation community detection"""
    labels = {int(node): int(node) for node in G.nodes()}
    
    for iteration in range(max_iterations):
        new_labels = {}
        nodes = list(G.nodes())
        
        for node in nodes:
            node = int(node)
            neighbors = list(G.predecessors(node)) + list(G.successors(node))
            neighbors = [int(n) for n in neighbors]
            
            if not neighbors:
                new_labels[node] = labels[node]
                continue
            
            neighbor_labels = [labels[neighbor] for neighbor in neighbors]
            label_counts = Counter(neighbor_labels)
            
            # Break ties by smallest label
            most_common_count = label_counts.most_common(1)[0][1]
            tied_labels = [label for label, count in label_counts.items() if count == most_common_count]
            new_labels[node] = min(tied_labels)
        
        if new_labels == labels:
            print(f"Label propagation converged after {iteration + 1} iterations")
            break
        
        labels = new_labels
    
    return labels

def compute_node_metrics(G, nodes_df):
    """Compute all node-level metrics"""
    communities = label_propagation_communities(G)
    
    node_metrics = []
    
    for _, row in nodes_df.iterrows():
        node_id = int(row['node_id'])
        
        if node_id not in G:
            continue
        
        in_degree = G.in_degree(node_id)
        out_degree = G.out_degree(node_id)
        clustering_coeff = compute_clustering_coefficient(G, node_id)
        community = communities[node_id]
        
        node_metrics.append({
            'node_id': node_id,
            'title': row['title'],
            'field': row['field'],
            'in_degree': in_degree,
            'out_degree': out_degree,
            'clustering_coefficient': clustering_coeff,
            'community': community
        })
    
    return pd.DataFrame(node_metrics)

def compute_network_metrics(G, node_metrics_df):
    """Compute network-level metrics"""
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    
    max_possible_edges = n_nodes * (n_nodes - 1)
    density = n_edges / max_possible_edges if max_possible_edges > 0 else 0.0
    
    mean_clustering = float(node_metrics_df['clustering_coefficient'].mean())
    n_communities = int(node_metrics_df['community'].nunique())
    
    # Top hubs with proper type conversion
    top_hubs_df = node_metrics_df.nlargest(10, 'in_degree')[['node_id', 'in_degree', 'title']]
    top_hubs = []
    for _, row in top_hubs_df.iterrows():
        top_hubs.append({
            'node_id': int(row['node_id']),
            'in_degree': int(row['in_degree']),
            'title': str(row['title'])
        })
    
    degree_dist = node_metrics_df['in_degree'].value_counts().sort_index()
    degree_distribution = pd.DataFrame({
        'in_degree': degree_dist.index,
        'count': degree_dist.values
    })
    
    network_summary = {
        'n_nodes': int(n_nodes),
        'n_edges': int(n_edges),
        'density': float(density),
        'mean_clustering': mean_clustering,
        'n_communities': n_communities,
        'top_hubs': top_hubs
    }
    
    return network_summary, degree_distribution

def main():
    args = parse_arguments()
    
    os.makedirs(args.output, exist_ok=True)
    
    # Load data and build graph
    edges_df, nodes_df = load_data(args.edges, args.nodes)
    G = build_graph(edges_df, nodes_df)
    
    print(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Compute metrics
    node_metrics_df = compute_node_metrics(G, nodes_df)
    network_summary, degree_distribution = compute_network_metrics(G, node_metrics_df)
    
    # Save outputs
    node_metrics_df.to_csv(os.path.join(args.output, 'node_metrics.csv'), index=False)
    
    with open(os.path.join(args.output, 'network_summary.json'), 'w') as f:
        json.dump(network_summary, f, indent=2, default=str)
    
    degree_distribution.to_csv(os.path.join(args.output, 'degree_distribution.csv'), index=False)
    
    # Print summary
    print(f"Number of nodes: {network_summary['n_nodes']}")
    print(f"Number of edges: {network_summary['n_edges']}")
    print(f"Number of communities: {network_summary['n_communities']}")
    print("\nTop 5 hubs:")
    for i, hub in enumerate(network_summary['top_hubs'][:5]):
        print(f"{i+1}. {hub['title']} (in_degree: {hub['in_degree']})")

if __name__ == "__main__":
    main()
