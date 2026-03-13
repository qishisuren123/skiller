#!/usr/bin/env python3
import argparse
import json
import sys
from collections import Counter

def parse_fastq(filename):
    """Generator to parse FASTQ file in 4-line blocks"""
    with open(filename, 'r') as f:
        while True:
            header = f.readline().strip()
            if not header:
                break
            if not header.startswith('@'):
                raise ValueError(f"Invalid FASTQ header: {header}")
            
            sequence = f.readline().strip()
            plus = f.readline().strip()
            quality = f.readline().strip()
            
            if not plus.startswith('+'):
                raise ValueError(f"Invalid FASTQ separator: {plus}")
            if len(sequence) != len(quality):
                raise ValueError(f"Sequence and quality length mismatch")
            
            yield header, sequence, quality

def quality_scores_from_string(quality_string):
    """Convert Phred+33 quality string to numeric scores"""
    return [ord(c) - 33 for c in quality_string]

def mean_quality(quality_string):
    """Calculate mean quality score from quality string"""
    if not quality_string:
        return 0
    scores = quality_scores_from_string(quality_string)
    return sum(scores) / len(scores)

def trim_read_3prime(sequence, quality, min_qual):
    """Trim read from 3' end until base quality >= min_qual"""
    qual_scores = quality_scores_from_string(quality)
    trim_pos = len(sequence)
    
    # Find first position from 3' end with quality >= min_qual
    for i in range(len(qual_scores) - 1, -1, -1):
        if qual_scores[i] >= min_qual:
            break
        trim_pos = i
    
    return sequence[:trim_pos], quality[:trim_pos]

def quality_distribution(quality_strings):
    """Calculate quality score distribution"""
    all_scores = []
    for qual_str in quality_strings:
        all_scores.extend(quality_scores_from_string(qual_str))
    
    counter = Counter(all_scores)
    # Create distribution dict with scores 0-40
    distribution = {i: counter.get(i, 0) for i in range(41)}
    return distribution

def main():
    parser = argparse.ArgumentParser(description='FASTQ quality trimming and statistics')
    parser.add_argument('--input', required=True, help='Input FASTQ file')
    parser.add_argument('--output', required=True, help='Output trimmed FASTQ file')
    parser.add_argument('--report', required=True, help='Output JSON report file')
    parser.add_argument('--min-quality', type=int, default=20, help='Minimum quality threshold (default: 20)')
    parser.add_argument('--min-length', type=int, default=50, help='Minimum read length after trimming (default: 50)')
    
    args = parser.parse_args()
    
    # Storage for statistics
    original_reads = []
    trimmed_reads = []
    original_qualities = []
    trimmed_qualities = []
    
    total_reads = 0
    passed_reads = 0
    
    try:
        # Process FASTQ file
        with open(args.output, 'w') as out_file:
            for header, sequence, quality in parse_fastq(args.input):
                total_reads += 1
                
                # Store original data for statistics
                original_reads.append(len(sequence))
                original_qualities.append(quality)
                
                # Trim read from 3' end
                trimmed_seq, trimmed_qual = trim_read_3prime(sequence, quality, args.min_quality)
                
                # Filter by minimum length
                if len(trimmed_seq) >= args.min_length:
                    passed_reads += 1
                    trimmed_reads.append(len(trimmed_seq))
                    trimmed_qualities.append(trimmed_qual)
                    
                    # Write to output file
                    out_file.write(f"{header}\n")
                    out_file.write(f"{trimmed_seq}\n")
                    out_file.write("+\n")
                    out_file.write(f"{trimmed_qual}\n")
        
        # Calculate statistics
        mean_length_before = sum(original_reads) / len(original_reads) if original_reads else 0
        mean_length_after = sum(trimmed_reads) / len(trimmed_reads) if trimmed_reads else 0
        mean_quality_before = sum(mean_quality(q) for q in original_qualities) / len(original_qualities) if original_qualities else 0
        mean_quality_after = sum(mean_quality(q) for q in trimmed_qualities) / len(trimmed_qualities) if trimmed_qualities else 0
        
        # Generate report
        report = {
            "total_reads": total_reads,
            "passed_reads": passed_reads,
            "mean_quality_before": round(mean_quality_before, 2),
            "mean_quality_after": round(mean_quality_after, 2),
            "mean_length_before": round(mean_length_before, 2),
            "mean_length_after": round(mean_length_after, 2),
            "quality_distribution": quality_distribution(original_qualities)
        }
        
        # Write JSON report
        with open(args.report, 'w') as report_file:
            json.dump(report, report_file, indent=2)
        
        # Print summary
        trim_rate = ((total_reads - passed_reads) / total_reads * 100) if total_reads > 0 else 0
        quality_improvement = mean_quality_after - mean_quality_before
        
        print(f"FASTQ Quality Trimming Results:")
        print(f"Reads before: {total_reads}")
        print(f"Reads after: {passed_reads}")
        print(f"Trim rate: {trim_rate:.1f}%")
        print(f"Mean quality improvement: {quality_improvement:+.2f}")
        print(f"Mean length before: {mean_length_before:.1f}")
        print(f"Mean length after: {mean_length_after:.1f}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
