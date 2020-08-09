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
    #parser = argparse.ArgumentParser()
    #parser.add_argument("url", default="")
    #args = parser.parse_args()
    #url = args.url
    #if url == "":
        url = input("Enter URL:")
        while True:
            browser = browse_page_from_cache(url)
            url = input("Enter URL:")
            browser.close()
    #else:
    #    browser = browse_page_from_cache(url)
    #    input()
    #    browser.close()
