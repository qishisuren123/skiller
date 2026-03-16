## String Parsing Error with Single Sequences

**Error**: AttributeError: 'str' object has no attribute 'strip' when processing single sequence input

**Root Cause**: The split(',') method on single sequences without commas creates a list of individual characters, and calling strip() on characters fails

**Fix**: Implemented proper sequence parsing logic that handles both single sequences and comma-separated lists by checking if seq.strip() is valid before processing

## High GC Content Filtering

**Error**: No valid primers found for sequences with naturally high GC content

**Root Cause**: Default maximum GC content of 60% was too restrictive for GC-rich sequences

**Fix**: Made GC content limits configurable via command-line arguments and added debug output to show why primers are filtered out

## Tm Calculation Verification

**Error**: Suspected incorrect melting temperature calculations

**Root Cause**: User needed to verify the 2×AT + 4×GC formula was being applied correctly

**Fix**: Added detailed debug output showing individual nucleotide counts and step-by-step Tm calculation to enable verification

## Large JSON Output Files

**Error**: JSON output files becoming unwieldy with full sequence storage for large genes

**Root Cause**: Storing complete input sequences (several kilobases) in output made files difficult to work with

**Fix**: Modified output format to store only sequence length and preview (first 50 nucleotides) while adding comprehensive summary statistics
