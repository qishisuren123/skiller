#!/usr/bin/env python3
import argparse
import json
import re
import logging
import os
from typing import List, Dict, Tuple, Optional

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def parse_arguments():
    parser = argparse.ArgumentParser(description='PCR Primer Design Tool')
    parser.add_argument('--sequences', '--input', required=True,
                       help='Input DNA sequences (comma-separated or file path)')
    parser.add_argument('--output', '--out', required=True,
                       help='Output JSON file for primer designs')
    parser.add_argument('--min-length', type=int, default=18,
                       help='Minimum primer length (default: 18)')
    parser.add_argument('--max-length', type=int, default=25,
                       help='Maximum primer length (default: 25)')
    parser.add_argument('--target-tm', type=float, default=60.0,
                       help='Target melting temperature in Celsius (default: 60)')
    parser.add_argument('--tm-tolerance', type=float, default=5.0,
                       help='Acceptable deviation from target Tm (default: 5)')
    parser.add_argument('--min-gc', type=float, default=40.0,
                       help='Minimum GC content percentage (default: 40)')
    parser.add_argument('--max-gc', type=float, default=60.0,
                       help='Maximum GC content percentage (default: 60)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug output')
    return parser.parse_args()

def validate_sequence(sequence: str) -> bool:
    """Validate DNA sequence contains only A, T, G, C"""
    return bool(re.match(r'^[ATGC]+$', sequence.upper()))

def calculate_tm(sequence: str, debug: bool = False) -> float:
    """Calculate melting temperature using basic formula"""
    sequence = sequence.upper()
    a_count = sequence.count('A')
    t_count = sequence.count('T')
    g_count = sequence.count('G')
    c_count = sequence.count('C')
    
    at_count = a_count + t_count
    gc_count = g_count + c_count
    tm = 2 * at_count + 4 * gc_count
    
    if debug:
        logging.info(f"    Tm calculation for {sequence}:")
        logging.info(f"    A: {a_count}, T: {t_count}, G: {g_count}, C: {c_count}")
        logging.info(f"    AT: {at_count}, GC: {gc_count}")
        logging.info(f"    Tm = 2×{at_count} + 4×{gc_count} = {tm}°C")
    
    return float(tm)

def calculate_gc_content(sequence: str) -> float:
    """Calculate GC content percentage"""
    sequence = sequence.upper()
    gc_count = sequence.count('G') + sequence.count('C')
    return (gc_count / len(sequence)) * 100

def parse_fasta_file(filepath: str) -> Dict[str, str]:
    """Parse FASTA file and return dictionary of sequence names and sequences"""
    sequences = {}
    current_name = None
    current_seq = []
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    if current_name and current_seq:
                        sequences[current_name] = ''.join(current_seq)
                    current_name = line[1:]
                    current_seq = []
                elif line:
                    current_seq.append(line.replace(' ', '').replace('\t', ''))
            
            if current_name and current_seq:
                sequences[current_name] = ''.join(current_seq)
                
    except FileNotFoundError:
        logging.error(f"FASTA file not found: {filepath}")
        return {}
    except Exception as e:
        logging.error(f"Error reading FASTA file: {e}")
        return {}
    
    logging.info(f"Loaded {len(sequences)} sequences from {filepath}")
    return sequences

def generate_primers(sequence: str, min_len: int, max_len: int, 
                    min_gc: float, max_gc: float, debug: bool = False) -> List[Dict]:
    """Generate all possible forward primers within constraints"""
    primers = []
    sequence = sequence.upper()
    
    if debug:
        logging.info(f"Generating primers for sequence: {sequence[:50]}{'...' if len(sequence) > 50 else ''}")
        logging.info(f"Length range: {min_len}-{max_len}, GC range: {min_gc}-{max_gc}%")
    
    for length in range(min_len, max_len + 1):
        if length <= len(sequence):
            primer_seq = sequence[:length]
            gc_content = calculate_gc_content(primer_seq)
            tm = calculate_tm(primer_seq, debug)
            
            if debug:
                logging.info(f"  Length {length}: {primer_seq} (GC: {gc_content:.1f}%, Tm: {tm:.1f}°C)")
            
            if min_gc <= gc_content <= max_gc:
                primers.append({
                    'sequence': primer_seq,
                    'length': length,
                    'tm': tm,
                    'gc_content': gc_content
                })
                if debug:
                    logging.info(f"    ✓ Added to candidates")
            else:
                if debug:
                    logging.info(f"    ✗ GC content out of range")
    
    if debug:
        logging.info(f"Total candidates passing GC filter: {len(primers)}")
    
    return primers

