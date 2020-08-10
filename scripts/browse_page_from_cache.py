"""

This script can be used to view cached pages.

Use from the scripts directory as follows:
python browse_page_from_cache.py
Enter URL: <chosen url here>

If the entry is not present within the cache, it will be added.

"""

from browser import Browser
import argparse
from combined_interface import StandardMetadataCache
from caches import MHTMLCache

def browse_page_from_cache(url):
    browser = Browser()
    returned = StandardMetadataCache.get(url)
    print(returned)
    MHTMLCache.load()
    browser.get_local(MHTMLCache.get(url))
    return browser

if __name__ == "__main__":
    url = input("Enter URL: ")
    while True:
        browser = browse_page_from_cache(url)
        url = input("Enter URL: ")
        browser.close()
