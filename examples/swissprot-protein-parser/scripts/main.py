import json
import pandas as pd
import numpy as np
import re
import argparse
from typing import Dict, List, Any, Union, Iterator
import logging
from pathlib import Path
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_extract_text(text_info: Union[List, Dict, str]) -> str:
    """Safely extract text value from various formats."""
    if not text_info:
        return ''
    
    if isinstance(text_info, str):
        return text_info
    elif isinstance(text_info, list):
        if len(text_info) == 0:
            return ''
        first_item = text_info[0]
        if isinstance(first_item, dict):
            return first_item.get('value', '')
        return str(first_item)
    elif isinstance(text_info, dict):
        return text_info.get('value', '')
    
    return str(text_info)

def parse_swissprot_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a single SwissProt JSON entry and extract structured fields."""
    
    parsed_data = {
        'protein_id': '',
        'protein_name': '',
        'function_description': '',
        'go_annotations': '',
        'subcellular_location': '',
        'sequence': '',
        'sequence_length': 0
    }
    
    # Extract protein ID
    for id_field in ['accession', 'accessions', 'primaryAccession', 'id']:
        if id_field in entry and entry[id_field]:
            acc = entry[id_field]
            parsed_data['protein_id'] = acc[0] if isinstance(acc, list) and acc else str(acc)
            break
    
    # Extract protein name
    if 'protein' in entry:
        protein_info = entry['protein']
        name_sources = ['recommendedName', 'submittedName']
        
        for name_type in name_sources:
            if name_type in protein_info:
                name_info = protein_info[name_type]
                if isinstance(name_info, list) and name_info:
                    name_info = name_info[0]
                
                if isinstance(name_info, dict) and 'fullName' in name_info:
                    full_name = name_info['fullName']
                    name_text = safe_extract_text(full_name)
                    if name_text:
                        parsed_data['protein_name'] = name_text
                        break
    
    # Process comments
    comments = []
    if 'comment' in entry:
        comments = entry['comment'] if isinstance(entry['comment'], list) else [entry['comment']]
    
    for comment in comments:
        if not isinstance(comment, dict):
            continue
            
        comment_type = comment.get('type', '')
        
        if comment_type == 'function' and not parsed_data['function_description']:
            if 'text' in comment:
                func_text = safe_extract_text(comment['text'])
                if func_text:
                    parsed_data['function_description'] = func_text
        
        elif comment_type == 'subcellular location' and not parsed_data['subcellular_location']:
            if 'subcellularLocation' in comment:
                subloc = comment['subcellularLocation']
                if isinstance(subloc, list) and subloc:
                    subloc = subloc[0]
                if isinstance(subloc, dict) and 'location' in subloc:
                    loc_text = safe_extract_text(subloc['location'])
                    if loc_text:
                        parsed_data['subcellular_location'] = loc_text
    
    # Extract GO annotations
    go_terms = []
    if 'dbReference' in entry:
        db_refs = entry['dbReference'] if isinstance(entry['dbReference'], list) else [entry['dbReference']]
        
        for ref in db_refs:
            if not isinstance(ref, dict):
                continue
                
            if ref.get('type') == 'GO':
                go_id = ref.get('id', '').strip()
                if go_id:
                    term_desc = ''
                    if 'property' in ref and ref['property']:
                        props = ref['property'] if isinstance(ref['property'], list) else [ref['property']]
                        for prop in props:
                            if isinstance(prop, dict):
                                prop_val = prop.get('value', '').strip()
                                if prop_val:
                                    term_desc = prop_val
                                    break
                    
                    if term_desc:
                        go_terms.append(f"{go_id}:{term_desc}")
                    else:
                        go_terms.append(go_id)
    
    parsed_data['go_annotations'] = '; '.join(go_terms) if go_terms else ''
    
    # Extract sequence
    if 'sequence' in entry:
        seq_info = entry['sequence']
        sequence = ''
        if isinstance(seq_info, dict):
            sequence = seq_info.get('value', '')
        elif isinstance(seq_info, str):
            sequence = seq_info
        
        if sequence:
            cleaned_seq = re.sub(r'[\s\n\r\t]', '', str(sequence))
            parsed_data['sequence'] = cleaned_seq
            parsed_data['sequence_length'] = len(cleaned_seq)
    
    return parsed_data

def process_entries_streaming(entries: List[Dict], output_file: str, output_format: str, batch_size: int = 1000) -> Dict[str, int]:
    """Process entries in streaming fashion to avoid memory issues."""
    
    stats = {
        'total_processed': 0,
        'total_errors': 0,
        'entries_with_protein_id': 0,
        'entries_with_go_annotations': 0,
        'entries_with_sequence': 0
    }
    
    # Initialize output file
    if output_format.lower() == 'csv':
        # Write CSV header
        header_written = False
    elif output_format.lower() == 'json':
        # Start JSON structure
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('{"metadata": {"total_entries": 0}, "entries": [\n')
    
    first_json_entry = True
    
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i+batch_size]
        batch_parsed = []
        
        for j, entry in enumerate(batch):
            try:
                parsed_entry = parse_swissprot_entry(entry)
                batch_parsed.append(parsed_entry)
                
                # Update statistics
                stats['total_processed'] += 1
                if parsed_entry['protein_id']:
                    stats['entries_with_protein_id'] += 1
                if parsed_entry['go_annotations']:
                    stats['entries_with_go_annotations'] += 1
                if parsed_entry['sequence']:
                    stats['entries_with_sequence'] += 1
                    
            except Exception as e:
                logger.warning(f"Error parsing entry {i+j}: {e}")
                stats['total_errors'] += 1
                continue
        
        # Write batch to file
        if batch_parsed:
            df_batch = pd.DataFrame(batch_parsed)
            
            if output_format.lower() == 'csv':
                mode = 'w' if not header_written else 'a'
                header = not header_written
                df_batch.to_csv(output_file, mode=mode, header=header, index=False, encoding='utf-8')
                header_written = True
                
            elif output_format.lower() == 'json':
                with open(output_file, 'a', encoding='utf-8') as f:
                    for idx, record in enumerate(df_batch.to_dict('records')):
                        if not first_json_entry:
                            f.write(',\n')
                        json.dump(record, f, ensure_ascii=False)
                        first_json_entry = False
        
        logger.info(f"Processed batch {i//batch_size + 1}/{(len(entries)-1)//batch_size + 1}")
    
    # Finalize JSON file
    if output_format.lower() == 'json':
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f'\n], "statistics": {json.dumps(stats)}}}')
    
    return stats

def parse_swissprot_json(input_file: str, output_file: str, output_format: str = 'csv', batch_size: int = 1000, stats_file: str = None) -> None:
    """Parse SwissProt JSON file with streaming processing."""
    
    logger.info(f"Loading JSON file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        for key in ['entries', 'results', 'data']:
            if key in data:
                entries = data[key]
                break
        else:
            entries = [data]
    else:
        raise ValueError("Unexpected JSON structure")
    
    logger.info(f"Processing {len(entries)} entries with streaming approach...")
    
    # Process with streaming
    stats = process_entries_streaming(entries, output_file, output_format, batch_size)
    
    # Print statistics
    logger.info("=== PARSING STATISTICS ===")
    logger.info(f"Total entries processed: {stats['total_processed']}")
    logger.info(f"Total errors: {stats['total_errors']}")
    logger.info(f"Entries with protein ID: {stats['entries_with_protein_id']}")
    logger.info(f"Entries with GO annotations: {stats['entries_with_go_annotations']}")
    logger.info(f"Entries with sequence: {stats['entries_with_sequence']}")
    
    # Save statistics if requested
    if stats_file:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Statistics saved to {stats_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Parse SwissProt protein database JSON files into structured format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.json output.csv
  %(prog)s input.json output.json --format json
  %(prog)s input.json output.csv --batch-size 2000 --stats stats.json
        """
    )
    
    parser.add_argument('input_file', help='Input SwissProt JSON file')
    parser.add_argument('output_file', help='Output file (CSV or JSON)')
    parser.add_argument('--format', '-f', choices=['csv', 'json'], default='csv',
                        help='Output format (default: csv)')
    parser.add_argument('--batch-size', '-b', type=int, default=1000,
                        help='Batch size for processing (default: 1000)')
    parser.add_argument('--stats', '-s', help='Save statistics to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not Path(args.input_file).exists():
        logger.error(f"Input file not found: {args.input_file}")
        return 1
    
    try:
        parse_swissprot_json(
            input_file=args.input_file,
            output_file=args.output_file,
            output_format=args.format,
            batch_size=args.batch_size,
            stats_file=args.stats
        )
        logger.info("Parsing completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Error during parsing: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
