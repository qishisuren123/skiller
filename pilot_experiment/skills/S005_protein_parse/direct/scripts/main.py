import json
import pandas as pd
import argparse
import sys
from pathlib import Path

def safe_get_nested(data, keys, default=''):
    """Safely navigate nested dictionary structure."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and current:
            current = current[0].get(key) if isinstance(current[0], dict) else None
        else:
            return default
        if current is None:
            return default
    return current

def extract_protein_data(entry):
    """Extract structured data from a SwissProt protein entry."""
    # Basic fields with safe extraction
    accession = entry.get('accession', '')
    
    # Protein name from nested structure
    protein_name = safe_get_nested(entry, ['protein', 'recommendedName', 'fullName', 'value'])
    
    # Gene name - handle list structure
    gene_name = ''
    if entry.get('gene') and isinstance(entry['gene'], list) and entry['gene']:
        gene_name = safe_get_nested(entry['gene'][0], ['name', 'value'])
    
    # Organism name from nested structure
    organism = ''
    organism_names = entry.get('organism', {}).get('name', [])
    if organism_names and isinstance(organism_names, list):
        organism = safe_get_nested(organism_names[0], ['value'])
    
    # Sequence length
    sequence_length = 0
    sequence_data = entry.get('sequence', {})
    if sequence_data and sequence_data.get('value'):
        sequence_length = len(sequence_data['value'])
    
    # Number of features
    features_count = len(entry.get('features', []))
    
    # Extract GO terms from dbReferences
    go_terms = []
    for ref in entry.get('dbReferences', []):
        if ref.get('type') == 'GO' and ref.get('id'):
            go_terms.append(ref['id'])
    
    return {
        'accession': accession,
        'protein_name': protein_name,
        'gene_name': gene_name,
        'organism': organism,
        'sequence_length': sequence_length,
        'number_of_features': features_count,
        'GO_terms': ';'.join(go_terms)
    }

def parse_swissprot_json(input_file, output_file):
    """Parse SwissProt JSON file and extract structured data to CSV."""
    try:
        # Load JSON data
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both list and single entry formats
        if isinstance(data, dict):
            entries = [data]
        elif isinstance(data, list):
            entries = data
        else:
            raise ValueError("JSON must contain a list of entries or a single entry")
        
        # Extract data from each entry
        extracted_data = []
        for entry in entries:
            try:
                protein_data = extract_protein_data(entry)
                extracted_data.append(protein_data)
            except Exception as e:
                print(f"Warning: Error processing entry {entry.get('accession', 'unknown')}: {e}")
                continue
        
        if not extracted_data:
            print("No valid protein entries found in the input file.")
            return
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(extracted_data)
        
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV with UTF-8 encoding
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        # Generate summary statistics
        total_proteins = len(df)
        unique_organisms = df['organism'].nunique()
        avg_sequence_length = df['sequence_length'].mean()
        
        print(f"Processing complete!")
        print(f"Total proteins: {total_proteins}")
        print(f"Unique organisms: {unique_organisms}")
        print(f"Average sequence length: {avg_sequence_length:.1f}")
        print(f"Output saved to: {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{input_file}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Parse SwissProt protein entries from JSON and extract structured information to CSV'
    )
    parser.add_argument(
        '--input', 
        required=True, 
        help='Path to input JSON file containing SwissProt protein entries'
    )
    parser.add_argument(
        '--output', 
        required=True, 
        help='Path to output CSV file'
    )
    
    args = parser.parse_args()
    
    parse_swissprot_json(args.input, args.output)

if __name__ == '__main__':
    main()
