# Proteomics Enrichment Analysis Workflow

## Step 1: Data Loading and Validation
- Load protein expression matrix from CSV file
- Validate sample column names match control/treatment groups
- Check for missing values and data quality issues
- Log data dimensions and basic statistics

## Step 2: Statistical Analysis
- Perform t-test for each protein between control and treatment groups
- Calculate log2 fold changes and mean expression levels
- Apply Benjamini-Hochberg multiple testing correction
- Filter significant proteins based on p-value and fold change thresholds

## Step 3: Protein ID Mapping
- Map mixed protein identifiers (gene symbols, UniProt IDs) to standardized UniProt accessions
- Use UniProt REST API with batch processing for efficiency
- Handle mapping failures gracefully and log success rates
- Create mapping dictionary for downstream analysis

## Step 4: GO Enrichment Analysis
- Retrieve GO annotations for mapped UniProt IDs
- Perform Fisher's exact test for each GO term
- Calculate enrichment ratios and odds ratios
- Apply multiple testing correction to enrichment p-values

## Step 5: KEGG Pathway Analysis
- Convert UniProt IDs to KEGG gene identifiers
- Retrieve pathway associations for each gene
- Perform pathway enrichment analysis using Fisher's exact test
- Get pathway names and descriptions from KEGG database

## Step 6: Visualization and Output
- Generate bubble plots showing enrichment significance and protein counts
- Create bar charts for top enriched terms/pathways
- Export all results to CSV files
- Save high-resolution plots as PNG files
