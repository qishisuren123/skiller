#!/usr/bin/env python3
import numpy as np
import argparse
import json
import logging
import gc
import psutil
import os
from pathlib import Path

def compute_rmsd(coords1, coords2):
    """
    Compute RMSD between two coordinate sets with memory optimization.
    
    Args:
        coords1, coords2: numpy arrays of shape (N, 3)
    
    Returns:
        float: RMSD value
    """
    if coords1.shape != coords2.shape:
        raise ValueError("Coordinate arrays must have the same shape")
    
    # Process in chunks for large arrays to save memory
    chunk_size = min(10000, coords1.shape[0])
    total_sq_diff = 0.0
    
    for i in range(0, coords1.shape[0], chunk_size):
        end_idx = min(i + chunk_size, coords1.shape[0])
        chunk1 = coords1[i:end_idx]
        chunk2 = coords2[i:end_idx]
        
        diff = chunk1 - chunk2
        total_sq_diff += np.sum(diff * diff)
        
        # Clean up chunk references
        del diff, chunk1, chunk2
    
    rmsd = np.sqrt(total_sq_diff / (coords1.shape[0] * 3))
    return rmsd

def kabsch_alignment(ref_coords, target_coords):
    """
    Perform Kabsch alignment with memory optimization for large structures.
    
    Args:
        ref_coords, target_coords: centered coordinate arrays (N, 3)
    
    Returns:
        tuple: (rotation_matrix, rmsd_after_rotation, rotated_coords)
    """
    n_atoms = ref_coords.shape[0]
    
    # Memory check
    memory_gb = psutil.virtual_memory().available / (1024**3)
    estimated_memory_needed = (n_atoms * 3 * 8 * 4) / (1024**3)
    
    if estimated_memory_needed > memory_gb * 0.8:
        logging.warning(f"Large structure detected ({n_atoms} atoms). "
                       f"Estimated memory needed: {estimated_memory_needed:.2f} GB")
    
    # Compute covariance matrix H in chunks
    H = np.zeros((3, 3), dtype=np.float64)
    chunk_size = min(10000, n_atoms)
    
    for i in range(0, n_atoms, chunk_size):
        end_idx = min(i + chunk_size, n_atoms)
        target_chunk = target_coords[i:end_idx]
        ref_chunk = ref_coords[i:end_idx]
        
        H += np.dot(np.transpose(target_chunk), ref_chunk)
        del target_chunk, ref_chunk
    
    # SVD and rotation matrix computation
    U, S, Vt = np.linalg.svd(H)
    R = np.dot(np.transpose(Vt), np.transpose(U))
    
    # Ensure proper rotation
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = np.dot(np.transpose(Vt), np.transpose(U))
    
    # Apply rotation in chunks
    target_rotated = np.zeros_like(target_coords)
    R_T = np.transpose(R)
    
    for i in range(0, n_atoms, chunk_size):
        end_idx = min(i + chunk_size, n_atoms)
        target_rotated[i:end_idx] = np.dot(target_coords[i:end_idx], R_T)
    
    rmsd_aligned = compute_rmsd(ref_coords, target_rotated)
    
    del H, U, S, Vt, R_T
    gc.collect()
    
    return R, rmsd_aligned, target_rotated

def subsample_structure(coords, max_atoms=10000, method='uniform'):
    """
    Memory-efficient subsampling for large structures.
    
    Args:
        coords: coordinate array
        max_atoms: maximum number of atoms to keep
        method: 'uniform' or 'random'
    
    Returns:
        tuple: (subsampled_coords, indices_used)
    """
    n_atoms = coords.shape[0]
    
    if n_atoms <= max_atoms:
        return coords, np.arange(n_atoms)
    
    if method == 'uniform':
        step = n_atoms // max_atoms
        indices = np.arange(0, n_atoms, step)[:max_atoms]
    elif method == 'random':
        # Memory-efficient random sampling
        np.random.seed(42)
        indices = []
        for _ in range(max_atoms):
            idx = np.random.randint(0, n_atoms)
            while idx in indices:
                idx = np.random.randint(0, n_atoms)
            indices.append(idx)
        indices = np.array(sorted(indices))
    else:
        raise ValueError(f"Unknown subsampling method: {method}")
    
    return coords[indices], indices

def match_atom_counts(ref_coords, target_coords, method='truncate'):
    """Handle structures with different atom counts."""
    ref_size = ref_coords.shape[0]
    target_size = target_coords.shape[0]
    
    if ref_size == target_size:
        return ref_coords, target_coords
    
    min_size = min(ref_size, target_size)
    logging.warning(f"Atom count mismatch: ref={ref_size}, target={target_size}")
    
    if method == 'truncate':
        logging.info(f"Truncating both structures to {min_size} atoms")
        return ref_coords[:min_size], target_coords[:min_size]
    elif method == 'pad':
        max_size = max(ref_size, target_size)
        if ref_size < target_size:
            padding = np.zeros((target_size - ref_size, 3))
            ref_matched = np.vstack([ref_coords, padding])
            return ref_matched, target_coords
        else:
            padding = np.zeros((ref_size - target_size, 3))
            target_matched = np.vstack([target_coords, padding])
            return ref_coords, target_matched
    
    raise ValueError(f"Unknown matching method: {method}")

