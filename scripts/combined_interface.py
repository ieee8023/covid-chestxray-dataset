"""
Scrape radiographs, together with related metadata.

The scraper uses Selenium to enter terms on Eurorad and Radiopaedia's site search and
click through the results. It downloads the highest-resolution versions of
images available and places them in the same directory, under the same filename
they have on the source website (with the possible addition of -1, -2 etc. if multiple
images have the same name).

It also extracts metadata from these pages and saves them to a csv file compatible
with metadata.csv. Internally, it starts by converting this metadata to an
interoperable format that is easy to work with (referred to as "standard"), so
if you wish you can write a function to convert the metadata to an output format
suitable for your own applications.

Usage:

First download the correct chromedriver for your operating system from here:
https://sites.google.com/a/chromium.org/chromedriver/

Make sure it is for the same version as your Chrome installation.

Extract it and put it in the parent directory of this file.

Then, run from the console as combined_interface.py, ideally in the same directory.

Usage example:

python combined_interface.py "search terms" image_output_folder/ new_metadata_filename.csv old_metadata_filename.csv' internal retry

The second-to-last argument, which describes the search method, can be either "internal" or "bing". If you are using "bing", you should create a file called "subscription_key.txt" in the same directory as this code, with the key on the first line.

The final argument indicates whether to retry 

Portability:

This code requires wget to be in $PATH, so it will require extra configuration to run on Windows.

Tested with Chrome 80.0.3987.87.

"""

import os
import shutil
import glob
import base64
import json
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from urllib.request import urlretrieve
from copy import deepcopy
from urllib.parse import urlparse
from urllib.error import HTTPError
from scipy.stats import truncnorm
from subprocess import run
from functools import wraps
import sys
import tempfile
import email
import re
import tqdm
import time
import logging
import pdb
import pandas as pd
import pickle
import numpy as np
import argparse
from PIL import Image
import urllib.request
import argparse

from utils import filename_from_url, find_new_entries, deduplicate_filename, output_candidate_entries
from browser import Browser
from caches import *

from azure.cognitiveservices.search.websearch import WebSearchClient
from azure.cognitiveservices.search.websearch.models import SafeSearch
from msrest.authentication import CognitiveServicesCredentials

chromedriver_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../chromedriver"
    )
)

#Replace with your subscription key.
subscription_key_path=os.path.join(
    os.path.dirname(__file__),
    "subscription_key.txt"
)
subscription_key = None
if os.path.exists(subscription_key_path):
    with open("subscription_key.txt") as handle:
        subscription_key = next(handle).strip()
        print("Using subscription key", subscription_key)

    endpoint="https://api.cognitive.microsoft.com" #/bing/v7.0/search/"

    #Instantiate the client and replace with your endpoint.
    client = WebSearchClient(
        endpoint=endpoint,
        credentials=CognitiveServicesCredentials(subscription_key)
    )


def wget(src, filename):
    "Call wget from the command line"
    if run(["wget", src, "-O", filename]).returncode != 0:
        raise ValueError("Failed to download", src, "to", filename)

class MetadataCache(Cache):
    """
    Base class for metadata caches.
    Opens a browser and calls a method (metadata_from_result_page) to extract data from it.
    Inheriting classes must implement metadata_from_results_page.
    """
    @classmethod
    def source(cls, url):
        print("Getting metadata from source")
        print(url)
        browser = Browser()
        browser.get(url)
        metadata = cls.metadata_from_result_page(browser)
        MHTMLCache.add_from_browser(url, browser)
        browser.close()
        return metadata

