import subprocess
import json
import tempfile
import os
import sys
import numpy as np
from scipy.stats import fisher_exact

def create_data():
    """Create synthetic gene-GO mapping data"""
    # Create 200 background genes
    background_genes = [f"GENE_{i:03d}" for i in range(1, 201)]
    
    # Create 50 GO terms with descriptions
    go_terms = {}
    go_descriptions = [
        "cell division", "DNA repair", "protein folding", "metabolic process",
        "signal transduction", "transcription", "translation", "cell cycle",
        "apoptosis", "immune response", "development", "differentiation",
        "transport", "localization", "binding", "catalytic activity",
        "regulation", "response to stimulus", "cellular component organization",
        "biosynthetic process", "catabolic process", "homeostasis",
        "cell communication", "cell adhesion", "cell migration",
        "protein modification", "RNA processing", "DNA replication",
        "chromosome organization", "cell wall organization", "membrane organization",
        "cytoskeleton organization", "organelle organization", "vesicle transport",
        "protein transport", "ion transport", "carbohydrate metabolism",
        "lipid metabolism", "amino acid metabolism", "nucleotide metabolism",
        "energy metabolism", "photosynthesis", "respiration", "fermentation",
        "cell recognition", "cell death", "growth", "reproduction",
        "aging", "circadian rhythm"
    ]
    
    for i, desc in enumerate(go_descriptions):
        go_terms[f"GO:{i+1:07d}"] = desc
    
    # Create gene-GO mappings (each gene maps to 3-8 random GO terms)
    np.random.seed(42)
    gene_go_mapping = {}
    go_term_ids = list(go_terms.keys())
    
    for gene in background_genes:
        num_terms = np.random.randint(3, 9)
        mapped_terms = np.random.choice(go_term_ids, num_terms, replace=False)
        gene_go_mapping[gene] = mapped_terms.tolist()
    
    return background_genes, go_terms, gene_go_mapping

def run_test():
    background_genes, go_terms, gene_go_mapping = create_data()
    
    # Create test gene list (first 20 genes, biased toward certain GO terms)
    test_genes = background_genes[:20]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Test basic functionality
        genes_str = ",".join(test_genes)
        background_str = ",".join(background_genes)
        
        try:
            result = subprocess.run([
                sys.executable, "generated.py",
                "--genes", genes_str,
                "--background-genes", background_str,
                "--output", "results.json"
            ], capture_output=True, text=True, timeout=30)
            
            print(f"PASS: Script executed without errors")
            script_ran = True
        except Exception as e:
            print(f"FAIL: Script execution failed: {e}")
            script_ran = False
            return
        
        # Check if output file was created
        if os.path.exists("results.json"):
            print("PASS: Output JSON file created")
            output_created = True
        else:
            print("FAIL: Output JSON file not created")
            output_created = False
            return
        
        # Load and validate JSON structure
        try:
            with open("results.json", 'r') as f:
                results = json.load(f)
            print("PASS: Output file is valid JSON")
            valid_json = True
        except:
            print("FAIL: Output file is not valid JSON")
            valid_json = False
            return
        
        # Check if results is a list
        if isinstance(results, list):
            print("PASS: Results is a list")
            is_list = True
        else:
            print("FAIL: Results is not a list")
            is_list = False
            return
        
        # Check if results contain required fields
        required_fields = ["go_term", "description", "gene_count", "background_count", 
                          "enrichment_ratio", "p_value", "corrected_p_value"]
        has_required_fields = True
        if results:
            for field in required_fields:
                if field not in results[0]:
                    has_required_fields = False
                    break
        
        if has_required_fields and results:
            print("PASS: Results contain required fields")
        else:
            print("FAIL: Results missing required fields")
            has_required_fields = False
        
        # Check gene count filtering (>= 2 genes)
        gene_count_filter = True
        if results:
            for result in results:
                if result.get("gene_count", 0) < 2:
                    gene_count_filter = False
                    break
        
        if gene_count_filter:
            print("PASS: All results have gene_count >= 2")
        else:
            print("FAIL: Some results have gene_count < 2")
        
        # Check p-value filtering (< 0.05)
        pvalue_filter = True
        if results:
            for result in results:
                if result.get("corrected_p_value", 1.0) >= 0.05:
                    pvalue_filter = False
                    break
        
        if pvalue_filter:
            print("PASS: All results have corrected p-value < 0.05")
        else:
            print("FAIL: Some results have corrected p-value >= 0.05")
        
        # Check if results are sorted by corrected p-value
        sorted_results = True
        if len(results) > 1:
            for i in range(1, len(results)):
                if results[i]["corrected_p_value"] < results[i-1]["corrected_p_value"]:
                    sorted_results = False
                    break
        
        if sorted_results:
            print("PASS: Results sorted by corrected p-value")
        else:
            print("FAIL: Results not sorted by corrected p-value")
        
        # Check enrichment ratio calculation
        enrichment_calc = True
        if results:
            for result in results:
                gene_count = result.get("gene_count", 0)
                background_count = result.get("background_count", 1)
                expected_ratio = result.get("enrichment_ratio", 0)
                
                # Calculate expected enrichment ratio
                input_size = len(test_genes)
                background_size = len(background_genes)
                observed_freq = gene_count / input_size
                expected_freq = background_count / background_size
                calc_ratio = observed_freq / expected_freq if expected_freq > 0 else 0
                
                if abs(expected_ratio - calc_ratio) > 0.01:
                    enrichment_calc = False
                    break
        
        if enrichment_calc:
            print("PASS: Enrichment ratios calculated correctly")
        else:
            print("FAIL: Enrichment ratios calculated incorrectly")
        
        # Check GO term format
        go_format = True
        if results:
            for result in results:
                go_term = result.get("go_term", "")
                if not go_term.startswith("GO:"):
                    go_format = False
                    break
        
        if go_format:
            print("PASS: GO terms have correct format")
        else:
            print("FAIL: GO terms have incorrect format")
        
        # Test with space-separated genes
        try:
            genes_space = " ".join(test_genes[:10])
            result = subprocess.run([
                sys.executable, "generated.py",
                "--genes", genes_space,
                "--background-genes", background_str,
                "--output", "results2.json"
            ], capture_output=True, text=True, timeout=30)
            
            space_separated = os.path.exists("results2.json")
            if space_separated:
                print("PASS: Handles space-separated gene lists")
            else:
                print("FAIL: Does not handle space-separated gene lists")
        except:
            print("FAIL: Error with space-separated gene lists")
            space_separated = False
        
        # Test error handling with invalid genes
        try:
            result = subprocess.run([
                sys.executable, "generated.py",
                "--genes", "INVALID1,INVALID2",
                "--background-genes", background_str,
                "--output", "results3.json"
            ], capture_output=True, text=True, timeout=30)
            
            error_handling = True
            print("PASS: Handles invalid gene IDs gracefully")
        except:
            print("FAIL: Does not handle invalid gene IDs")
            error_handling = False
        
        # Calculate completeness score
        completeness_components = [
            script_ran, output_created, valid_json, is_list, 
            has_required_fields, gene_count_filter, pvalue_filter
        ]
        completeness_score = sum(completeness_components) / len(completeness_components)
        print(f"SCORE: completeness {completeness_score:.3f}")
        
        # Calculate accuracy score
        accuracy_components = [
            sorted_results, enrichment_calc, go_format, 
            space_separated, error_handling
        ]
        accuracy_score = sum(accuracy_components) / len(accuracy_components)
        print(f"SCORE: accuracy {accuracy_score:.3f}")

if __name__ == "__main__":
    run_test()
