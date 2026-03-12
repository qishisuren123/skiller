#!/usr/bin/env python3
"""
PRIDE Proteomics Downloader
Downloads FragPipe-processed proteomics projects from PRIDE database
"""

import requests
import pandas as pd
import json
from pathlib import Path
import time
import os
import argparse
import logging
from urllib.parse import urlparse, urljoin
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def search_pride_projects(query_terms=None, page_size=100, page=0):
    """Search PRIDE projects using REST API"""
    base_url = "https://www.ebi.ac.uk/pride/ws/archive/v2/search/projects"

    params = {
        'pageSize': page_size,
        'page': page,
        'sortDirection': 'DESC',
        'sortFields': 'submission_date'
    }
    
    if query_terms:
        params['keyword'] = query_terms

    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    # v2 API 直接返回项目列表
    if isinstance(data, list):
        projects = data
    else:
        projects = data.get('_embedded', {}).get('compactprojects', data.get('list', []))
    return {'list': projects}

def get_project_details(project_accession):
    """Get detailed information for a specific project"""
    url = f"https://www.ebi.ac.uk/pride/ws/archive/v2/projects/{project_accession}"
    
    response = requests.get(url)
    response.raise_for_status()
    
    return response.json()

def get_project_files(project_accession):
    """Get list of files for a specific project"""
    url = f"https://www.ebi.ac.uk/pride/ws/archive/v2/files/byProject?accession={project_accession}"
    
    response = requests.get(url)
    response.raise_for_status()
    
    return response.json()

