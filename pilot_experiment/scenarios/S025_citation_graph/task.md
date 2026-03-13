Write a Python CLI script to analyze a citation network graph and compute node-level and network-level metrics.

Input: Two CSV files:
- Edges CSV (--edges): columns source_id, target_id, year (a citation from source to target)
- Nodes CSV (--nodes): columns node_id, title, field

Requirements:
1. Use argparse: --edges CSV, --nodes CSV, --output directory
2. Build a directed citation graph from the edge list
3. Compute node-level metrics:
   - in_degree (number of citations received) and out_degree (number of references made)
   - clustering coefficient (local, treating graph as undirected for this calculation)
   - Community detection using simple label propagation:
     * Initialize each node with its own label
     * Iteratively assign each node the most frequent label among its neighbors
     * Run for 10 iterations or until convergence
4. Identify hub nodes: top 10 nodes by in_degree
5. Compute network-level metrics:
   - Total nodes, total edges, graph density
   - Degree distribution: count of nodes at each in-degree value
   - Mean clustering coefficient
   - Number of communities detected
6. Output:
   - node_metrics.csv: node_id, title, field, in_degree, out_degree, clustering_coefficient, community
   - network_summary.json: {n_nodes, n_edges, density, mean_clustering, n_communities, top_hubs: [{node_id, in_degree, title}]}
   - degree_distribution.csv: in_degree, count
7. Print: number of nodes/edges, top 5 hubs, number of communities
