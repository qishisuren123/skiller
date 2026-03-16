1. Install required dependencies using pip install -r requirements.txt
2. Prepare command line arguments including species name, weights, and output directory
3. Execute main script with python scripts/main.py -o ./results -s "Species Name" -w "0.25,0.25,0.25,0.25"
4. System generates synthetic environmental data layers with spatial correlation
5. Individual suitability functions calculate scores for temperature, precipitation, elevation, and vegetation
6. Weighted HSI computation combines individual scores using user-specified weights
7. Summary statistics calculation identifies optimal habitat locations and coverage percentages
8. File export operations save CSV grid data, JSON summary statistics, and PNG visualization
9. Review output files for analysis results and habitat recommendations
10. Adjust parameters and re-run for sensitivity analysis or different species requirements
