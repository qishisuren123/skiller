import argparse
import json
import re
import random
from collections import defaultdict, Counter

def normalize_text(text, max_words=200):
    """Normalize text with length limiting to prevent memory issues"""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Limit to first max_words to prevent memory issues with very long texts
    words = text.split()
    if len(words) > max_words:
        text = ' '.join(words[:max_words])
    
    return text

def get_word_shingles(text, n=3):
    """Create word n-grams with memory optimization"""
    normalized = normalize_text(text)
    words = normalized.split()
    if len(words) < n:
        return {tuple(words)}
    
    shingles = set()
    # Limit number of shingles to prevent memory explosion
    max_shingles = min(100, len(words) - n + 1)
    for i in range(max_shingles):
        shingles.add(tuple(words[i:i+n]))
    return shingles

def has_potential_overlap(text1, text2, threshold=0.3):
    """Quick check if two texts might be similar using shingles"""
    shingles1 = get_word_shingles(text1)
    shingles2 = get_word_shingles(text2)
    
    if not shingles1 or not shingles2:
        return len(shingles1) == len(shingles2) == 0
    
    intersection = len(shingles1 & shingles2)
    smaller_set = min(len(shingles1), len(shingles2))
    
    return intersection / smaller_set >= threshold

def calculate_similarity(text1, text2):
    """Calculate word overlap ratio between two texts with type safety"""
    if not isinstance(text1, str) or not isinstance(text2, str):
        return 0.0
    
    if not text1.strip() and not text2.strip():
        return 1.0
    if not text1.strip() or not text2.strip():
        return 0.0
    
    try:
        words1 = set(normalize_text(text1).split())
        words2 = set(normalize_text(text2).split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        smaller_set_size = min(len(words1), len(words2))
        
        return intersection / smaller_set_size
    except Exception:
        return 0.0

def validate_entry(entry):
    """Validate a single JSONL entry with robust type checking"""
    required_fields = ['instruction', 'input', 'output', 'source', 'category']
    
    # Check required fields exist
    for field in required_fields:
        if field not in entry:
            return False, f"Missing field: {field}"
    
    # Check field types and convert if possible
    for field in ['instruction', 'input', 'output', 'source', 'category']:
        if entry[field] is None:
            return False, f"Field {field} is null"
        if not isinstance(entry[field], str):
            try:
                entry[field] = str(entry[field])
            except:
                return False, f"Field {field} cannot be converted to string"
    
    # Check non-empty instruction and output
    if not entry['instruction'].strip():
        return False, "Empty instruction"
    if not entry['output'].strip():
        return False, "Empty output"
    
    # Check length limits
    if len(entry['instruction']) >= 500:
        return False, "Instruction too long"
    if len(entry['output']) >= 5000:
        return False, "Output too long"
    
    return True, None

def main():
    parser = argparse.ArgumentParser(description='Clean materials science training dataset')
    parser.add_argument('--input', required=True, help='Input JSONL file path')
    parser.add_argument('--output', required=True, help='Output cleaned JSONL file path')
    parser.add_argument('--report', required=True, help='Report JSON file path')
    parser.add_argument('--duplicates-sample', help='Optional: save sample of removed duplicates')
    parser.add_argument('--sample-size', type=int, default=50, help='Number of duplicate pairs to sample')
    
    args = parser.parse_args()
    
    # Load and process data
    entries = []
    removal_reasons = defaultdict(int)
    
    with open(args.input, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                entries.append((entry, line_num))
            except json.JSONDecodeError:
                removal_reasons['invalid_json'] += 1
                print(f"Warning: Invalid JSON on line {line_num}")
    
    print(f"Loaded {len(entries)} entries")
    
    # Validate entries
    valid_entries = []
    for entry, line_num in entries:
        is_valid, error = validate_entry(entry)
        if is_valid:
            valid_entries.append(entry)
        else:
            removal_reasons[error] += 1
            print(f"Invalid entry on line {line_num}: {error}")
    
    print(f"Valid entries: {len(valid_entries)}")
    
    # Detect duplicates
    print("Detecting duplicates...")
    final_entries = []
    removed_as_duplicate = 0
    duplicate_samples = []
    
    for i, entry in enumerate(valid_entries):
        is_duplicate = False
        matched_entry = None
        
        for kept_entry in final_entries:
            if has_potential_overlap(entry['instruction'], kept_entry['instruction']):
                similarity = calculate_similarity(entry['instruction'], kept_entry['instruction'])
                if similarity > 0.9:
                    is_duplicate = True
                    matched_entry = kept_entry
                    removed_as_duplicate += 1
                    if i % 100 == 0:
                        print(f"Processed {i+1}/{len(valid_entries)} entries...")
                    break
        
        if not is_duplicate:
            final_entries.append(entry)
        elif args.duplicates_sample and len(duplicate_samples) < args.sample_size:
            duplicate_samples.append({
                'removed_entry': entry,
                'similar_to': matched_entry,
                'similarity_score': calculate_similarity(entry['instruction'], matched_entry['instruction'])
            })
    
    removal_reasons['near_duplicate'] = removed_as_duplicate
    print(f"After duplicate removal: {len(final_entries)}")
    
    # Write cleaned data
    with open(args.output, 'w') as f:
        for entry in final_entries:
            f.write(json.dumps(entry) + '\n')
    
    # Save duplicate samples if requested
    if args.duplicates_sample and duplicate_samples:
        with open(args.duplicates_sample, 'w') as f:
            for sample in duplicate_samples:
                f.write(json.dumps(sample) + '\n')
        print(f"Saved {len(duplicate_samples)} duplicate samples to {args.duplicates_sample}")
    
    # Generate report
    category_dist = Counter(entry['category'] for entry in final_entries) if final_entries else {}
    
    if final_entries:
        avg_instruction_len = sum(len(entry['instruction']) for entry in final_entries) / len(final_entries)
        avg_output_len = sum(len(entry['output']) for entry in final_entries) / len(final_entries)
    else:
        avg_instruction_len = 0
        avg_output_len = 0
        print("Warning: No valid entries remain after cleaning!")
    
    report = {
        'total_entries': len(entries),
        'removed_count': dict(removal_reasons),
        'category_distribution': dict(category_dist),
        'average_lengths': {
            'instruction': avg_instruction_len,
            'output': avg_output_len
        }
    }
    
    with open(args.report, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Cleaning complete. Report saved to {args.report}")

if __name__ == "__main__":
    main()
