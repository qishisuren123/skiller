# Example 1: Basic B-factor analysis
python main.py "15.2,23.1,18.7,45.3,67.2,34.1,12.8,89.4,56.7,23.9"

# Expected output files:
# - bfactor_analysis.json: Statistical summary and flexible regions
# - bfactor_analysis.png: B-factor profile visualization

# Example 2: Normalized analysis with custom output
python main.py "8.1,12.3,45.7,23.4,67.8,89.2,34.5,56.1,78.9,43.2,67.5,23.8" --normalize --output protein_flexibility

# Sample JSON output structure:
{
  "statistics": {
    "mean": 45.87,
    "median": 44.95,
    "std": 24.13,
    "q75": 65.25
  },
  "flexible_regions": {
    "threshold": 65.25,
    "positions": [4, 5, 8, 10],
    "segments": [[4, 5], [8, 8], [10, 10]],
    "count": 4
  },
  "normalized_bfactors": [0.0, 5.2, 46.3, 18.8, 73.6, 100.0, 32.5, 59.1, 87.2, 43.1, 73.1, 19.3]
}
