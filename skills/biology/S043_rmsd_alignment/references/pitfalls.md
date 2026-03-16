## Atom Count Mismatch Error

**Error**: ValueError: operands could not be broadcast together with shapes (1247,3) (1250,3)

**Root Cause**: MD simulation structures had different numbers of atoms due to varying water molecules or missing residues

**Fix**: Implemented match_atom_counts() function with truncate/pad options to handle size differences

## Numpy Compatibility Error  

**Error**: AttributeError: 'numpy.ndarray' object has no attribute 'T'

**Root Cause**: Older numpy versions (1.16.4) had inconsistent .T attribute support for matrix operations

**Fix**: Replaced .T with np.transpose() and @ operator with np.dot() for better version compatibility

## Memory Allocation Error

**Error**: MemoryError: Unable to allocate 381.47 MiB for array with shape (50000,) and data type int64

**Root Cause**: np.random.choice() function allocating large internal arrays for subsampling large structures

**Fix**: Implemented memory-efficient subsampling using iterative random selection instead of vectorized operations
