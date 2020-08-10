"""

This script is for exporting metadata from a given URL to JSON. The exported content is written to stdout.

Example usage:
python access_metadata_json.py <your chosen url>

If the URL is not present in the cache, it will be added.

"""

import argparse
from caches import *
from combined_interface import StandardMetadataCache, EuroradMetadataCache, RadiopaediaMetadataCache

StandardMetadataCache.load()
EuroradMetadataCache.load()
RadiopaediaMetadataCache.load()
MHTMLCache.load()
SimpleMHTMLCache.load()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    metadata = StandardMetadataCache.get(args.url)
    print(metadata)
