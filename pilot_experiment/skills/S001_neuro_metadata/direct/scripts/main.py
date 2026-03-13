#!/usr/bin/env python3
"""
Neuroscience Data Structure Scanner
Recursively scans directories for HDF5 and MATLAB files, extracting metadata.
"""

import argparse
import json
import os
import sys
import logging
from pathlib import Path

import h5py
import scipy.io
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def extract_hdf5_metadata(filepath):
    """Extract metadata from HDF5 files."""
    metadata = {"datasets": []}
    
    try:
        with h5py.File(filepath, 'r') as f:
            def visitor(name, obj):
                if isinstance(obj, h5py.Dataset):
                    metadata["datasets"].append({
                        "path": name,
                        "shape": list(obj.shape),
                        "dtype": str(obj.dtype)
                    })
            f.visititems(visitor)
    except Exception as e:
        raise Exception(f"Failed to read HDF5 file: {e}")
    
    return metadata

def extract_matlab_metadata(filepath):
    """Extract metadata from MATLAB files, handling both v7.3 and older formats."""
    metadata = {"variables": []}
    
    # First try scipy.io.loadmat for older MATLAB files
    try:
        mat_data = scipy.io.loadmat(filepath, struct_as_record=False, squeeze_me=False)
        
        for var_name, var_data in mat_data.items():
            # Skip MATLAB metadata variables
            if var_name.startswith('__'):
                continue
                
            metadata["variables"].append({
                "name": var_name,
                "shape": list(var_data.shape) if hasattr(var_data, 'shape') else [],
                "dtype": str(var_data.dtype) if hasattr(var_data, 'dtype') else str(type(var_data))
            })
            
    except (NotImplementedError, ValueError):
        # MATLAB v7.3 files are actually HDF5 format
        logger.info(f"Falling back to HDF5 reader for MATLAB v7.3 file: {filepath}")
        try:
            with h5py.File(filepath, 'r') as f:
                def visitor(name, obj):
                    if isinstance(obj, h5py.Dataset):
                        # Clean up MATLAB-specific paths
                        clean_name = name.replace('#refs#', 'refs').replace('#subsystem#', 'subsystem')
                        metadata["variables"].append({
                            "name": clean_name,
                            "shape": list(obj.shape),
                            "dtype": str(obj.dtype)
                        })
                f.visititems(visitor)
        except Exception as e:
            raise Exception(f"Failed to read MATLAB file with HDF5 fallback: {e}")
    
    except Exception as e:
        raise Exception(f"Failed to read MATLAB file: {e}")
    
    return metadata

def find_data_files(root_dir):
    """Recursively find all .h5 and .mat files."""
    data_files = []
    root_path = Path(root_dir)
    
    if not root_path.exists():
        raise FileNotFoundError(f"Directory does not exist: {root_dir}")
    
    # Find all relevant files
    for pattern in ['**/*.h5', '**/*.mat']:
        data_files.extend(root_path.glob(pattern))
    
    return sorted(data_files)

def process_file(filepath, root_dir):
    """Process a single data file and extract metadata."""
    rel_path = os.path.relpath(filepath, root_dir)
    file_info = {
        "path": rel_path,
        "absolute_path": str(filepath),
        "size_bytes": filepath.stat().st_size
    }
    
    try:
        if filepath.suffix.lower() == '.h5':
            metadata = extract_hdf5_metadata(filepath)
            file_info.update(metadata)
            file_info["file_type"] = "HDF5"
            
        elif filepath.suffix.lower() == '.mat':
            metadata = extract_matlab_metadata(filepath)
            file_info.update(metadata)
            file_info["file_type"] = "MATLAB"
            
        logger.info(f"Processed: {rel_path}")
        
    except Exception as e:
        logger.error(f"Error processing {rel_path}: {e}")
        file_info["error"] = str(e)
        file_info["status"] = "error"
    
    return file_info

def main():
    parser = argparse.ArgumentParser(
        description="Scan directory for neuroscience data files and extract metadata"
    )
    parser.add_argument(
        "directory",
        help="Root directory to scan for .h5 and .mat files"
    )
    parser.add_argument(
        "-o", "--output",
        default="meta.json",
        help="Output JSON file path (default: meta.json)"
    )
    
    args = parser.parse_args()
    
    try:
        # Find all data files
        logger.info(f"Scanning directory: {args.directory}")
        data_files = find_data_files(args.directory)
        logger.info(f"Found {len(data_files)} data files")
        
        # Process each file
        results = {
            "scan_directory": os.path.abspath(args.directory),
            "total_files": len(data_files),
            "files": []
        }
        
        for filepath in data_files:
            file_info = process_file(filepath, args.directory)
            results["files"].append(file_info)
        
        # Create output directory if needed
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write results to JSON
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Metadata written to: {output_path}")
        
        # Summary
        successful = len([f for f in results["files"] if "error" not in f])
        failed = len(results["files"]) - successful
        logger.info(f"Summary: {successful} successful, {failed} failed")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
