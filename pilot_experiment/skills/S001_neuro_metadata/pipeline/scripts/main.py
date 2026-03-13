#!/usr/bin/env python3
import argparse
import json
import os
import h5py
import scipy.io
import numpy as np
from pathlib import Path
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def make_json_serializable(obj):
    """Convert numpy types to JSON serializable types"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.dtype, type)):
        return str(obj)
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    else:
        return obj

def safe_get_shape_dtype(data):
    """Safely extract shape and dtype from various MATLAB data types"""
    try:
        # Handle cell arrays and other object arrays
        if hasattr(data, 'dtype') and data.dtype == 'object':
            return {
                'shape': list(data.shape) if hasattr(data, 'shape') else 'unknown',
                'dtype': 'cell' if 'cell' in str(type(data)) else 'object'
            }
        # Handle regular arrays
        elif hasattr(data, 'shape') and hasattr(data, 'dtype'):
            return {
                'shape': make_json_serializable(list(data.shape)),
                'dtype': str(data.dtype)
            }
        else:
            return {'shape': 'unknown', 'dtype': str(type(data))}
    except Exception:
        return {'shape': 'unknown', 'dtype': 'unknown'}

def scan_hdf5_file(filepath):
    """Extract metadata from HDF5 file"""
    datasets = []
    
    def visitor(name, obj):
        if isinstance(obj, h5py.Dataset):
            datasets.append({
                'path': name,
                'shape': make_json_serializable(list(obj.shape)),
                'dtype': str(obj.dtype)
            })
    
    try:
        with h5py.File(filepath, 'r') as f:
            f.visititems(visitor)
    except Exception as e:
        logging.error(f"Failed to read HDF5 file {filepath}: {e}")
        return None
    
    return datasets

def scan_mat_file(filepath):
    """Extract metadata from MATLAB file"""
    variables = []
    
    try:
        # Try scipy.io.loadmat first
        mat_data = scipy.io.loadmat(filepath)
        for name, data in mat_data.items():
            if not name.startswith('__'):  # Skip metadata variables
                shape_dtype = safe_get_shape_dtype(data)
                variables.append({
                    'name': name,
                    'shape': shape_dtype['shape'],
                    'dtype': shape_dtype['dtype']
                })
    except NotImplementedError:
        # Fall back to h5py for v7.3 files
        try:
            with h5py.File(filepath, 'r') as f:
                # For MATLAB v7.3, variables are stored at the root level
                for name in f.keys():
                    if not name.startswith('#'):  # Skip MATLAB internal references
                        obj = f[name]
                        if isinstance(obj, h5py.Dataset):
                            variables.append({
                                'name': name,
                                'shape': make_json_serializable(list(obj.shape)),
                                'dtype': str(obj.dtype)
                            })
                        elif isinstance(obj, h5py.Group):
                            # Handle structured variables
                            variables.append({
                                'name': name,
                                'shape': 'struct',
                                'dtype': 'group'
                            })
        except Exception as e:
            logging.error(f"Failed to read MATLAB file {filepath}: {e}")
            return None
    except Exception as e:
        logging.error(f"Failed to read MATLAB file {filepath}: {e}")
        return None
    
    return variables

def find_data_files(root_dir):
    """Find all .h5 and .mat files, return list for progress tracking"""
    data_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(('.h5', '.mat')):
                data_files.append(os.path.join(root, file))
    return data_files

def main():
    parser = argparse.ArgumentParser(description='Extract metadata from neuroscience data files')
    parser.add_argument('root_dir', help='Root directory to scan')
    parser.add_argument('-o', '--output', default='meta.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.exists(args.root_dir):
        print(f"Error: Directory '{args.root_dir}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(args.root_dir):
        print(f"Error: '{args.root_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Convert to absolute path for consistent relative path calculation
    root_dir = os.path.abspath(args.root_dir)
    
    # Find all data files first for progress tracking
    print("Scanning for data files...")
    data_files = find_data_files(root_dir)
    
    if not data_files:
        print("No .h5 or .mat files found in the specified directory")
        sys.exit(0)
    
    print(f"Found {len(data_files)} data files. Processing...")
    
    files_metadata = []
    
    # Process files with progress indicator
    for i, filepath in enumerate(data_files, 1):
        relative_path = os.path.relpath(filepath, root_dir)
        print(f"Processing {i}/{len(data_files)}: {relative_path}")
        
        if filepath.endswith('.h5'):
            datasets = scan_hdf5_file(filepath)
            if datasets is not None:
                files_metadata.append({
                    'path': relative_path,
                    'type': 'hdf5',
                    'datasets': datasets
                })
        else:  # .mat file
            variables = scan_mat_file(filepath)
            if variables is not None:
                files_metadata.append({
                    'path': relative_path,
                    'type': 'matlab',
                    'variables': variables
                })
    
    # Write output
    output_data = {'files': files_metadata}
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Metadata extracted for {len(files_metadata)} files -> {args.output}")

if __name__ == '__main__':
    main()
