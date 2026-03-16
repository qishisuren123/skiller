# Common Pitfalls and Solutions

## Encoding Issues with Detector Data

**Error**: UnicodeDecodeError: 'utf-8' codec can't decode byte 0x89 in position 0: invalid start byte

**Root Cause**: Detector software exports data in non-UTF-8 encodings (latin-1, cp1252) or binary formats

**Fix**: Implement multiple encoding attempts in load_data() function, trying utf-8, latin-1, cp1252, and iso-8859-1 sequentially

## String Values in Numeric Columns

**Error**: TypeError: bad operand type for abs(): 'str'

**Root Cause**: Detector outputs missing values as strings ("N/A", "-") instead of proper NaN values

**Fix**: Replace string missing indicators with NaN, then use pd.to_numeric(errors='coerce') to convert columns safely

## Unrealistic Statistical Significance

**Error**: Significance values of 45+ which are impossible in particle physics

**Root Cause**: Using total background count instead of background specifically in the signal region

**Fix**: Calculate significance only for events within the mass window: S / sqrt(S + B) where S and B are region-specific

## DataFrame View Warnings

**Error**: SettingWithCopyWarning when adding event_type column

**Root Cause**: Trying to modify a DataFrame slice/view instead of the actual data

**Fix**: Use .copy() method after filtering operations and use .loc[:, column] for assignments to ensure proper DataFrame handling
