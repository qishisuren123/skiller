## Word Overlap False Positives

**Error**: Simple word overlap similarity flagged clearly different questions as duplicates (e.g., "What is the band gap of silicon?" vs "What is the crystal structure of silicon?" scored 0.923 similar)

**Root Cause**: Materials science questions share many common domain terms like "silicon", "what", "is", making basic word overlap too aggressive for distinguishing genuinely different questions

**Fix**: Implemented weighted n-gram similarity with stop word downweighting and TF-IDF-like scoring to better handle domain-specific vocabulary patterns

## Division by Zero on Empty Results

**Error**: ZeroDivisionError when calculating average instruction/output lengths after all entries were removed during cleaning

**Root Cause**: Overly aggressive duplicate detection removed all entries, leaving empty cleaned dataset for statistics calculation

**Fix**: Added check for empty cleaned_entries list before calculating averages and improved duplicate detection algorithm to be less aggressive

## Missing External Dependencies

**Error**: ModuleNotFoundError for 'sklearn' when trying to use TfidfVectorizer for similarity calculation

**Root Cause**: Attempted to use scikit-learn for text similarity without ensuring dependency availability in target environment

**Fix**: Implemented custom n-gram similarity using only Python standard library modules (collections, re, hashlib) to avoid external dependencies

## O(n²) Performance Bottleneck

**Error**: Duplicate detection taking 30+ minutes on 15,000 entry dataset due to comparing all possible pairs

**Root Cause**: Naive approach comparing every entry with every other entry results in 112+ million comparisons for large datasets

**Fix**: Implemented Locality-Sensitive Hashing (LSH) with MinHash signatures to reduce comparisons to only likely candidate pairs, reducing runtime to ~3 minutes

## JSON Serialization Type Error

**Error**: TypeError "Object of type Counter is not JSON serializable" when writing cleaning report

**Root Cause**: Counter objects from collections module cannot be directly serialized to JSON format

**Fix**: Explicitly convert all Counter objects to regular dictionaries using dict() before JSON serialization in report generation
