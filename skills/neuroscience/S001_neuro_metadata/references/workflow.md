1. Install dependencies: pip install -r requirements.txt
2. Run script: python scripts/main.py /path/to/data/directory
3. Script recursively finds all .h5, .hdf5, and .mat files
4. For each HDF5 file: Uses iterative traversal with h5py to extract dataset metadata
5. For each MATLAB file: Uses scipy.io.whosmat() for memory-efficient metadata extraction
6. Falls back to h5py for MATLAB v7.3 files (HDF5-based format)
7. Handles edge cases: NaN/infinity values, JSON serialization, memory constraints
8. Outputs standardized JSON with consistent "datasets" structure for both file types
9. Provides comprehensive error tracking and summary in output
10. Check processing_errors array in output for any failed files
