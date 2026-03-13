# PCR Primer Design Tool

Create a command-line tool that designs PCR primers for given DNA sequences with specified melting temperature (Tm) and GC content constraints.

Your script should accept the following arguments:
- `--sequences` or `--input`: Input DNA sequences (comma-separated or file path to FASTA-like format)
- `--output` or `--out`: Output JSON file containing primer designs
- `--min-length`: Minimum primer length (default: 18)
- `--max-length`: Maximum primer length (default: 25)
- `--target-tm`: Target melting temperature in Celsius (default: 60)
- `--tm-tolerance`: Acceptable deviation from target Tm (default: 5)
- `--min-gc`: Minimum GC content percentage (default: 40)
- `--max-gc`: Maximum GC content percentage (default: 60)

## Requirements:

1. **Sequence Processing**: Parse input DNA sequences and validate they contain only valid nucleotides (A, T, G, C, case-insensitive).

2. **Primer Generation**: For each sequence, generate all possible forward primers from the 5' end within the specified length range that meet the GC content constraints.

3. **Melting Temperature Calculation**: Calculate Tm for each primer using the basic formula: Tm = 2×(A+T) + 4×(G+C). Filter primers within the specified Tm tolerance range.

4. **GC Content Analysis**: Calculate GC content percentage for each primer and ensure it falls within the specified range.

5. **Primer Selection**: For each input sequence, select the primer closest to the target Tm. If multiple primers have the same Tm distance, prefer the one with GC content closest to 50%.

6. **Output Generation**: Save results as JSON with sequence names, selected primers, their properties (length, Tm, GC content), and summary statistics.

The tool should handle multiple sequences and provide comprehensive primer design information for PCR optimization.
