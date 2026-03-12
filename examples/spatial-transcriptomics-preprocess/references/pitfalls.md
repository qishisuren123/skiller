# Common Pitfalls and Solutions

## Error 1: File Format Recognition
**Error**: ValueError: Unable to open file (file signature not found)
**Root Cause**: Using sc.read_h5ad() for 10X Genomics HDF5 files instead of sc.read_10x_h5()
**Fix**: Use sc.read_10x_h5() for 10X format files and sc.read_h5ad() only for AnnData format files

## Error 2: Raw Data Loss
**Error**: AttributeError: 'NoneType' object has no attribute 'X'
**Root Cause**: Overwriting adata.raw during normalization steps, losing access to original counts
**Fix**: Store raw data before filtering and preserve filtered raw counts in layers['raw_filtered'] for STAGATE

## Error 3: Plotting Function Compatibility
**Error**: TypeError: violin() got an unexpected keyword argument 'multi_panel'
**Root Cause**: Using deprecated or incorrect parameters for scanpy plotting functions
**Fix**: Replace sc.pl.violin() with matplotlib histograms or use correct scanpy plotting parameters

## Error 4: Aggressive Filtering
**Error**: Excessive spot loss during quality control (>30% of spots removed)
**Root Cause**: Using single-cell RNA-seq filtering parameters for spatial transcriptomics data
**Fix**: Use more lenient parameters: min_genes=100 (vs 200), max_genes=8000 (vs 5000), max_mt_pct=25% (vs 20%)

## Error 5: STAGATE Performance Issues
**Error**: Memory errors or extremely slow processing with STAGATE
**Root Cause**: Running STAGATE on full large datasets without optimization
**Fix**: Subsample datasets >5000 spots to 3000 spots, reduce n_epochs from 1000 to 500, adjust spatial network radius