def center_coordinates(coords):
    """Center coordinates at centroid with memory optimization."""
    if coords.shape[0] > 100000:
        chunk_size = 10000
        centroid_sum = np.zeros(3)
        for i in range(0, coords.shape[0], chunk_size):
            end_idx = min(i + chunk_size, coords.shape[0])
            centroid_sum += np.sum(coords[i:end_idx], axis=0)
        centroid = centroid_sum / coords.shape[0]
    else:
        centroid = np.mean(coords, axis=0)
    
    return coords - centroid, centroid

def load_coordinates(filepath):
    """Load coordinates from file."""
    coords = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                x, y, z = map(float, line.strip().split())
                coords.append([x, y, z])
    return np.array(coords, dtype=np.float64)

def save_coordinates(coords, filepath):
    """Save coordinates to file."""
    with open(filepath, 'w') as f:
        for coord in coords:
            f.write(f"{coord[0]:.6f} {coord[1]:.6f} {coord[2]:.6f}\n")

def create_report(initial_rmsd, final_rmsd, rotation_matrix, ref_centroid, target_centroid, 
                 num_atoms, improvement):
    """Create alignment report dictionary."""
    report = {
        'alignment_statistics': {
            'initial_rmsd_angstrom': float(initial_rmsd),
            'final_rmsd_angstrom': float(final_rmsd),
            'improvement_percentage': float(improvement),
            'num_atoms_aligned': int(num_atoms)
        },
        'transformation_parameters': {
            'rotation_matrix': rotation_matrix.tolist(),
            'reference_centroid': ref_centroid.tolist(),
            'target_centroid': target_centroid.tolist(),
            'translation_vector': (ref_centroid - target_centroid).tolist()
        }
    }
    return report

def main():
    parser = argparse.ArgumentParser(description='Protein Structure RMSD Alignment Tool')
    parser.add_argument('reference', help='Reference structure coordinates file')
    parser.add_argument('target', help='Target structure coordinates file')
    parser.add_argument('-o', '--output', default='aligned_structure.xyz', 
                       help='Output file for aligned coordinates')
    parser.add_argument('--report', default='alignment_report.json',
                       help='JSON report file')
    parser.add_argument('--match-method', choices=['truncate', 'pad'], default='truncate',
                       help='Method to handle different atom counts')
    parser.add_argument('--max-atoms', type=int, default=None,
                       help='Maximum atoms for subsampling large structures')
    parser.add_argument('--subsample-method', choices=['uniform', 'random'], default='uniform',
                       help='Subsampling method for large structures')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        memory_gb = psutil.virtual_memory().available / (1024**3)
        logging.info(f"Available memory: {memory_gb:.2f} GB")
        
        logging.info("Loading coordinate files...")
        ref_coords = load_coordinates(args.reference)
        target_coords = load_coordinates(args.target)
        
        logging.info(f"Reference structure: {ref_coords.shape[0]} atoms")
        logging.info(f"Target structure: {target_coords.shape[0]} atoms")
        
        if args.max_atoms and ref_coords.shape[0] > args.max_atoms:
            logging.info(f"Subsampling structures to {args.max_atoms} atoms")
            ref_coords, ref_indices = subsample_structure(ref_coords, args.max_atoms, 
                                                         args.subsample_method)
            target_coords, target_indices = subsample_structure(target_coords, args.max_atoms, 
                                                               args.subsample_method)
        
        ref_matched, target_matched = match_atom_counts(ref_coords, target_coords, 
                                                       args.match_method)
        
        logging.info("Computing initial RMSD...")
        initial_rmsd = compute_rmsd(ref_matched, target_matched)
        logging.info(f"Initial RMSD: {initial_rmsd:.4f} Å")
        
        logging.info("Centering coordinates...")
        ref_centered, ref_centroid = center_coordinates(ref_matched)
        target_centered, target_centroid = center_coordinates(target_matched)
        
        logging.info("Performing Kabsch alignment...")
        rotation_matrix, final_rmsd, target_rotated = kabsch_alignment(ref_centered, target_centered)
        
        target_aligned = target_rotated + ref_centroid
        improvement = ((initial_rmsd - final_rmsd) / initial_rmsd) * 100
        
        logging.info("Saving results...")
        save_coordinates(target_aligned, args.output)
        
        report = create_report(initial_rmsd, final_rmsd, rotation_matrix, 
                             ref_centroid, target_centroid, len(ref_matched), improvement)
        
        with open(args.report, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Initial RMSD: {initial_rmsd:.4f} Å")
        print(f"Final RMSD: {final_rmsd:.4f} Å")
        print(f"Improvement: {improvement:.2f}%")
        print(f"Aligned coordinates saved to: {args.output}")
        print(f"Alignment report saved to: {args.report}")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