def get_pubmed_pdf_url(pubmed_id):
    """Try to get PDF URL from PubMed ID via PMC"""
    try:
        pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pubmed_id}&format=json"
        response = requests.get(pmc_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        records = data.get('records', [])
        
        if records and 'pmcid' in records[0]:
            pmc_id = records[0]['pmcid']
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
            return pdf_url
        
    except Exception as e:
        logger.error(f"Error getting PMC PDF for PubMed ID {pubmed_id}: {e}")
    
    return None

def download_file(file_url, local_path, chunk_size=8192):
    """Download a file from URL to local path with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    response = requests.get(file_url, stream=True, headers=headers, timeout=30)
    response.raise_for_status()
    
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    progress = (downloaded / total_size) * 100
                    print(f"\r    Downloading {local_path.name}: {progress:.1f}%", end="")
    
    print(f"\r    ✓ Downloaded {local_path.name} ({downloaded} bytes)")

def download_publications(project_info, download_dir="downloads"):
    """Download publication PDFs for a project"""
    project_accession = project_info['accession']
    references = project_info.get('references', [])
    
    if not references:
        logger.info(f"  No references found for {project_accession}")
        return
    
    pub_dir = Path(download_dir) / project_accession / "publications"
    pub_dir.mkdir(parents=True, exist_ok=True)
    
    for i, ref in enumerate(references):
        pubmed_id = ref.get('pubmedId')
        if pubmed_id:
            logger.info(f"  Downloading publication {pubmed_id}...")
            pdf_url = get_pubmed_pdf_url(pubmed_id)
            
            if pdf_url:
                pdf_filename = f"pubmed_{pubmed_id}.pdf"
                pdf_path = pub_dir / pdf_filename
                
                if pdf_path.exists():
                    logger.info(f"    Skipping {pdf_filename} (already exists)")
                    continue
                
                try:
                    download_file(pdf_url, pdf_path)
                except Exception as e:
                    logger.error(f"    Failed to download {pdf_filename}: {e}")
            else:
                logger.warning(f"    No PDF URL found for PubMed ID {pubmed_id}")
        
        time.sleep(1)

def download_raw_files(project_accession, download_dir="downloads"):
    """Download raw data files (.raw, .mzML) for a project"""
    logger.info(f"Getting file list for {project_accession}...")
    
    try:
        files_data = get_project_files(project_accession)
        files = files_data.get('list', [])
        logger.info(f"Found {len(files)} total files")
        
        raw_extensions = ['.raw', '.mzml', '.mzML']
        raw_files = []
        
        for file_info in files:
            file_name = file_info.get('fileName', '')
            if any(file_name.lower().endswith(ext.lower()) for ext in raw_extensions):
                raw_files.append(file_info)
        
        logger.info(f"Found {len(raw_files)} raw data files")
        
        if not raw_files:
            logger.info("No raw data files found")
            return
        
        project_dir = Path(download_dir) / project_accession
        project_dir.mkdir(parents=True, exist_ok=True)
        
        for file_info in raw_files:
            file_name = file_info.get('fileName', '')
            download_link = file_info.get('downloadLink', '')
            
            if download_link.startswith('/'):
                download_url = f"https://www.ebi.ac.uk{download_link}"
            elif not download_link.startswith('http'):
                download_url = f"https://www.ebi.ac.uk/pride/data/archive/{project_accession}/{file_name}"
            else:
                download_url = download_link
            
            local_path = project_dir / file_name
            
            if local_path.exists():
                logger.info(f"  Skipping {file_name} (already exists)")
                continue
            
            logger.info(f"  Downloading {file_name}...")
            
            try:
                download_file(download_url, local_path)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    logger.warning(f"  Access denied for {file_name}. File may require special permissions.")
                else:
                    logger.error(f"  Failed to download {file_name}: {e}")
            except Exception as e:
                logger.error(f"  Error downloading {file_name}: {e}")
            
            time.sleep(2)
            
    except Exception as e:
        logger.error(f"Error downloading files for {project_accession}: {e}")

def filter_projects_with_fragpipe_and_publications(projects_data):
    """Filter projects that have publications and use Fragpipe"""
    filtered_projects = []
    
    projects = projects_data.get('list', [])
    
    for project in projects:
        has_publication = (project.get('publicationDate') is not None or 
                          len(project.get('references', [])) > 0)
        
        if not has_publication:
            continue
            
        try:
            details = get_project_details(project['accession'])
            protocols = details.get('dataProcessingProtocol', '')
            
            if 'fragpipe' in protocols.lower():
                filtered_projects.append({
                    'accession': project['accession'],
                    'title': project['title'],
                    'publicationDate': project.get('publicationDate'),
                    'references': project.get('references'),
                    'dataProcessingProtocol': protocols
                })
                
        except Exception as e:
            logger.error(f"Error processing {project['accession']}: {e}")
            continue
            
        time.sleep(0.5)
    
    return filtered_projects

def main():
    parser = argparse.ArgumentParser(description='Download FragPipe proteomics projects from PRIDE database')
    parser.add_argument('--page-size', type=int, default=50, help='Number of projects per page')
    parser.add_argument('--max-pages', type=int, default=5, help='Maximum pages to search')
    parser.add_argument('--download-dir', default='downloads', help='Download directory')
    parser.add_argument('--skip-raw-files', action='store_true', help='Skip downloading raw data files')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Searching PRIDE projects...")
    
    all_filtered = []
    
    for page in range(args.max_pages):
        logger.info(f"Processing page {page + 1}/{args.max_pages}")
        results = search_pride_projects(page_size=args.page_size, page=page)
        
        filtered = filter_projects_with_fragpipe_and_publications(results)
        all_filtered.extend(filtered)
        
        if len(results.get('list', [])) < args.page_size:
            break
    
    logger.info(f"Found {len(all_filtered)} projects with FragPipe and publications")
    
    # Save project summary
    if all_filtered:
        df = pd.DataFrame(all_filtered)
        summary_path = Path(args.download_dir) / "project_summary.csv"
        df.to_csv(summary_path, index=False)
        logger.info(f"Saved project summary to {summary_path}")
    
    # Download files for each project
    for project in all_filtered:
        logger.info(f"{'='*60}")
        logger.info(f"Processing project: {project['accession']}")
        logger.info(f"Title: {project['title']}")
        
        # Download publications
        download_publications(project, args.download_dir)
        
        # Download raw files if not skipped
        if not args.skip_raw_files:
            download_raw_files(project['accession'], args.download_dir)
    
    logger.info("Download process completed!")

if __name__ == "__main__":
    main()
