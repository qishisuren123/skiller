---
name: pride-proteomics-downloader
description: "从PRIDE数据库(https://www.ebi.ac.uk/pride/)下载符合条件的蛋白质组学项目数据。筛选条件：项目已有发表论文(Publication字段)，Data Processing Protocol包含Fragpipe。需要使用PRIDE REST API搜索项目、获取项目详情、筛选符合条件的项目，下载项目中的原始数据文件(.raw/.mzML)，并下载关联的论文PDF。"
license: MIT
compatibility: "Python >=3.9; requests, pandas, tqdm, pathlib"
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---

# Pride Proteomics Downloader

## Overview
Downloads proteomics project data from PRIDE database (https://www.ebi.ac.uk/pride/) with specific filtering criteria. Searches for projects that have publications and use FragPipe in their data processing protocol, then downloads raw data files (.raw/.mzML) and associated publication PDFs.

## When to Use
Use this skill when you need to systematically collect FragPipe-processed proteomics datasets from PRIDE database for research analysis, method comparison, or literature review purposes.

## Inputs
- `--page-size`: Number of projects to fetch per page (default: 50)
- `--max-pages`: Maximum number of pages to search (default: 5)  
- `--download-dir`: Directory to save downloaded files (default: "downloads")
- `--skip-raw-files`: Skip downloading raw data files, only get publications
- `--debug`: Enable debug output for troubleshooting

## Workflow
1. Execute `scripts/main.py` with desired parameters
2. Script searches PRIDE projects using REST API from `references/workflow.md`
3. Filters projects with publications and FragPipe in data processing protocol
4. Downloads raw data files (.raw/.mzML) when accessible
5. Downloads publication PDFs using PubMed/PMC APIs
6. Saves project metadata and download status to CSV file

## Error Handling
The script includes comprehensive error handling for common issues:
- API endpoint errors are handled with fallback URL construction
- 403 Forbidden errors for restricted files are caught and logged
- Network timeouts are handled with retry logic
- Missing publication data is handled gracefully
- Invalid PubMed IDs are handled without stopping execution

## Common Pitfalls
See `references/pitfalls.md` for detailed error scenarios and fixes discovered during development, including API endpoint corrections and authentication issues.

## Quick Reference

```bash
# Search and download FragPipe projects with publications
python scripts/main.py --download-dir ./pride_data/ --max-pages 10

# Download only publications (skip raw files)
python scripts/main.py --download-dir ./pride_data/ --skip-raw-files --debug
```

```python
# Core PRIDE API search pattern
import requests

def search_pride(page_size=50, page=0):
    url = "https://www.ebi.ac.uk/pride/ws/archive/v2/search/projects"
    params = {"keyword": "fragpipe", "pageSize": page_size, "page": page}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("_embedded", {}).get("compactprojects", [])
```

## Output Format
- `downloads/{project_accession}/`: Directory per project containing raw files
- `downloads/{project_accession}/publications/`: PDF files of associated papers  
- `downloads/project_summary.csv`: Metadata of all processed projects
- Console output showing download progress and status for each file
