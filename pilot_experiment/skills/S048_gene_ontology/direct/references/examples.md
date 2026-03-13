# Example 1: Basic GO enrichment analysis
"""
Command: python main.py --input "TP53,BRCA1,ATM,XRCC1" --output dna_repair.json

Expected output structure:
{
  "analysis_summary": {
    "input_gene_count": 4,
    "background_gene_count": 45,
    "total_go_terms_tested": 3,
    "significant_go_terms": 2
  },
  "enriched_go_terms": [
    {
      "go_id": "GO:0006281",
      "go_name": "DNA repair", 
      "input_gene_count": 4,
      "background_gene_count": 6,
      "enrichment_ratio": 7.5,
      "p_value": 0.001,
      "corrected_p_value": 0.003
    }
  ]
}
"""

# Example 2: Metabolic pathway analysis with custom background
"""
Command: python main.py --input "GAPDH ALDOA PGK1 ENO1" --background "GAPDH,ALDOA,PGK1,ENO1,PFKM,HK1,G6PD,ACTB,TUBB,MYC" --output metabolism.json

This analyzes glycolytic enzymes against a custom background set including both metabolic and non-metabolic genes. Expected to find significant enrichment in:
- GO:0006096 (glycolytic process) 
- GO:0008152 (metabolic process)
- GO:0006006 (glucose metabolic process)

The custom background prevents over-enrichment that might occur when using the full database as background.
"""
