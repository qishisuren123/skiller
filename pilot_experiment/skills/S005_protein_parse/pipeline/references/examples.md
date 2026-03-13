# Safe nested JSON parsing
protein_name = ''
if 'protein' in entry:
    if 'recommendedName' in entry['protein']:
        protein_name = entry['protein']['recommendedName'].get('fullName', '')
    elif 'alternativeName' in entry['protein']:
        alt_names = entry['protein']['alternativeName']
        if isinstance(alt_names, list) and len(alt_names) > 0:
            protein_name = alt_names[0].get('fullName', '')

# Multiple gene name handling
gene_names = []
if 'gene' in entry and isinstance(entry['gene'], list):
    for gene in entry['gene']:
        if 'name' in gene:
            gene_names.append(gene['name'])
gene_name = ';'.join(gene_names)

# Streaming large JSON arrays
with open(args.input, 'rb') as infile:
    proteins = ijson.items(infile, 'item')
    for protein in proteins:
        # Process one at a time
        processed = parse_protein_entry(protein)

# Safe average calculation
proteins_with_sequences = [p for p in data if p['sequence_length'] > 0]
if proteins_with_sequences:
    avg = sum(p['sequence_length'] for p in proteins_with_sequences) / len(proteins_with_sequences)
