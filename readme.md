# Automated URL Indexation & Verification Script

This Python script automates the process of checking whether URLs from a specified sitemap are indexed on Google Search and, if not, requesting their indexing via the Google Indexing API. The script also maintains a local record of “processed” URLs to avoid repeated checks, thereby making the process efficient and less error-prone.

---

## Overview
- **Script Name**: `indexation_script.py`
- **Purpose**: 
  - Fetch all URLs from an XML sitemap.
  - Check each URL’s indexation status through the Google Search Console URL Inspection API.
  - If not indexed, request indexing via the Google Indexing API.
  - Keep track of processed URLs in a local file to avoid reprocessing in subsequent runs.

---

## Key Features
1. **Automated Sitemap Parsing**  
   Pulls URLs directly from an XML sitemap, ensuring you always work with the latest set of pages.

2. **Google Search Console Integration**  
   Leverages the URL Inspection API to determine whether a page is already in Google’s index.

3. **Indexing API Requests**  
   Automates the submission of non-indexed pages to the Indexing API, helping Google discover or refresh your site’s content faster.

4. **Processed URLs Tracking**  
   Saves each processed URL to a local file (`processed_urls.txt`), preventing duplicate requests and optimizing efficiency.

---

## Prerequisites
1. **Programming Environment**  
   - Python 3.x installed.

2. **Python Libraries**  
   - [requests](https://pypi.org/project/requests/)
   - [google-api-python-client](https://pypi.org/project/google-api-python-client/)
   - [google-auth](https://pypi.org/project/google-auth/)
   
   *Example installation command:*
   ```bash
   pip install requests google-api-python-client google-auth
