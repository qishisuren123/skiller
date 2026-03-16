import argparse
import json
import logging
from collections import defaultdict, Counter
import re
import hashlib

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_jsonl(file_path):
    """Load JSONL file and return list of entries"""
    entries = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                entry['_line_num'] = line_num
                entries.append(entry)
            except json.JSONDecodeError as e:
                logging.warning(f"Invalid JSON at line {line_num}: {e}")
    return entries

def validate_entry(entry):
    """Validate a single entry and return (is_valid, error_reason)"""
    required_fields = ['instruction', 'input', 'output', 'source', 'category']
    
    # Check required fields
    for field in required_fields:
        if field not in entry:
            return False, f"missing_field_{field}"
    
    # Check non-empty instruction and output
    if not entry['instruction'].strip():
        return False, "empty_instruction"
    if not entry['output'].strip():
        return False, "empty_output"
    
    # Check length limits
    if len(entry['instruction']) >= 500:
        return False, "instruction_too_long"
    if len(entry['output']) >= 5000:
        return False, "output_too_long"
    
    return True, None

def get_shingles(text, k=3):
    """Get character k-shingles from text"""
    text = re.sub(r'\s+', ' ', text.lower().strip())
    shingles = set()
    for i in range(len(text) - k + 1):
        shingles.add(text[i:i+k])
    return shingles

def minhash_signature(shingles, num_hashes=100):
    """Generate MinHash signature for a set of shingles"""
    signature = []
    
    for i in range(num_hashes):
        min_hash = float('inf')
        for shingle in shingles:
            # Create hash with different seed for each hash function
            hash_input = f"{i}:{shingle}".encode('utf-8')
            hash_val = int(hashlib.md5(hash_input).hexdigest(), 16)
            min_hash = min(min_hash, hash_val)
        signature.append(min_hash)
    
    return signature

def create_lsh_buckets(signatures, num_bands=20, rows_per_band=5):
    """Create LSH buckets for candidate pair generation"""
    buckets = defaultdict(list)
    
    for idx, signature in enumerate(signatures):
        for band in range(num_bands):
            start = band * rows_per_band
            end = start + rows_per_band
            band_signature = tuple(signature[start:end])
            bucket_key = f"{band}:{hash(band_signature)}"
            buckets[bucket_key].append(idx)
    
    return buckets

def get_candidate_pairs(buckets):
    """Get candidate pairs from LSH buckets"""
    candidates = set()
    
    for bucket_indices in buckets.values():
        if len(bucket_indices) > 1:
            for i in range(len(bucket_indices)):
                for j in range(i + 1, len(bucket_indices)):
                    candidates.add((bucket_indices[i], bucket_indices[j]))
    
    return candidates

def calculate_ngram_similarity(text1, text2, weights=None):
    """Calculate similarity using weighted n-gram overlap"""
    if weights is None:
        weights = {1: 0.3, 2: 0.5, 3: 0.2}
    
    stop_words = {'what', 'is', 'the', 'of', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'how', 'why', 'when', 'where'}
    
    def get_ngrams(text, n):
        words = re.findall(r'\w+', text.lower())
        return [tuple(words[i:i+n]) for i in range(len(words)-n+1)]
    
    total_similarity = 0.0
    total_weight = 0.0
    
    for n, weight in weights.items():
        ngrams1 = get_ngrams(text1, n)
        ngrams2 = get_ngrams(text2, n)
        
        if not ngrams1 or not ngrams2:
            continue
            
        counter1 = Counter(ngrams1)
        counter2 = Counter(ngrams2)
        
        overlap = 0
        for ngram in counter1:
            if ngram in counter2:
                ngram_weight = 1.0
                stop_word_count = sum(1 for word in ngram if word in stop_words)
                if stop_word_count > 0:
                    ngram_weight = 1.0 / (1 + stop_word_count * 0.5)
                
                overlap += min(counter1[ngram], counter2[ngram]) * ngram_weight
        
        avg_length = (len(ngrams1) + len(ngrams2)) / 2
        if avg_length > 0:
            ngram_similarity = overlap / avg_length
            total_similarity += ngram_similarity * weight
            total_weight += weight
    
    return total_similarity / total_weight if total_weight > 0 else 0.0

