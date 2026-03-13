Write a Python CLI script to compute quality statistics and perform quality trimming on FASTQ sequencing data.

Input: A FASTQ file (text format with 4 lines per read: @header, sequence, +, quality).

Requirements:
1. Use argparse: --input FASTQ, --output trimmed FASTQ, --report JSON, --min-quality (default 20), --min-length (default 50)
2. Parse the FASTQ file (quality scores are Phred+33 encoded: ASCII char - 33 = quality)
3. Trim reads from the 3' end until base quality >= min_quality
4. Discard reads shorter than min_length after trimming
5. Output: trimmed FASTQ file, report JSON with {total_reads, passed_reads, mean_quality_before, mean_quality_after, mean_length_before, mean_length_after, quality_distribution}
6. Print: reads before/after, trim rate, mean quality improvement
