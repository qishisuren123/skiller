#!/usr/bin/env python3
import argparse
import json
import sys
from collections import defaultdict

def parse_fastq_streaming(filename):
    """Generator that yields one FASTQ record at a time"""
    try:
        with open(filename, 'r') as f:
            line_num = 0
            while True:
                header = f.readline().strip()
                line_num += 1
                if not header:
                    break
                
                if not header.startswith('@'):
                    raise ValueError(f"Line {line_num}: Expected header starting with '@', got: {header}")
                
                sequence = f.readline().strip()
                line_num += 1
                if not sequence:
                    raise ValueError(f"Line {line_num}: Unexpected end of file, missing sequence")
                
                plus = f.readline().strip()
                line_num += 1
                if not plus.startswith('+'):
                    raise ValueError(f"Line {line_num}: Expected '+', got: {plus}")
                
                quality = f.readline().strip()
                line_num += 1
                if not quality:
                    raise ValueError(f"Line {line_num}: Unexpected end of file, missing quality")
                
                if len(sequence) != len(quality):
                    raise ValueError(f"Line {line_num}: Sequence and quality length mismatch")
                
                yield (header, sequence, quality)
    
    except FileNotFoundError:
        print(f"Error: Input file '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing FASTQ file: {e}")
        sys.exit(1)

def quality_to_phred(quality_string):
    """Convert quality string to Phred scores with error handling"""
    try:
        scores = []
        for char in quality_string:
            score = ord(char) - 33
            if score < 0 or score > 93:
                print(f"Warning: Invalid quality score character '{char}' (score: {score})")
                score = max(0, min(93, score))
            scores.append(score)
        return scores
    except Exception as e:
        print(f"Error converting quality scores: {e}")
        return [0] * len(quality_string)

def calculate_mean_quality(quality_string):
    """Calculate mean quality score"""
    phred_scores = quality_to_phred(quality_string)
    return sum(phred_scores) / len(phred_scores) if phred_scores else 0

def trim_read(sequence, quality, min_quality):
    """Trim read from 3' end until base quality >= min_quality"""
    if not sequence or not quality:
        return "", ""
    
    phred_scores = quality_to_phred(quality)
    trim_pos = 0
    
    for i in range(len(phred_scores) - 1, -1, -1):
        if phred_scores[i] >= min_quality:
            trim_pos = i + 1
            break
    
    return sequence[:trim_pos], quality[:trim_pos]

def main():
    parser = argparse.ArgumentParser(description='FASTQ quality trimming')
    parser.add_argument('--input', required=True, help='Input FASTQ file')
    parser.add_argument('--output', required=True, help='Output trimmed FASTQ file')
    parser.add_argument('--report', required=True, help='Output JSON report')
    parser.add_argument('--min-quality', type=int, default=20, help='Minimum quality score')
    parser.add_argument('--min-length', type=int, default=50, help='Minimum read length')
    
    args = parser.parse_args()
    
    # Initialize counters and accumulators
    total_reads = 0
    passed_reads = 0
    quality_dist = defaultdict(int)
    
    # Accumulators for statistics
    sum_original_quality = 0
    sum_original_length = 0
    sum_passed_original_quality = 0
    sum_passed_original_length = 0
    sum_trimmed_quality = 0
    sum_trimmed_length = 0
    
    # Process reads one at a time
    try:
        with open(args.output, 'w') as output_file:
            for header, sequence, quality in parse_fastq_streaming(args.input):
                total_reads += 1
                
                # Calculate original statistics
                original_quality = calculate_mean_quality(quality)
                original_length = len(sequence)
                sum_original_quality += original_quality
                sum_original_length += original_length
                
                # Update quality distribution
                for score in quality_to_phred(quality):
                    quality_dist[score] += 1
                
                # Trim the read
                trimmed_seq, trimmed_qual = trim_read(sequence, quality, args.min_quality)
                
                # Check if it passes length filter
                if len(trimmed_seq) >= args.min_length:
                    passed_reads += 1
                    
                    # Write to output file
                    output_file.write(f"{header}\n{trimmed_seq}\n+\n{trimmed_qual}\n")
                    
                    # Collect statistics for passed reads
                    trimmed_quality = calculate_mean_quality(trimmed_qual)
                    trimmed_length = len(trimmed_seq)
                    
                    sum_passed_original_quality += original_quality
                    sum_passed_original_length += original_length
                    sum_trimmed_quality += trimmed_quality
                    sum_trimmed_length += trimmed_length
                
                # Progress indicator for large files
                if total_reads % 100000 == 0:
                    print(f"Processed {total_reads} reads...")
    
    except Exception as e:
        print(f"Error processing reads: {e}")
        sys.exit(1)
    
    if total_reads == 0:
        print("Error: No reads found in input file")
        sys.exit(1)
    
    # Calculate final statistics
    mean_original_quality = sum_original_quality / total_reads
    mean_original_length = sum_original_length / total_reads
    
    if passed_reads > 0:
        mean_passed_original_quality = sum_passed_original_quality / passed_reads
        mean_passed_original_length = sum_passed_original_length / passed_reads
        mean_trimmed_quality = sum_trimmed_quality / passed_reads
        mean_trimmed_length = sum_trimmed_length / passed_reads
    else:
        mean_passed_original_quality = mean_trimmed_quality = 0
        mean_passed_original_length = mean_trimmed_length = 0
    
    # Generate report
    report = {
        "total_reads": total_reads,
        "passed_reads": passed_reads,
        "mean_quality_before": mean_passed_original_quality,
        "mean_quality_after": mean_trimmed_quality,
        "mean_length_before": mean_passed_original_length,
        "mean_length_after": mean_trimmed_length,
        "quality_distribution": dict(quality_dist)
    }
    
    try:
        with open(args.report, 'w') as f:
            json.dump(report, f, indent=2)
    except Exception as e:
        print(f"Error writing report: {e}")
        sys.exit(1)
    
    # Print summary
    trim_rate = (total_reads - passed_reads) / total_reads * 100
    
    print(f"Reads before: {total_reads}")
    print(f"Reads after: {passed_reads}")
    print(f"Trim rate: {trim_rate:.1f}%")
    
    if passed_reads > 0:
        quality_improvement = mean_trimmed_quality - mean_passed_original_quality
        length_reduction = mean_passed_original_length - mean_trimmed_length
        print(f"Mean quality improvement: {quality_improvement:.2f}")
        print(f"Mean length reduction: {length_reduction:.1f} bp")
    else:
        print("Warning: No reads passed filtering - consider lowering quality/length thresholds")

if __name__ == "__main__":
    main()
