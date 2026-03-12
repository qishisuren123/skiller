---
name: proteomics-enrichment-analysis
description: "对差异蛋白原始实验数据进行富集分析和数据处理。包括：读取差异蛋白表达矩阵，进行统计检验(t-test/limma)筛选差异蛋白，对差异蛋白进行GO富集分析和KEGG通路分析，生成富集结果表格和可视化（气泡图、柱状图）。同样适用于多组学数据输入。工具: limma, KEGG API, STRING API, numpy, pandas, scipy, matplotlib。 Use this skill when the user needs to 对差异蛋白原始实验数据进行富集分析和数据处理。包括：读取差异蛋白表达矩阵，进行统计检验(t-test/limma)筛选差异蛋白，对差异蛋白进行go富集分析和kegg通路分析，生成富集结果表格和可视化（."
license: MIT
compatibility: "Python >=3.9; pandas, numpy, scipy, matplotlib, requests, goatools"
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---

# Proteomics Enrichment Analysis

## Overview
Comprehensive pipeline for differential protein expression analysis and functional enrichment. Processes protein expression matrices, performs statistical testing (t-test), identifies differentially expressed proteins, and conducts GO/KEGG enrichment analysis with publication-ready visualizations.

## When to Use
- Analyzing proteomics experimental data with control vs treatment groups
- Identifying significantly differentially expressed proteins
- Performing functional enrichment analysis (GO terms, KEGG pathways)
- Creating publication-ready bubble plots and bar charts
- Handling mixed protein ID formats (UniProt IDs, gene symbols)
- Processing multi-omics data requiring pathway analysis

## Inputs
- **protein_expression.csv**: Expression matrix with proteins as rows, samples as columns
- **control_samples**: List of control sample column names (e.g., ['Ctrl_1', 'Ctrl_2', 'Ctrl_3'])
- **treatment_samples**: List of treatment sample column names (e.g., ['Treat_1', 'Treat_2', 'Treat_3'])
- **p_threshold**: Adjusted p-value threshold (default: 0.05)
- **fc_threshold**: Log2 fold change threshold (default: 1.0)

## Workflow
1. Load protein expression data using `scripts/main.py`
2. Perform statistical testing (t-test) with Benjamini-Hochberg correction
3. Filter significant proteins based on p-value and fold change thresholds
4. Map mixed protein IDs to UniProt IDs using batch API calls
5. Retrieve GO annotations and KEGG pathway information
6. Perform Fisher's exact test for enrichment analysis
7. Generate bubble plots and bar charts as referenced in `references/workflow.md`
8. Export results to CSV files and visualization PNG files

## Error Handling
The pipeline includes robust error handling for API timeouts and network issues. When KEGG API calls fail or timeout, the system will retry with exponential backoff and skip problematic entries. UniProt ID mapping errors are logged but don't stop the analysis. Missing data points are handled gracefully by skipping proteins with NaN values during statistical testing.

## Common Pitfalls
- Mixed protein ID formats causing mapping failures
- API rate limiting and timeout issues with KEGG/UniProt services
- Insufficient statistical power with small sample sizes
- Memory issues with large protein datasets
- Network connectivity problems during batch API calls
- See `references/pitfalls.md` for detailed troubleshooting

## Quick Reference

```bash
# Run full enrichment analysis
python scripts/main.py --input expression.csv \
    --control Ctrl_1,Ctrl_2,Ctrl_3 --treatment Treat_1,Treat_2,Treat_3 \
    --output-dir ./results/ --p-threshold 0.05 --fc-threshold 1.0
```

```python
# Core statistical testing pattern
from scipy import stats
import numpy as np

pvalues = []
for _, row in df.iterrows():
    ctrl = row[control_cols].dropna().values.astype(float)
    treat = row[treatment_cols].dropna().values.astype(float)
    _, p = stats.ttest_ind(ctrl, treat, equal_var=False)
    pvalues.append(p)
# Benjamini-Hochberg correction
from scipy.stats import false_discovery_control
adjusted = false_discovery_control(pvalues, method='bh')
```

## Output Format
- **differential_expression_results.csv**: Statistical results with p-values, fold changes
- **go_enrichment_results.csv**: GO term enrichment with adjusted p-values
- **kegg_enrichment_results.csv**: KEGG pathway enrichment results
- **go_bubble_plot.png**: GO enrichment bubble plot visualization
- **kegg_bar_plot.png**: KEGG pathway bar chart visualization
