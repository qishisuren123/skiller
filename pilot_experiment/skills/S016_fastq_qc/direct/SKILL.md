# FASTQ Quality Control and Trimming

## Overview
This skill enables processing of FASTQ sequencing data files to compute quality statistics and perform 3' end quality trimming based on Phred quality scores, with comprehensive reporting of before/after metrics.

## Workflow
1. Parse command-line arguments for input/output files and quality thresholds
2. Read FASTQ file in 4-line blocks (@header, sequence, +, quality scores)
3. Decode Phred+33 quality scores (ASCII value - 33) and compute initial statistics
4. Trim each read from 3' end until encountering base with quality >= min_quality
5. Filter out reads shorter than min_length after trimming
6. Write trimmed reads to output FASTQ file maintaining original format
7. Generate comprehensive JSON report and print summary statistics

## Common Pitfalls
- **Quality score encoding confusion**: Always verify Phred+33 encoding (ASCII - 33), not Phred+64
- **FASTQ format parsing errors**: Ensure strict 4-line per read parsing; handle files without trailing newlines
- **Memory issues with large files**: Process reads iteratively rather than loading entire file into memory
- **Empty reads after trimming**: Check for zero-length sequences before length filtering to avoid downstream errors
- **Quality distribution binning**: Use appropriate bin ranges (0-40) for Phred scores to capture meaningful quality ranges

## Error Handling
- Validate FASTQ format integrity (4 lines per read, matching sequence/quality lengths)
- Handle file I/O errors with descriptive messages for missing input files
- Check for empty input files and malformed quality score characters
- Ensure output directory exists before writing files

## Quick Reference
