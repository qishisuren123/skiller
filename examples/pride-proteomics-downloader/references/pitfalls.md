# Common Pitfalls and Solutions

## API Endpoint Errors

### Error: 404 Not Found for project list
**Root Cause**: Used incorrect API endpoint `/pride/ws/archive/v2/projects`
**Fix**: Changed to correct endpoint `/pride/ws/archive/project/list`

### Error: 404 Not Found for file list  
**Root Cause**: Used incorrect endpoint `/pride/ws/archive/file/list/project/{accession}`
**Fix**: Changed to `/pride/ws/archive/file/list/{accession}`

## Data Structure Issues

### Error: No projects found in filtering
**Root Cause**: Assumed wrong response structure, looked for `_embedded.projects` 
**Fix**: Projects are in `list` field of response

### Error: File download URLs not found
**Root Cause**: Assumed `downloadUrl` field name
**Fix**: Actual field is `downloadLink`, added fallback URL construction

## Authentication and Access Issues

### Error: 403 Forbidden on file downloads
**Root Cause**: Missing proper HTTP headers and some files require authentication
**Fix**: Added browser-like headers and graceful handling of restricted files

### Error: PMC PDF download failures
**Root Cause**: Not all PubMed articles have free PDFs available
**Fix**: Added error handling and fallback messaging for inaccessible papers

## Rate Limiting Issues

### Error: Too many requests errors
**Root Cause**: Making rapid API calls without delays
**Fix**: Added sleep delays between API calls (0.5s for metadata, 2s for downloads)