class EuroradMetadataCache(MetadataCache):
    """
    Class for extracting metadata from Eurorad.
    """
    folder="eurorad_cache"
    @classmethod
    def metadata_from_result_page(cls, browser):
        "Return the metadata from the Eurorad case the browser is currently on."

        title = browser.find_element_by_xpath("//title").text

        #This part is fragile if the specific element does not appear
        try:
            demographics = browser.find_element_by_xpath("//p[@class='color-grey']").text
            age, sex = demographics.split(",")
        except Exception as e:
            print(e)
            demographics = ""
            age = ""
            sex = ""

        standard_keys = [
            'CLINICAL HISTORY',
            'IMAGING FINDINGS',
            'DISCUSSION',
            'FINAL DIAGNOSIS'
        ]

        #Must visit element to retrieve text
        wait(10)
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        wait(5)

        image_xpath = "//div[contains(@class,'figure-gallery__item')]/*/img[@typeof='foaf:Image']"
        description_xpath = "//div[contains(@class,'figure-gallery__item')]/div[@class='figure-gallery__item__label']/span[@class='mb-1 d-block']"

        images = browser.find_elements_by_xpath(image_xpath)
        image_descriptions = browser.find_elements_by_xpath(description_xpath)

        wait(5)

        figure_label_xpath = "//li[@class='list-inline-item' and ./a[contains(@class, figure-gallery-paginator__link) and @href='#']]"
        figure_labels = browser.find_elements_by_xpath(figure_label_xpath)

        image_descriptions_text = []

        for image_description in image_descriptions:
            try:
                browser.execute_script("arguments[0].scrollIntoView()", image_description)
            except:
                pass
            image_descriptions_text.append(image_description.get_attribute("innerHTML"))

        images_src = []

        for image in images:
            browser.execute_script("arguments[0].scrollIntoView()", image)
            while image.get_attribute("src").startswith("data"):
                pass
            wait(1)
            low_res = image.get_attribute("src")
            high_res = low_res.replace("_teaser_large","")
            all_resolutions = [high_res, low_res]
            images_src.append(all_resolutions)

        out = {}
        out["images"] = images_src
        out["image_descriptions"] = image_descriptions_text
        out["url"] = browser.current_url
        out["age"] = age
        out["sex"] = sex
        out["title"] = demographics

        for subsection in browser.find_elements_by_xpath("//div[@class='row' and div/@class='col-12 col-md-3']"):
            key = subsection.find_element_by_xpath("div[@class='col-12 col-md-3']").text
            value = subsection.find_element_by_xpath("div[@class='col-12 col-md-9']").text
            if key in standard_keys:
                out[key] = value
            if key == "DIFFERENTIAL DIAGNOSIS LIST":
                out[key] = value.split("\n")
        return out

class RadiopaediaMetadataCache(MetadataCache):
    """
    Class for extracting metadata from Eurorad.
    """
    folder="radiopaedia_cache"
    @classmethod
    def metadata_from_result_page(cls, browser):
        "Return metadata from the Radiopaedia result page"
        def get_other_notes(browser):
            element = browser.find_element_by_xpath("//div[@class='js-tooltip icon download']")
            browser.execute_script("arguments[0].click()",element)
            time.sleep(5)
            other_notes = browser.find_element_by_xpath("//textarea[@class='select-all-js']").text
            print("Other notes:", other_notes)
            return other_notes
        def get_location(browser):
            author_link = browser.find_element_by_xpath("//div[@class='author-info']/a").get_attribute("href")
            location_browser = Browser()
            location_browser.get_local(SimpleMHTMLCache.get(author_link))
            author_location = location_browser.find_element_by_xpath("//dd[@class='institution-and-location']").text
            location_browser.close()
            print("Author location:", author_location)
            return author_location
        def get_image_urls_from_current_page(browser):
            "When on a Radiopaedia case, find and visit pages listing image URLs"
            case_name = filename_from_url(browser.current_url)

            study_ids = [element.get_attribute("data-study-id") for element in browser.find_elements_by_xpath("//div[@data-study-id]")]
            json_objs = []
            for study_id in study_ids:
                print(study_id)
                stacks_url = "https://radiopaedia.org/studies/{}/stacks?lang=us".format(study_id)
                stacks_browser = Browser()
                stacks_browser.get_local(SimpleMHTMLCache.get(stacks_url))
                json_text = stacks_browser.find_element_by_xpath("/*").text
                json_obj = json.loads(json_text)
                json_objs.append(json_obj)
                stacks_browser.close()
                wait(4)

            viewers = []
            for viewer, study_id in zip(json_objs, study_ids):
                slides = []
                for index, slide in enumerate(viewer):
                    if slide["modality"] == "X-ray":
                        slides.append(slide)
                    elif slide["modality"] == "CT":
                        pass
                viewers.append(slides)
            return viewers

        characteristics = [i.text for i in browser.find_elements_by_xpath("//div[@class='data-item']")]
        characteristic_dict = {}
        for characteristic in characteristics:
            name, value = characteristic.split(": ")
            characteristic_dict[name] = value

        presentation = try_or_nothing(
            lambda: browser.find_element_by_xpath("//div[@class='case-section view-section']").text
        )

        image_text = [study_finding.text for study_finding in browser.find_elements_by_xpath("//div[@class='sub-section study-findings body']")]

        title = browser.find_element_by_xpath("//h1[@class='header-title']").text

        images = get_image_urls_from_current_page(browser)

        location = try_or_nothing(lambda: get_location(browser))

        other_notes = try_or_nothing(lambda: get_other_notes(browser))

        data = {"images":images,
                "image_descriptions":image_text,
                "clinical_history":presentation,
                "demographic_information":characteristic_dict,
                "title":title,
                "url":browser.current_url,
                "location":location,
                "other_notes":other_notes
        }
        return data

