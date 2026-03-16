#!/usr/bin/env python3
import argparse
import json
import os
import logging
from pathlib import Path
import h5py
import scipy.io
import numpy as np
import math
from collections import deque

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Global error tracking
processing_errors = []

def log_error(filepath, error_msg):
    """Log error and add to global error tracking."""
    error_entry = {
        'file': str(filepath),
        'error': error_msg
    }
    processing_errors.append(error_entry)
    logging.error(f"Error processing {filepath}: {error_msg}")

def make_json_serializable(obj):
    """Convert numpy types to JSON-serializable Python types, handling edge cases."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        if math.isnan(obj) or math.isinf(obj):
            return None  # Convert NaN/inf to null in JSON
        return float(obj)
    elif isinstance(obj, (int, float)):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return obj
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    else:
        return obj

def extract_hdf5_metadata(filepath, max_depth=100):
    """Extract metadata from HDF5 files using iterative traversal to avoid recursion limits."""
    datasets = []
    
    try:
        with h5py.File(filepath, 'r') as f:
            # Use iterative approach with queue to avoid recursion limits
            queue = deque([(f, "", 0)])  # (object, path, depth)
            
            while queue:
                obj, path, depth = queue.popleft()
                
                if depth > max_depth:
                    logging.warning(f"Maximum depth {max_depth} reached in {filepath}")
                    continue
                
                if isinstance(obj, h5py.Dataset):
                    try:
                        size_bytes = int(obj.size * obj.dtype.itemsize)
                        if size_bytes < 0:
                            size_bytes = None
                    except (OverflowError, ValueError):
                        size_bytes = None
                        
                    datasets.append({
                        'name': path,
                        'shape': make_json_serializable(list(obj.shape)),
                        'dtype': str(obj.dtype),
                        'size_bytes': size_bytes
                    })
                elif isinstance(obj, h5py.Group):
                    for key in obj.keys():
                        child_path = f"{path}/{key}" if path else key
                        queue.append((obj[key], child_path, depth + 1))
        
        return datasets
    except Exception as e:
        log_error(filepath, str(e))
        return []

def extract_mat_metadata(filepath):
    """Extract metadata from MATLAB files without loading data."""
    datasets = []
    
    try:
        # Use whosmat to get metadata without loading data
        mat_info = scipy.io.whosmat(filepath)
        for name, shape, dtype in mat_info:
            datasets.append({
                'name': name,
                'shape': make_json_serializable(list(shape)),
                'dtype': dtype
            })
        return datasets
    except Exception as e:
        logging.warning(f"scipy.io.whosmat failed for {filepath}: {e}")
        logging.info(f"Trying h5py fallback for MATLAB v7.3 file: {filepath}")
        
        # Fallback to h5py for MATLAB v7.3 files
        try:
            return extract_hdf5_metadata(filepath)
        except Exception as e2:
            log_error(filepath, f"Both scipy.io and h5py failed: {e2}")
            return []

def scan_directory(root_dir):
    """Recursively scan directory for .h5 and .mat files."""
    files_metadata = []
    root_path = Path(root_dir)
    
    for filepath in root_path.rglob('*'):
        if filepath.suffix.lower() in ['.h5', '.hdf5']:
            logging.info(f"Processing HDF5: {filepath}")
            datasets = extract_hdf5_metadata(filepath)
            files_metadata.append({
                'path': str(filepath),
                'type': 'hdf5',
                'datasets': datasets
            })
        elif filepath.suffix.lower() == '.mat':
            logging.info(f"Processing MAT: {filepath}")
            datasets = extract_mat_metadata(filepath)
            files_metadata.append({
                'path': str(filepath),
                'type': 'matlab',
                'datasets': datasets
            })
    
    return files_metadata

def main():
    parser = argparse.ArgumentParser(description='Extract metadata from HDF5 and MATLAB files')
    parser.add_argument('directory', help='Root directory to scan')
    parser.add_argument('-o', '--output', default='meta.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    setup_logging()
    
    if not os.path.exists(args.directory):
        logging.error(f"Directory {args.directory} does not exist")
        return 1
    
    logging.info(f"Scanning directory: {args.directory}")
    files_metadata = scan_directory(args.directory)
    
    output_data = {
        'files': files_metadata,
        'total_files': len(files_metadata),
        'processing_errors': processing_errors,
        'error_count': len(processing_errors)
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logging.info(f"Metadata written to {args.output}")
    if processing_errors:
        logging.warning(f"Processing completed with {len(processing_errors)} errors")
    else:
        logging.info("Processing completed successfully with no errors")
    
    return 0

if __name__ == '__main__':
    exit(main())
