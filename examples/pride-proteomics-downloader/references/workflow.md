# PRIDE Proteomics Downloader Workflow

## Step 1: Project Search
- Use PRIDE REST API endpoint: `https://www.ebi.ac.uk/pride/ws/archive/project/list`
- Search projects with pagination support
- Parameters: pageSize, page, order, sort

## Step 2: Project Filtering  
- Get detailed project info: `https://www.ebi.ac.uk/pride/ws/archive/project/{accession}`
- Check for publications (publicationDate or references fields)
- Check dataProcessingProtocol field for "fragpipe" (case insensitive)

## Step 3: File Discovery
- Get project files: `https://www.ebi.ac.uk/pride/ws/archive/file/list/{accession}`
- Filter for raw data files (.raw, .mzML, .mzml extensions)
- Extract download URLs from file metadata

## Step 4: Publication Download
- Extract PubMed IDs from project references
- Use PMC API to convert PubMed ID to PMC ID
- Download PDFs from PMC: `https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/`

## Step 5: Data Download
- Download raw files using proper HTTP headers
- Handle 403 Forbidden errors gracefully
- Implement retry logic and rate limiting
- Save files in organized directory structure

## Step 6: Results Summary
- Generate CSV summary of all processed projects
- Include metadata: accession, title, publication info, protocol details
