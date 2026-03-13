# Data type conversion for JSON serialization
network_summary = {
    'n_nodes': int(G.number_of_nodes()),  # Convert from numpy
    'density': float(density),  # Ensure float type
    'top_hubs': [{'node_id': int(row['node_id'])} for _, row in df.iterrows()]
}

# Clustering coefficient calculation
def compute_clustering_coefficient(G, node):
    predecessors = set(G.predecessors(node))
    successors = set(G.successors(node))
    neighbors = list(predecessors.union(successors))
    
    if len(neighbors) < 2:
        return 0.0
    
    edges_between_neighbors = 0
    for i in range(len(neighbors)):
        for j in range(i + 1, len(neighbors)):
            if G.has_edge(neighbors[i], neighbors[j]) or G.has_edge(neighbors[j], neighbors[i]):
                edges_between_neighbors += 1
    
    possible_edges = len(neighbors) * (len(neighbors) - 1) // 2
    return edges_between_neighbors / possible_edges

# Label propagation with tie-breaking
label_counts = Counter(neighbor_labels)
most_common_count = label_counts.most_common(1)[0][1]
tied_labels = [label for label, count in label_counts.items() if count == most_common_count]
new_labels[node] = min(tied_labels)  # Break ties consistently
