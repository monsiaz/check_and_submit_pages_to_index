import os
import requests
import xml.etree.ElementTree as ET
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --------------------------------------------------------------------
# 1) PARAMETERS: Update paths and variables below
# --------------------------------------------------------------------
SERVICE_ACCOUNT_FILE = '/path/to/your/service_account.json'  # Replace by your service account key path
SITEMAP_URL = 'https://example.com/sitemap_document.xml'     # Replace by your sitemap
PROPERTY_URL = 'sc-domain:example.com'                       # Replace by your domain property

PROCESSED_FILE = 'processed_urls.txt'  # Local file storing processed URLs
# --------------------------------------------------------------------


def read_processed_urls(filepath: str) -> set:
    """
    Reads the file containing the list of already processed URLs
    and returns a set for quick access.
    """
    if not os.path.exists(filepath):
        return set()
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return set(lines)


def save_processed_urls(filepath: str, processed_urls: set):
    """
    Writes the set of processed URLs to a file (1 URL per line).
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        for url in processed_urls:
            f.write(url + "\n")


def get_urls_from_sitemap(sitemap_url: str) -> list:
    """
    Retrieves the list of URLs from a given XML sitemap.
    """
    print(f"Retrieving URLs from sitemap: {sitemap_url}")
    response = requests.get(sitemap_url)
    if response.status_code != 200:
        raise Exception(f"Unable to retrieve sitemap: HTTP status code {response.status_code}")

    root = ET.fromstring(response.content)
    namespace = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    urls = []

    for url_element in root.findall(f'{namespace}url'):
        loc = url_element.find(f'{namespace}loc')
        if loc is not None and loc.text:
            urls.append(loc.text.strip())

    print(f"Number of URLs found in the sitemap: {len(urls)}")
    return urls


def check_url_index_status(search_console_service, inspection_url: str, site_url: str):
    """
    Checks the indexing status of a given URL using the Search Console API (URL Inspection).
    Returns True if the URL is indexed, False otherwise.
    Returns None if an error (HttpError) occurs.
    """
    try:
        request_body = {
            "inspectionUrl": inspection_url,
            "siteUrl": site_url,
            "languageCode": "fr-FR"
        }

        request = search_console_service.urlInspection().index().inspect(body=request_body)
        response = request.execute()

        # Analyze the response for indexing status
        inspection_result = response.get('inspectionResult', {})
        index_status_result = inspection_result.get('indexStatusResult', {})
        coverage_state = index_status_result.get('coverageState', 'UNSPECIFIED')

        # coverageState can be "Indexed" (INDEXED) or something else
        if coverage_state.upper() == "INDEXED":
            return True
        else:
            return False

    except HttpError as e:
        print(f"Error checking index status for {inspection_url}: {e}")
        return None


def request_indexing(indexing_service, url: str):
    """
    Sends a request to the Indexing API to request indexing or updating of the given URL.
    May raise a HttpError (e.g., 429 for quota issues).
    """
    print(f"-> Requesting indexing for: {url}")
    body = {
        "url": url,
        "type": "URL_UPDATED"
    }
    request = indexing_service.urlNotifications().publish(body=body)
    response = request.execute()
    print(f"Indexing API response: {response}")


def main():
    # 1) Authentication via service account file
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    scoped_credentials = credentials.with_scopes([
        "https://www.googleapis.com/auth/webmasters",
        "https://www.googleapis.com/auth/indexing"
    ])

    # 2) Build the Search Console service (URL Inspection)
    search_console_service = build('searchconsole', 'v1', credentials=scoped_credentials)

    # 3) Build the Indexing API service
    indexing_service = build('indexing', 'v3', credentials=scoped_credentials)

    # 4) Retrieve all URLs from the sitemap
    urls = get_urls_from_sitemap(SITEMAP_URL)

    # 5) Read already processed URLs
    processed_urls = read_processed_urls(PROCESSED_FILE)

    # 6) Iterate over each URL; if it's not already processed, check indexing and request if needed
    for url in urls:
        # Skip if URL is already in processed_urls
        if url in processed_urls:
            continue

        # Check if indexed
        is_indexed = check_url_index_status(search_console_service, url, PROPERTY_URL)
        if is_indexed is None:
            # An error occurred during the check => add it to processed_urls anyway
            processed_urls.add(url)
            continue

        if not is_indexed:
            # Attempt to request indexing
            try:
                request_indexing(indexing_service, url)
            except HttpError as e:
                # If quota exceeded (429), stop immediately
                if e.resp.status == 429:
                    print("Quota exceeded (429). Stopping the script for later retry.")
                    break
                else:
                    print(f"Other error for {url}: {e}")
                    # Decide whether to add the URL to processed_urls
                    processed_urls.add(url)
                    continue

        # If the page is already indexed or if indexing was requested successfully,
        # add the URL to the list of processed URLs
        processed_urls.add(url)

    # 7) Save the list of processed URLs
    save_processed_urls(PROCESSED_FILE, processed_urls)


if __name__ == "__main__":
    main()
