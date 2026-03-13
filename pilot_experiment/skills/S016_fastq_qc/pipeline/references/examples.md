# Basic FASTQ parsing generator
def parse_fastq_streaming(filename):
    with open(filename, 'r') as f:
        while True:
            header = f.readline().strip()
            if not header:
                break
            sequence = f.readline().strip()
            plus = f.readline().strip()
            quality = f.readline().strip()
            yield (header, sequence, quality)

# Quality score conversion
def quality_to_phred(quality_string):
    return [ord(char) - 33 for char in quality_string]

# 3' end trimming logic
def trim_read(sequence, quality, min_quality):
    phred_scores = quality_to_phred(quality)
    trim_pos = 0
    
    for i in range(len(phred_scores) - 1, -1, -1):
        if phred_scores[i] >= min_quality:
            trim_pos = i + 1
            break
    
    return sequence[:trim_pos], quality[:trim_pos]

# Streaming processing pattern
total_reads = 0
passed_reads = 0
sum_quality = 0

with open(output_file, 'w') as out:
    for header, seq, qual in parse_fastq_streaming(input_file):
        total_reads += 1
        trimmed_seq, trimmed_qual = trim_read(seq, qual, min_qual)
        
        if len(trimmed_seq) >= min_length:
            passed_reads += 1
            out.write(f"{header}\n{trimmed_seq}\n+\n{trimmed_qual}\n")
            sum_quality += calculate_mean_quality(trimmed_qual)

mean_quality = sum_quality / passed_reads if passed_reads > 0 else 0
