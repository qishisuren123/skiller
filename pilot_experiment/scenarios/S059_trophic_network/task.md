# Trophic Network Analysis Tool

Create a command-line tool that analyzes food web structure and computes trophic levels from predator-prey interaction data.

Your script should accept a CSV file containing species interaction data with columns: predator, prey, and interaction_strength (0-1). The tool should construct a trophic network, calculate trophic levels for each species, and analyze network properties.

## Requirements

1. **Parse interaction data**: Read the CSV file and construct an adjacency matrix representing the food web network. Handle cases where species appear as predators but not prey (top predators) and vice versa (primary producers).

2. **Calculate trophic levels**: Compute trophic levels using the standard ecological formula where primary producers have trophic level 1, and each consumer's trophic level is 1 + weighted average of its prey's trophic levels, weighted by interaction strength.

3. **Network metrics**: Calculate and report key network properties including:
   - Number of species at each trophic level
   - Connectance (fraction of possible links that exist)
   - Mean trophic level
   - Maximum food chain length

4. **Identify keystone species**: Determine species with disproportionately high impact by calculating each species' betweenness centrality in the network.

5. **Output results**: Save results to a JSON file containing species trophic levels, network metrics, and top 3 keystone species ranked by centrality.

6. **Generate network visualization**: Create a network diagram showing species as nodes (sized by trophic level) and interactions as directed edges (thickness proportional to interaction strength). Save as PNG file.

## Command Line Interface
