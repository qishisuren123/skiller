1. Parse command-line arguments including sequence input, output file, and primer constraints
2. Set up logging configuration based on debug flag
3. Parse input sequences using parse_input_sequences() function from scripts/main.py
4. Validate each DNA sequence contains only A, T, G, C nucleotides
5. Generate primer candidates within specified length range for each sequence
6. Filter candidates by GC content constraints (min_gc to max_gc percentage)
7. Calculate melting temperature using 2×AT + 4×GC formula for each candidate
8. Select best primer closest to target Tm with GC content as tiebreaker
9. Compile results with sequence previews and primer statistics
10. Calculate summary statistics including success rate and average values
11. Output structured JSON with summary, parameters, and detailed results
12. Log completion status and success metrics to console