def wait(n):
    """Wait a random period of time"""
    print("Waiting an average of", n, "seconds")
    time_to_wait = truncnorm.rvs(n/2, n*2, loc=n, scale=n/4)
    for tenth in tqdm.tqdm(range(int(time_to_wait * 10))):
        time.sleep(.1)

def or_blank(text):
    "If text is None, return an empty string"
    if text is None:
        return ""
    return text

def sanitize_radiopaedia_url(url):
    "Remove GET queries from the Radiopaedia url (e.g. '?lang=us'"
    if "?" in url:
        return url[:url.index("?")]
    return url

def search_bing(search_terms, max_results):
    "Iterate search results from given terms"
    count=8
    offset=0
    last_count = count
    while last_count == count:
        web_data = client.web.search(query=search_terms, count=count, offset=offset)
        results = web_data.as_dict()["web_pages"]["value"]
        last_count = len(results)
        offset += len(results)
        for result in results:
            yield result["url"]
        time.sleep(1)

def try_or_nothing(func):
    "Call a function and return None if it raises an error."
    try:
        return func()
    except Exception as e:
        print(type(Exception))
        print(e)

class Repository:
    "Base class for a repository of radiographs. Contains methods for searching using various backends"
    case_class = None
    cache_class = None
    @classmethod
    def sanitize_search_terms(cls, search_terms):
        "Ensure search terms are a list"
        if isinstance(search_terms, str):
            return search_terms.split(" ")
        elif isinstance(search_terms, list):
            return search_terms
        else:
            raise ValueError("Invalid search terms: " + str(search_terms))
    @classmethod
    def get(cls, item):
        return cls.case_class(item, cls.cache_class.get(item))
    @classmethod
    def search_internal(cls, search_terms, max_results):
        "Use browser to get all case URLs matching the given search terms"
        search_terms = cls.sanitize_search_terms(search_terms)
        browser = Browser()
        next_search_page = cls.format_internal_search_url(search_terms)
        out = []
        n_results = 0
        while next_search_page:
            print("using search page", next_search_page)
            browser.get(next_search_page)
            wait(10)
            results = list(cls.extract_results_from_search_page(browser))
            if cls.is_end_of_results(browser):
                print("End of results")
                break
            if not results:
                print("Please resolve the captcha.")
                input()
                results = list(cls.extract_results_from_search_page(browser))
            n_results += len(results)
            for result in results:
                yield cls.get(result)
            if n_results > max_results:
                print("Over max results")
                break
            next_search_page = cls.get_next_search_page(browser)
    @classmethod
    def search_bing(cls, search_terms, max_results):
        "Use Bing to search the site"
        search_terms = cls.sanitize_search_terms(search_terms)
        for url in search_bing(" ".join(search_terms) + " " + cls.external_search_limiter, max_results):
            yield cls.case_class(url)
    @classmethod
    def search_all(cls):
        "Dump all cached entries"
        return (cls.case_class(url) for url in cls.cache_class.data)

class Case():
    "Base class for cases"
    def __init__(self, url, raw_data):
        self.url = url
        self.raw_data = raw_data
        self.data = None
    def extract_data(self):
        "Retrieve data from the cache"
        return self.to_standard(self.raw_data)
    def get_data(self):
        "Return data to the user."
        if self.data is None:
            self.data = self.extract_data()
        return self.data

