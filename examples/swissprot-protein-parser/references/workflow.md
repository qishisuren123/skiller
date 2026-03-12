# SwissProt Protein Parser Workflow

## Step 1: Input Validation
- Validate input JSON file exists and is readable
- Check JSON structure (list vs nested dict)
- Identify entry format and field variations

## Step 2: Structure Detection
- Detect if entries are direct list or nested under keys like 'entries', 'results', 'data'
- Handle single entry vs multiple entries
- Validate entry format consistency

## Step 3: Streaming Processing
- Process entries in configurable batches (default 1000)
- Parse each entry individually with error handling
- Extract structured fields: protein_id, protein_name, function_description, go_annotations, subcellular_location, sequence

## Step 4: Field Extraction
- Use safe_extract_text() for handling various text formats
- Try multiple field names for protein ID (accession, accessions, primaryAccession, id)
- Process comments array for function and subcellular location
- Extract GO annotations from dbReference array

## Step 5: Data Validation
- Ensure all fields have proper data types
- Handle empty arrays and null values
- Clean sequence data (remove whitespace/newlines)
- Calculate sequence lengths

## Step 6: Output Generation
- Stream write to CSV with headers or JSON with metadata
- Include parsing statistics and error counts
- Generate optional statistics file

## Step 7: Error Reporting
- Log individual entry parsing errors
- Report batch processing progress
- Provide comprehensive statistics summary
