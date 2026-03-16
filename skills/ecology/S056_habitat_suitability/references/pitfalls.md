# Common Pitfalls and Solutions

## Filename Space Error
**Error**: ValueError: cannot save file with spaces
**Root Cause**: Species names containing spaces caused filesystem compatibility issues when creating output filenames
**Fix**: Implemented sanitize_filename() function using regex to replace spaces with underscores and remove special characters, ensuring filesystem-safe filenames while preserving original names in displays

## Memory Allocation Error  
**Error**: MemoryError: Unable to allocate 18.6 GiB for an array
**Root Cause**: Large grid sizes (10000x10000) caused numpy.argpartition to attempt massive temporary array allocation for finding top locations
**Fix**: Replaced single argpartition call with chunked processing approach, processing data in 1M element chunks and maintaining running list of top values to avoid memory overflow