class RadiopaediaCase(Case):
    "An object representing an Eurorad case."
    def _in(self, metadata):
        "Check whether the URL is in the provided metadata."
        metadata_sanitized_url = list(metadata["url"].map(sanitize_radiopaedia_url))
        return sanitize_radiopaedia_url(self.url) in metadata_sanitized_url
    def to_standard(self, radiopaedia_record):
        "Convert the metadata to the standard format."
        standard_patient = {
            "sex":radiopaedia_record["demographic_information"].get("GENDER", ""),
            "age":radiopaedia_record["demographic_information"].get("AGE", ""),
            "clinical_history":radiopaedia_record["clinical_history"],
            "finding":radiopaedia_record["title"],
            "misc":{
                "location":radiopaedia_record["location"],
                "other_notes":radiopaedia_record["other_notes"]
            }
        }
        standard_document = {
            "doi":None,
            "url":radiopaedia_record["url"],
            "license":"CC BY-NC-SA"
        }
        images = []
        image_sets = radiopaedia_record["images"]
        for image_set in image_sets:
            images.extend(image_set)
        descriptions = radiopaedia_record["image_descriptions"]
        standard_images = []
        for viewer, description in zip(image_sets, descriptions):
            for figure_group in viewer:
                image_extracted = [img["fullscreen_filename"] for img in figure_group["images"]], #wrong
                if figure_group["modality"] == "X-ray":
                    for image in figure_group["images"]:
                        standard_images.append({
                            "url":[image["fullscreen_filename"]],
                            "image_description":description,
                            "modality":figure_group["modality"]
                        })
                else:
                    pass
        data = {
            "patient":standard_patient,
            "images":standard_images,
            "document":standard_document
        }
        return data

class EuroRadCase(Case):
    "An object representing an Eurorad case."
    def _in(self, metadata):
        "Check whether the URL is in the metadata."
        return self.url in list(metadata["url"])
    def to_standard(self, eurorad_record):
        "Convert the Eurorad metadata to a more interoperable format."
        standard_patient = {
            "sex":eurorad_record["sex"],
            "age":eurorad_record["age"],
            "clinical_history":eurorad_record.get("CLINICAL HISTORY"),
            "finding":eurorad_record.get("FINAL DIAGNOSIS"),
            "misc":{}
        }
        standard_document = {
            "doi":None,
            "url":eurorad_record["url"],
            "license":"CC BY-NC-SA 4.0"
        }
        images = eurorad_record["images"]
        descriptions = eurorad_record["image_descriptions"]
        standard_images = []
        for image, description in zip(images, descriptions):
            standard_images.append({
                "url":image,
                "image_description":description,
                "modality":"CT" if "CT" in description else "X-ray" #currently only supports X-rays
            })
        return {
            "patient":standard_patient,
            "images":standard_images,
            "document":standard_document
        }

class Eurorad(Repository):
    "Class for interfacing programmatically with Eurorad."
    case_class = EuroRadCase
    cache_class = EuroradMetadataCache
    external_search_limiter = "site:eurorad.org/case"
    @classmethod
    def is_end_of_results(cls, browser):
        "Return whether the page of search results is the last one."
        try:
            return 'No case found' in browser.page_source
        except NoSuchElementException:
            return False
    @classmethod
    def format_internal_search_url(cls, search_terms):
        "Format a URL for searching the given terms in Eurorad."
        return "https://www.eurorad.org/advanced-search?search=" + "+".join(search_terms)
    @classmethod
    def extract_results_from_search_page(cls, browser):
        "Return all case URLs in the search page browser is currently on."
        out = []
        for a in browser.find_elements_by_xpath("//a[contains(@href,'/case/')]"):
            out.append(a.get_attribute("href"))
        return list(set(out))
    @classmethod
    def get_next_search_page(cls, browser):
        "Get a link to the search page next in sequence after the search page browser is on."
        try:
            next_ref = browser.find_element_by_xpath(
                "//div[@class='pagination']/a[@title='Go to next page']"
            )
            return next_ref.get_attribute("href")
        except:
            return None

