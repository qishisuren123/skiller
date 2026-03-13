import argparse
import json
import logging
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def calculate_word_overlap_ratio(text1: str, text2: str) -> float:
    """Calculate word overlap ratio between two texts."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    return intersection / union if union > 0 else 0.0

def validate_entry(entry: Dict[str, Any], line_num: int) -> Tuple[bool, str]:
    """Validate a single JSONL entry."""
    required_fields = ['instruction', 'input', 'output', 'source', 'category']
    
    # Check required fields
    for field in required_fields:
        if field not in entry:
            return False, f"Missing required field: {field}"
        if entry[field] is None:
            return False, f"Field {field} is None"
    
    # Check instruction not empty and length limit
    instruction = str(entry['instruction']).strip()
    if not instruction:
        return False, "Instruction field is empty"
    if len(instruction) >= 500:
        return False, f"Instruction too long: {len(instruction)} chars (limit: 500)"
    
    # Check output not empty and length limit
    output = str(entry['output']).strip()
    if not output:
        return False, "Output field is empty"
    if len(output) >= 5000:
        return False, f"Output too long: {len(output)} chars (limit: 5000)"
    
    return True, ""

def detect_duplicates(entries: List[Dict[str, Any]], threshold: float = 0.9) -> Set[int]:
    """Detect near-duplicate entries based on instruction similarity."""
    duplicates = set()
    instructions = [(i, str(entry['instruction']).strip()) for i, entry in enumerate(entries)]
    
    for i in range(len(instructions)):
        if i in duplicates:
            continue
        for j in range(i + 1, len(instructions)):
            if j in duplicates:
                continue
            
            similarity = calculate_word_overlap_ratio(instructions[i][1], instructions[j][1])
            if similarity > threshold:
                duplicates.add(j)  # Keep first occurrence, mark later ones as duplicates
                logging.info(f"Duplicate detected: entries {i} and {j} (similarity: {similarity:.3f})")
    
    return duplicates

def process_dataset(input_path: str, output_path: str, report_path: str):
    """Main processing function."""
    setup_logging()
    
    # Statistics tracking
    total_entries = 0
    removal_reasons = Counter()
    valid_entries = []
    category_counts = Counter()
    instruction_lengths = []
    output_lengths = []
    
    # Load and validate entries
    logging.info(f"Loading dataset from {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                total_entries += 1
                line = line.strip()
                if not line:
                    removal_reasons['empty_line'] += 1
                    continue
                
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as e:
                    logging.warning(f"Invalid JSON at line {line_num}: {e}")
                    removal_reasons['invalid_json'] += 1
                    continue
                
                # Validate entry
                is_valid, error_msg = validate_entry(entry, line_num)
                if not is_valid:
                    logging.warning(f"Invalid entry at line {line_num}: {error_msg}")
                    removal_reasons['validation_failed'] += 1
                    continue
                
                valid_entries.append(entry)
    
    except FileNotFoundError:
        logging.error(f"Input file not found: {input_path}")
        return
    except Exception as e:
        logging.error(f"Error reading input file: {e}")
        return
    
    logging.info(f"Loaded {len(valid_entries)} valid entries out of {total_entries}")
    
    # Detect duplicates
    logging.info("Detecting near-duplicates...")
    duplicate_indices = detect_duplicates(valid_entries)
    removal_reasons['near_duplicate'] = len(duplicate_indices)
    
    # Filter out duplicates
    cleaned_entries = [entry for i, entry in enumerate(valid_entries) if i not in duplicate_indices]
    logging.info(f"Removed {len(duplicate_indices)} near-duplicates")
    
    # Calculate statistics for cleaned data
    for entry in cleaned_entries:
        category_counts[entry['category']] += 1
        instruction_lengths.append(len(str(entry['instruction']).strip()))
        output_lengths.append(len(str(entry['output']).strip()))
    
    # Write cleaned dataset
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in cleaned_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        logging.info(f"Wrote {len(cleaned_entries)} cleaned entries to {output_path}")
    except Exception as e:
        logging.error(f"Error writing output file: {e}")
        return
    
    # Generate report
    report = {
        'total_entries': total_entries,
        'cleaned_entries': len(cleaned_entries),
        'removed_count': {
            'total': total_entries - len(cleaned_entries),
            'by_reason': dict(removal_reasons)
        },
        'category_distribution': dict(category_counts),
        'statistics': {
            'avg_instruction_length': sum(instruction_lengths) / len(instruction_lengths) if instruction_lengths else 0,
            'avg_output_length': sum(output_lengths) / len(output_lengths) if output_lengths else 0,
            'unique_categories': len(category_counts)
        }
    }
    
    # Write report
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logging.info(f"Generated report: {report_path}")
    except Exception as e:
        logging.error(f"Error writing report file: {e}")
        return
    
    # Print summary
    print(f"\nDataset Cleaning Summary:")
    print(f"Total entries processed: {total_entries}")
    print(f"Valid entries after cleaning: {len(cleaned_entries)}")
    print(f"Removal breakdown: {dict(removal_reasons)}")
    print(f"Categories found: {len(category_counts)}")

def main():
    parser = argparse.ArgumentParser(description='Validate and clean materials science training dataset')
    parser.add_argument('--input', required=True, help='Input JSONL file path')
    parser.add_argument('--output', required=True, help='Output cleaned JSONL file path')
    parser.add_argument('--report', required=True, help='Output report JSON file path')
    
    args = parser.parse_args()
    process_dataset(args.input, args.output, args.report)

if __name__ == '__main__':
    main()