def find_duplicates(entries, threshold=0.85):
    """Find near-duplicate entries using LSH for efficiency"""
    if len(entries) < 2:
        return set()
    
    logging.info("Generating MinHash signatures...")
    signatures = []
    
    for entry in entries:
        shingles = get_shingles(entry['instruction'])
        if shingles:
            signature = minhash_signature(shingles)
            signatures.append(signature)
        else:
            signatures.append([])
    
    logging.info("Creating LSH buckets...")
    buckets = create_lsh_buckets(signatures)
    
    logging.info("Finding candidate pairs...")
    candidate_pairs = get_candidate_pairs(buckets)
    
    logging.info(f"Checking {len(candidate_pairs)} candidate pairs (reduced from {len(entries)*(len(entries)-1)//2})")
    
    duplicates = set()
    duplicate_pairs = []
    
    for i, j in candidate_pairs:
        if i in duplicates or j in duplicates:
            continue
            
        similarity = calculate_ngram_similarity(
            entries[i]['instruction'], 
            entries[j]['instruction']
        )
        
        if similarity > threshold:
            duplicates.add(j)
            duplicate_pairs.append((i, j, similarity))
            logging.debug(f"Duplicate found: lines {entries[i]['_line_num']} and {entries[j]['_line_num']} (similarity: {similarity:.3f})")
    
    logging.info(f"Found {len(duplicates)} duplicates from {len(duplicate_pairs)} similar pairs")
    return duplicates

def main():
    parser = argparse.ArgumentParser(description='Clean materials science training dataset')
    parser.add_argument('--input', required=True, help='Input JSONL file path')
    parser.add_argument('--output', required=True, help='Output cleaned JSONL file path')
    parser.add_argument('--report', required=True, help='Report JSON file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--similarity-threshold', type=float, default=0.85, help='Similarity threshold for duplicates (default: 0.85)')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        setup_logging()
    
    # Load data
    logging.info(f"Loading data from {args.input}")
    entries = load_jsonl(args.input)
    total_entries = len(entries)
    logging.info(f"Loaded {total_entries} entries")
    
    # Validate entries
    valid_entries = []
    removal_reasons = Counter()
    
    for entry in entries:
        is_valid, reason = validate_entry(entry)
        if is_valid:
            valid_entries.append(entry)
        else:
            removal_reasons[reason] += 1
            logging.debug(f"Removed entry at line {entry['_line_num']}: {reason}")
    
    logging.info(f"After validation: {len(valid_entries)} valid entries")
    
    # Find duplicates
    logging.info("Finding duplicates using LSH + n-gram similarity...")
    duplicate_indices = find_duplicates(valid_entries, threshold=args.similarity_threshold)
    logging.info(f"Found {len(duplicate_indices)} duplicates")
    
    # Remove duplicates
    cleaned_entries = []
    for i, entry in enumerate(valid_entries):
        if i not in duplicate_indices:
            cleaned_entries.append(entry)
        else:
            removal_reasons['duplicate'] += 1
    
    logging.info(f"After deduplication: {len(cleaned_entries)} entries")
    
    # Check if we have any entries left
    if len(cleaned_entries) == 0:
        logging.error("No entries remaining after cleaning! Check your data and validation criteria.")
        return
    
    # Generate statistics
    category_dist = Counter(entry['category'] for entry in cleaned_entries)
    avg_instruction_len = sum(len(entry['instruction']) for entry in cleaned_entries) / len(cleaned_entries)
    avg_output_len = sum(len(entry['output']) for entry in cleaned_entries) / len(cleaned_entries)
    
    # Write cleaned data
    with open(args.output, 'w', encoding='utf-8') as f:
        for entry in cleaned_entries:
            clean_entry = {k: v for k, v in entry.items() if not k.startswith('_')}
            f.write(json.dumps(clean_entry) + '\n')
    
    # Write report - ensure all Counter objects are converted to dict
    report = {
        'total_entries': total_entries,
        'cleaned_entries': len(cleaned_entries),
        'removed_count': dict(removal_reasons),  # Convert Counter to dict
        'category_distribution': dict(category_dist),  # Convert Counter to dict
        'average_instruction_length': avg_instruction_len,
        'average_output_length': avg_output_len,
        'similarity_threshold_used': args.similarity_threshold
    }
    
    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Cleaning complete. {len(cleaned_entries)}/{total_entries} entries retained")

if __name__ == '__main__':
    main()