class Radiopaedia(Repository):
    "Class for interfacing programmatically with Radiopaedia"
    case_class = RadiopaediaCase
    cache_class = RadiopaediaMetadataCache
    external_search_limiter = "site:radiopaedia.org/cases/"
    @classmethod
    def is_end_of_results(cls, browser):
        "Return whether the page of search results is the last one."
        return "No results were found with these refinement filters applied." in browser.page_source

    @classmethod
    def format_internal_search_url(cls, search_terms):
        "Format a URL for searching the given terms in Radiopaedia."
        def format_radiopaedia_search_url(search_terms, scope):
            base_url = "https://radiopaedia.org/search?utf8=%E2%9C%93&q={}&scope={}&lang=us&system=Chest"
            return base_url.format("+".join(search_terms), scope)

        def format_search_url(search_terms):
            return format_radiopaedia_search_url(search_terms, "cases")
        return format_search_url(search_terms)
    @classmethod
    def extract_results_from_search_page(cls, browser):
        "Return all case URLs in the search page browser is currently on."
        out = []
        for a in browser.find_elements_by_xpath("//a[contains(@href,'/cases/') and @class = 'search-result search-result-case']"):
            out.append(a.get_attribute("href"))
        return list(set(out))
    @classmethod
    def get_next_search_page(cls, browser):
        "Get a link to the search page next in sequence after the search page browser is on."
        try:
            next_ref = browser.find_element_by_xpath(
                "//a[@class='next_page']"
            )
            return next_ref.get_attribute("href")
        except:
            return None

class StandardMetadataCache(MetadataCache):
    "Retrieve metadata from a URL from any repository"
    folder = "standard_metadata_cache"
    repo_sources = {
        ".*eurorad.*":Eurorad,
        ".*radiopaedia.*":Radiopaedia
    }
    @classmethod
    def source(cls, url):
        "Retrieve metadata from a URL from any repository"
        for pattern, repo in cls.repo_sources.items():
            if re.match(pattern, url):
                return repo.get(url).get_data()
    def to_standard(cls, entry):
        "Entry is already in the standard format, so no change"
        return entry

class AllRadiographs(Repository):
    repositories = [Radiopaedia, Eurorad]
    @classmethod
    def search_bing(cls, search_terms, max_results):
        "Search all repositories using Bing"
        yield from cls.search_with("search_bing", search_terms, max_results)
    @classmethod
    def search_internal(cls, search_terms, max_results):
        "Search all repositories using their internal search features"
        yield from cls.search_with("search_internal", search_terms, max_results)
    @classmethod
    def search_all(cls):
        "Dump all records from all repositories."
        yield from cls.search_with("search_all")
    @classmethod
    def search_with(cls, search_function, *args, **kwargs):
        "Call the given function on each of the repositories, and iterate over the results from all sources."
        result_sources = [getattr(repository, search_function)(*args, **kwargs) for repository in cls.repositories]
        while True:
            active = 0
            for result_source in result_sources:
                try:
                    yield next(result_source)
                except StopIteration:
                    active += 1
            if active == len(result_sources): #All raised StopIteration
               break

ResourceCache.load()
MHTMLCache.load()
EuroradMetadataCache.load()
RadiopaediaMetadataCache.load()
StandardMetadataCache.load()

def run_scrapers(
        csv,
        max_results,
        results_from,
        newcsv,
        newimg,
        handle_failure):
    #Read in current metadata
    old_data = pd.read_table(csv, sep=",")

    #Build a generator of new case URLs
    if results_from == "bing":
        new_cases = AllRadiographs.search_bing(args.search, max_results)
    elif results_from == "internal":
        new_cases = AllRadiographs.search_internal(args.search, max_results)
    elif results_from == "all":
        new_cases = AllRadiographs.search_all()
    else:
        raise ValueError("Invalid source")

    #Record metadata from the cases not already recorded
    found = find_new_entries(old_data, new_cases)

    #Save new data to disk for examination.
    output_candidate_entries(
        found,
        old_data.columns,
        newcsv,
        newimg,
        ResourceCache,
        handle_failure=="retry"
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "search",
        help="The search terms used to identify images"
    )
    parser.add_argument(
        "newimg",
        help="Folder to use when storing images. Should be empty or not exist yet.",
        default="../candidate_images"
    )
    parser.add_argument(
        "newcsv",
         help="File to output candidate metadata.",
         default="../candidate_metadata.csv"
    )
    parser.add_argument(
        "csv",
        help="Location of old metadata.",
        default="../metadata.csv"
    )
    parser.add_argument(
        "max_results",
        help="Maximum number of results to retrieve.",
        default=100
    )
    parser.add_argument(
        "results_from",
        help="bing or internal search",
        default="internal"
    )
    parser.add_argument(
        "handle_failure",
        help="whether to retry inaccessible URLs",
        default="dont_retry"
    )

    args = parser.parse_args()

    run_scrapers(
        args.csv,
        int(args.max_results),
        args.results_from,
        args.newcsv,
        args.newimg,
        args.handle_failure=="retry"
    )
