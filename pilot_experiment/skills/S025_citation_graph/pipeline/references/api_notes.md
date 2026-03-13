# NetworkX DiGraph operations
G = nx.DiGraph()  # Create directed graph
G.add_node(node_id, **attributes)  # Add node with attributes
G.add_edge(source, target, **attributes)  # Add edge with attributes
G.predecessors(node)  # Get incoming neighbors
G.successors(node)  # Get outgoing neighbors
G.in_degree(node)  # Get in-degree
G.out_degree(node)  # Get out-degree
G.has_edge(source, target)  # Check if edge exists

# Pandas data validation
pd.to_numeric(series, errors='coerce')  # Convert to numeric, NaN for errors
df.dropna(subset=['col1', 'col2'])  # Remove rows with NaN in specified columns
df.duplicated(subset=['col'])  # Find duplicate rows
df.drop_duplicates(subset=['col'], keep='first')  # Remove duplicates

# JSON serialization with type conversion
json.dump(data, file, indent=2, default=str)  # default=str handles remaining type issues