def select_best_primer(primers: List[Dict], target_tm: float, tm_tolerance: float, debug: bool = False) -> Optional[Dict]:
    """Select primer closest to target Tm, with GC content tiebreaker"""
    if debug:
        logging.info(f"Selecting best primer from {len(primers)} candidates")
        logging.info(f"Target Tm: {target_tm}°C ± {tm_tolerance}°C")
    
    valid_primers = []
    for p in primers:
        tm_diff = abs(p['tm'] - target_tm)
        if tm_diff <= tm_tolerance:
            valid_primers.append(p)
            if debug:
                logging.info(f"  ✓ {p['sequence']} (Tm: {p['tm']:.1f}°C, diff: {tm_diff:.1f}°C)")
        else:
            if debug:
                logging.info(f"  ✗ {p['sequence']} (Tm: {p['tm']:.1f}°C, diff: {tm_diff:.1f}°C)")
    
    if not valid_primers:
        if debug:
            logging.info("No primers within Tm tolerance range")
        return None
    
    valid_primers.sort(key=lambda p: (abs(p['tm'] - target_tm), abs(p['gc_content'] - 50)))
    
    if debug:
        best = valid_primers[0]
        logging.info(f"Selected: {best['sequence']} (Tm: {best['tm']:.1f}°C, GC: {best['gc_content']:.1f}%)")
    
    return valid_primers[0]

def parse_input_sequences(input_str: str) -> Dict[str, str]:
    """Parse input sequences from command line or file"""
    if os.path.isfile(input_str):
        return parse_fasta_file(input_str)
    else:
        seq_list = [seq.strip() for seq in input_str.split(',') if seq.strip()]
        return {'seq_' + str(i+1): seq for i, seq in enumerate(seq_list)}

def calculate_summary_stats(results: Dict) -> Dict:
    """Calculate summary statistics from results"""
    total_sequences = len(results)
    successful_designs = sum(1 for r in results.values() if r['selected_primer'] is not None)
    success_rate = (successful_designs / total_sequences * 100) if total_sequences > 0 else 0
    
    valid_primers = [r['selected_primer'] for r in results.values() if r['selected_primer'] is not None]
    
    if valid_primers:
        tms = [p['tm'] for p in valid_primers]
        gcs = [p['gc_content'] for p in valid_primers]
        lengths = [p['length'] for p in valid_primers]
        
        summary = {
            'total_sequences': total_sequences,
            'successful_designs': successful_designs,
            'success_rate_percent': round(success_rate, 1),
            'primer_statistics': {
                'average_tm': round(sum(tms) / len(tms), 1),
                'tm_range': [round(min(tms), 1), round(max(tms), 1)],
                'average_gc_content': round(sum(gcs) / len(gcs), 1),
                'gc_range': [round(min(gcs), 1), round(max(gcs), 1)],
                'average_length': round(sum(lengths) / len(lengths), 1),
                'length_range': [min(lengths), max(lengths)]
            }
        }
    else:
        summary = {
            'total_sequences': total_sequences,
            'successful_designs': 0,
            'success_rate_percent': 0,
            'primer_statistics': None
        }
    
    return summary

if __name__ == '__main__':
    args = parse_arguments()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup_logging()
    
    sequences = parse_input_sequences(args.sequences)
    
    if not sequences:
        logging.error("No valid sequences found in input")
        exit(1)
    
    results = {}
    
    for seq_name, sequence in sequences.items():
        logging.info(f"Processing {seq_name}")
        
        if not validate_sequence(sequence):
            logging.warning(f"Invalid sequence {seq_name}: contains non-ATGC characters")
            continue
            
        primers = generate_primers(sequence, args.min_length, args.max_length, 
                                 args.min_gc, args.max_gc, args.debug)
        
        best_primer = select_best_primer(primers, args.target_tm, args.tm_tolerance, args.debug)
        
        results[seq_name] = {
            'sequence_length': len(sequence),
            'sequence_preview': sequence[:50] + ('...' if len(sequence) > 50 else ''),
            'selected_primer': best_primer,
            'total_candidates': len(primers)
        }
    
    summary = calculate_summary_stats(results)
    
    output_data = {
        'summary': summary,
        'parameters': {
            'min_length': args.min_length,
            'max_length': args.max_length,
            'target_tm': args.target_tm,
            'tm_tolerance': args.tm_tolerance,
            'min_gc': args.min_gc,
            'max_gc': args.max_gc
        },
        'results': results
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logging.info(f"Primer design complete. Results saved to {args.output}")
    logging.info(f"Success rate: {summary['success_rate_percent']}% ({summary['successful_designs']}/{summary['total_sequences']})")
