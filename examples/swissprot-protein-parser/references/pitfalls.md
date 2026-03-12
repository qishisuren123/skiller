# Common Pitfalls and Solutions

## Pitfall 1: JSON Structure Assumption
**Error**: KeyError: 'entries' when accessing data['entries']
**Root Cause**: Assumed JSON had nested structure with 'entries' key, but data was direct list
**Fix**: Added flexible structure detection checking for list vs dict and multiple possible keys

## Pitfall 2: Empty Text Arrays
**Error**: IndexError: list index out of range when accessing text_info[0]['value']
**Root Cause**: Some comment sections had empty text arrays
**Fix**: Implemented safe_extract_text() function with length checks and type validation

## Pitfall 3: Memory Overflow on Large Datasets
**Error**: MemoryError when creating DataFrame from 500K+ entries
**Root Cause**: Loading entire dataset into memory at once
**Fix**: Implemented streaming batch processing with incremental file writing

## Pitfall 4: Pandas Copy Warnings
**Error**: SettingWithCopyWarning when manipulating DataFrame
**Root Cause**: DataFrame operations on views instead of copies
**Fix**: Added explicit .copy() calls and proper data type handling with fillna()

## Pitfall 5: GO Annotation NaN Values
**Error**: GO annotations showing as NaN in output CSV
**Root Cause**: Improper handling of empty GO term lists and data type inconsistencies
**Fix**: Ensured GO annotations always return empty string instead of None, added proper validation

## Pitfall 6: Character Encoding Issues
**Error**: UnicodeDecodeError or corrupted characters in output
**Root Cause**: Missing UTF-8 encoding specification
**Fix**: Added explicit encoding='utf-8' for all file operations
