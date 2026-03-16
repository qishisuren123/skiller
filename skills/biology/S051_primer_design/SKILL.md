---
name: primer_design
description: "# PCR Primer Design Tool

Create a command-line tool that designs PCR primers for given DNA sequences with specified melting temperature (Tm) and GC content constraints.

Your script should accept the"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: biology
---

# PCR Primer Design Tool

## Overview
A command-line tool for designing PCR primers from DNA sequences with customizable melting temperature (Tm) and GC content constraints. The tool accepts both comma-separated sequences and FASTA files, generates candidate primers within specified parameters, and outputs detailed results with summary statistics.

## When to Use
- Designing forward primers for PCR amplification experiments
- Screening multiple gene sequences for optimal primer candidates
- Batch processing of sequences from FASTA files
- Quality control of primer designs with specific Tm and GC requirements

## Inputs
- DNA sequences (comma-separated or FASTA file)
- Primer length constraints (min/max)
- Target melting temperature with tolerance range
- GC content percentage limits
- Output file path for JSON results

## Workflow
1. Execute `scripts/main.py` with sequence input and parameters
2. Tool validates DNA sequences for valid nucleotides (A,T,G,C)
3. Generates all possible primers within length constraints
4. Filters candidates by GC content requirements
5. Calculates melting temperature using 2×AT + 4×GC formula
6. Selects best primer closest to target Tm
7. Outputs results with summary statistics to JSON file
8. Reference `references/workflow.md` for detailed steps

## Error Handling
The tool includes comprehensive error handling for invalid inputs. It will handle file not found errors gracefully and validate sequence formats. When sequences contain invalid characters, the tool logs warnings and continues processing valid sequences. FASTA parsing errors are caught and reported without crashing the application.

## Common Pitfalls
- String parsing errors with single sequences (fixed by proper comma splitting)
- High GC content sequences may not yield valid primers with default constraints
- Tm calculations require careful nucleotide counting to avoid off-by-one errors
- Large sequences in output JSON can be unwieldy (use concise format)
- See `references/pitfalls.md` for detailed error cases and solutions

## Output Format
JSON file containing:
- Primer results for each sequence with selected primer details
- Summary statistics including success rate, average Tm, GC content ranges
- Concise format storing only essential sequence information
- Total candidates generated and processing metrics
