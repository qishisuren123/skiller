#!/usr/bin/env python3
import argparse
import csv
from collections import Counter

try:
    import ijson
except ImportError:
    print("Error: ijson library is required for streaming JSON parsing.")
    print("Install it with: pip install ijson")
    exit(1)

def parse_protein_entry(entry):
    """Extract structured information from a protein entry"""
    accession = entry.get('accession', '')
    
    # Handle nested protein name structure - try recommendedName first, then alternativeName
    protein_name = ''
    if 'protein' in entry:
        if 'recommendedName' in entry['protein']:
            protein_name = entry['protein']['recommendedName'].get('fullName', '')
        elif 'alternativeName' in entry['protein']:
            # alternativeName might be a list or a single object
            alt_names = entry['protein']['alternativeName']
            if isinstance(alt_names, list) and len(alt_names) > 0:
                protein_name = alt_names[0].get('fullName', '')
            elif isinstance(alt_names, dict):
                protein_name = alt_names.get('fullName', '')
    
    # Handle gene names - collect all names from the list
    gene_names = []
    if 'gene' in entry and isinstance(entry['gene'], list):
        for gene in entry['gene']:
            if 'name' in gene:
                gene_names.append(gene['name'])
    gene_name = ';'.join(gene_names)
    
    # Handle organism - nested structure
    organism = ''
    if 'organism' in entry:
        organism = entry['organism'].get('scientificName', '')
    
    # Handle sequence - nested with 'value' key
    sequence_length = 0
    if 'sequence' in entry and 'value' in entry['sequence']:
        sequence_length = len(entry['sequence']['value'])
    
    number_of_features = len(entry.get('features', []))
    
    # Extract GO terms from dbReferences
    go_terms = []
    db_refs = entry.get('dbReferences', [])
    for ref in db_refs:
        if ref.get('type') == 'GO':
            go_terms.append(ref.get('id', ''))
    
    return {
        'accession': accession,
        'protein_name': protein_name,
        'gene_name': gene_name,
        'organism': organism,
        'sequence_length': sequence_length,
        'number_of_features': number_of_features,
        'GO_terms': ';'.join(go_terms)
    }

def main():
    parser = argparse.ArgumentParser(description='Parse SwissProt protein entries from JSON to CSV')
    parser.add_argument('--input', required=True, help='Input JSON file path')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    args = parser.parse_args()
    
    # Initialize summary statistics
    total_proteins = 0
    organisms = set()
    total_sequence_length = 0
    proteins_with_sequences = 0
    
    # Process file in streaming fashion
    fieldnames = ['accession', 'protein_name', 'gene_name', 'organism', 'sequence_length', 'number_of_features', 'GO_terms']
    
    with open(args.input, 'rb') as infile, open(args.output, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Stream parse the JSON array - correct ijson usage
        proteins = ijson.items(infile, 'item')
        
        for protein in proteins:
            processed_protein = parse_protein_entry(protein)
            writer.writerow(processed_protein)
            
            # Update statistics
            total_proteins += 1
            if processed_protein['organism']:
                organisms.add(processed_protein['organism'])
            if processed_protein['sequence_length'] > 0:
                total_sequence_length += processed_protein['sequence_length']
                proteins_with_sequences += 1
            
            # Progress indicator for large files
            if total_proteins % 1000 == 0:
                print(f"Processed {total_proteins} proteins...")
    
    # Print summary
    organism_count = len(organisms)
    if proteins_with_sequences > 0:
        avg_seq_length = total_sequence_length / proteins_with_sequences
        print(f"Total proteins: {total_proteins}")
        print(f"Number of organisms: {organism_count}")
        print(f"Average sequence length: {avg_seq_length:.2f} (based on {proteins_with_sequences} proteins with sequences)")
    else:
        print(f"Total proteins: {total_proteins}")
        print(f"Number of organisms: {organism_count}")
        print("Average sequence length: N/A (no proteins with sequence data)")

if __name__ == '__main__':
    main()
