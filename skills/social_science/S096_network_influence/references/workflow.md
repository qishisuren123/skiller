1. Prepare CSV input file with columns: user_id, interaction_type, timestamp, target_user
2. Ensure timestamps are in ISO format (e.g., "2024-01-15T10:30:45Z")
3. Run script: `python scripts/main.py input_file.csv --output results.json --top-n 15`
4. Script validates required columns and parses ISO timestamps
5. Calculates weighted influence scores using interaction type weights (share=3, comment=2, like=1)
6. Computes degree centrality using optimized pandas operations for performance
7. Normalizes influence scores to [0,1] range using min-max normalization
8. Combines scores with 60% influence weight and 40% centrality weight
9. Generates interaction statistics including time periods and averages
10. Outputs JSON file with top influencers, user metrics, and network summary
11. Displays console summary with key findings and top influencer rankings
