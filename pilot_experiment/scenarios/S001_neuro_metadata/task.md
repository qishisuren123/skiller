Write a standalone Python CLI script that recursively scans a directory containing HDF5 (.h5) and MATLAB (.mat) files from a neuroscience experiment, extracts internal structure metadata (dataset paths, shapes, dtypes), and writes a meta.json file.

Requirements:
1. Use argparse: positional arg for root directory, -o/--output for output path (default: meta.json)
2. Recursively find all .h5 and .mat files
3. For HDF5: traverse nested groups, record each dataset's path, shape, and dtype
4. For MAT: read variable names, shapes, dtypes. Handle MATLAB v7.3 files (which scipy.io.loadmat cannot open) by falling back to h5py
5. Output valid JSON with a "files" key listing all file entries, each with at least "path" and "datasets"/"variables" info
6. Handle corrupted files gracefully (log error, continue scanning)
