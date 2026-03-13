#!/usr/bin/env python3
"""
Phylogenetic Distance Calculator
Computes pairwise evolutionary distances from multiple sequence alignments
"""

import argparse
import sys
import json
import numpy as np
from itertools import combinations
from typing import Dict, List, Tuple, Callable

def parse_fasta(fasta_content: str) -> Dict[str, str]:
    """Parse FASTA format content into dictionary of sequences."""
    sequences = {}
    current_id = None
    current_seq = []
    
    for line in fasta_content.strip().split('\n'):
        line = line.strip()
        if line.startswith('>'):
            if current_id is not None:
                sequences[current_id] = ''.join(current_seq).upper()
            current_id = line[1:]
            current_seq = []
        elif line:
            current_seq.append(line)
    
    if current_id is not None:
        sequences[current_id] = ''.join(current_seq).upper()
    
    return sequences

def validate_alignment(sequences: Dict[str, str]) -> None:
    """Validate that all sequences have equal length."""
    if len(sequences) < 2:
        raise ValueError("Need at least 2 sequences for distance calculation")
    
    lengths = [len(seq) for seq in sequences.values()]
    if len(set(lengths)) > 1:
        raise ValueError("All sequences must have equal length (proper alignment)")

def hamming_distance(seq1: str, seq2: str) -> float:
    """Calculate Hamming distance (proportion of differing sites)."""
    valid_pairs = [(a, b) for a, b in zip(seq1, seq2) if a != '-' and b != '-']
    if not valid_pairs:
        return float('nan')
    
    differences = sum(1 for a, b in valid_pairs if a != b)
    return differences / len(valid_pairs)

def p_distance(seq1: str, seq2: str) -> float:
    """Calculate p-distance (simple proportion of differences, gaps ignored)."""
    return hamming_distance(seq1, seq2)  # Same calculation

def jukes_cantor_distance(seq1: str, seq2: str) -> float:
    """Calculate Jukes-Cantor corrected distance."""
    valid_pairs = [(a, b) for a, b in zip(seq1, seq2) if a != '-' and b != '-']
    if not valid_pairs:
        return float('nan')
    
    differences = sum(1 for a, b in valid_pairs if a != b)
    p = differences / len(valid_pairs)
    
    # Handle edge cases
    if p == 0:
        return 0.0
    
    if 4 * p / 3 >= 1:
        return p  # Fallback to p-distance when correction undefined
    
    return -3/4 * np.log(1 - 4*p/3)

def calculate_distance_matrix(sequences: Dict[str, str], distance_func: Callable) -> Tuple[np.ndarray, List[str]]:
    """Calculate pairwise distance matrix for all sequences."""
    seq_names = list(sequences.keys())
    n = len(seq_names)
    matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i+1, n):
            dist = distance_func(sequences[seq_names[i]], sequences[seq_names[j]])
            matrix[i, j] = dist
            matrix[j, i] = dist  # Symmetric matrix
    
    return matrix, seq_names

def save_matrix(matrix: np.ndarray, seq_names: List[str], filename: str) -> None:
    """Save distance matrix as tab-separated file."""
    with open(filename, 'w') as f:
        # Header row
        f.write('\t' + '\t'.join(seq_names) + '\n')
        
        # Data rows
        for i, name in enumerate(seq_names):
            row_data = [f"{matrix[i, j]:.6f}" for j in range(len(seq_names))]
            f.write(name + '\t' + '\t'.join(row_data) + '\n')

def save_pairwise_json(matrix: np.ndarray, seq_names: List[str], filename: str) -> None:
    """Save pairwise distances as JSON file."""
    pairwise_data = []
    
    for i in range(len(seq_names)):
        for j in range(i+1, len(seq_names)):
            pairwise_data.append({
                'sequence1': seq_names[i],
                'sequence2': seq_names[j],
                'distance': float(matrix[i, j])
            })
    
    with open(filename, 'w') as f:
        json.dump(pairwise_data, f, indent=2)

def calculate_summary_stats(matrix: np.ndarray) -> Dict[str, float]:
    """Calculate summary statistics for distance matrix."""
    # Extract upper triangle (excluding diagonal)
    upper_triangle = matrix[np.triu_indices_from(matrix, k=1)]
    
    # Filter out NaN values
    valid_distances = upper_triangle[~np.isnan(upper_triangle)]
    
    if len(valid_distances) == 0:
        return {'mean': float('nan'), 'std': float('nan'), 'min': float('nan'), 'max': float('nan')}
    
    return {
        'mean': float(np.mean(valid_distances)),
        'std': float(np.std(valid_distances)),
        'min': float(np.min(valid_distances)),
        'max': float(np.max(valid_distances))
    }

def main():
    parser = argparse.ArgumentParser(description='Calculate phylogenetic distances from multiple sequence alignment')
    parser.add_argument('-i', '--input', help='Input FASTA file (default: stdin)')
    parser.add_argument('-m', '--method', choices=['hamming', 'jukes-cantor', 'p-distance'], 
                       default='jukes-cantor', help='Distance calculation method')
    parser.add_argument('-o', '--output', default='distances', help='Output file prefix')
    parser.add_argument('--data', help='Direct sequence data for testing')
    
    args = parser.parse_args()
    
    # Distance method mapping
    distance_methods = {
        'hamming': hamming_distance,
        'jukes-cantor': jukes_cantor_distance,
        'p-distance': p_distance
    }
    
    try:
        # Read input data
        if args.data:
            fasta_content = args.data
        elif args.input:
            with open(args.input, 'r') as f:
                fasta_content = f.read()
        else:
            fasta_content = sys.stdin.read()
        
        # Parse and validate sequences
        sequences = parse_fasta(fasta_content)
        validate_alignment(sequences)
        
        print(f"Loaded {len(sequences)} sequences")
        print(f"Using {args.method} distance method")
        
        # Calculate distances
        distance_func = distance_methods[args.method]
        matrix, seq_names = calculate_distance_matrix(sequences, distance_func)
        
        # Save outputs
        matrix_file = f"{args.output}_matrix.txt"
        pairwise_file = f"{args.output}_pairwise.json"
        
        save_matrix(matrix, seq_names, matrix_file)
        save_pairwise_json(matrix, seq_names, pairwise_file)
        
        # Calculate and display summary statistics
        stats = calculate_summary_stats(matrix)
        
        print(f"\nSummary Statistics:")
        print(f"Mean distance: {stats['mean']:.6f}")
        print(f"Standard deviation: {stats['std']:.6f}")
        print(f"Minimum distance: {stats['min']:.6f}")
        print(f"Maximum distance: {stats['max']:.6f}")
        
        print(f"\nOutput files created:")
        print(f"Distance matrix: {matrix_file}")
        print(f"Pairwise distances: {pairwise_file}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
