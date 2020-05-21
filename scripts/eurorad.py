import os
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from urllib.request import urlretrieve
from copy import deepcopy
from urllib.parse import urlparse
from scipy.stats import truncnorm
import sys
import time
import pdb
import pandas as pd
import pickle
import numpy as np
import argparse
from PIL import Image
import urllib.request
import matplotlib.pyplot as plt
import argparse

"""

Usage:

First download the correct chromedriver for your operating system from here:
https://sites.google.com/a/chromium.org/chromedriver/

Make sure it is for the same version as your Chrome installation.

Extract it and put it in the same directory as this file.

Then, run from the console as eurorad.py, ideally in the same directory.

"""

#Maximum number of results (reduce during development)
max_results = 10000000000

chromedriver_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "chromedriver"
    )
)

def wait(n):
    """Wait a random period of time"""
    time.sleep(truncnorm.rvs(0, n*2, loc=n, scale=n/4))

def get_browser():
    "Return an instance of a Selenium browser."

    options = webdriver.ChromeOptions()
    options.gpu = False
    options.headless = False

    print(chromedriver_path)

    desired = options.to_capabilities()
    desired['loggingPrefs'] = { 'performance': 'ALL'}
    browser = webdriver.Chrome(desired_capabilities=desired,
                               executable_path=chromedriver_path)
    return browser

def format_search_url(search_terms):
    "Format a URL for searching the given terms in Eurorad."
    return "https://www.eurorad.org/advanced-search?search=" + "+".join(search_terms)

def extract_results_from_search_page(browser):
    "Return all case URLs in the search page browser is currently on."
    out = []
    for a in browser.find_elements_by_xpath("//a[contains(@href,'/case/')]"):
        out.append(a.get_attribute("href"))
    return list(set(out))

def get_next_search_page(browser):
    "Get a link to the search page next in sequence after the search page browser is on."
    try:
        next_ref = browser.find_element_by_xpath(
            "//div[@class='pagination']/a[@title='Go to next page']"
        )
        return next_ref.get_attribute("href")
    except:
        return None

def get_search_results(search_terms, browser):
    "Use browser to get all case URLs matching the given search terms"
    next_search_page = format_search_url(search_terms)
    out = []
    n_results = 0;
    while next_search_page:
        #print("using search page", next_search_page)
        browser.get(next_search_page)
        wait(10)
        results = list(extract_results_from_search_page(browser))
        if not results:
            print("Please resolve the captcha.")
            input()
            results = list(extract_results_from_search_page(browser))
        n_results += len(results)
        for result in results:
            yield EuroRadCase(result)
        if n_results > max_results:
            pass
            #print("Exiting due to overload")
            break
        next_search_page = get_next_search_page(browser)

def metadata_from_result_page(browser):
    "Return the metadata from the Eurorad case the browser is currently on."

    title = browser.find_element_by_xpath("//title").text

    demographics = browser.find_element_by_xpath("//p[@class='color-grey']").text

    age, sex = demographics.split(",")

    standard_keys = [
        'CLINICAL HISTORY',
        'IMAGING FINDINGS',
        'DISCUSSION',
        'FINAL DIAGNOSIS'
    ]

    #Must visit element to retrieve text
    wait(1)
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
        #print("printing", image_description)
        try:
            browser.execute_script("arguments[0].scrollIntoView()", image_description)
        except:
            pass
            #print("didn't work")
        image_descriptions_text.append(image_description.get_attribute("innerHTML"))

    images_src = []

    for image in images:
        browser.execute_script("arguments[0].scrollIntoView()", image)
        while image.get_attribute("src").startswith("data"):
            pass
        wait(1)
        #print("image", image.get_attribute("innerHTML"))
        images_src.append(image.get_attribute("src").replace("_teaser_large",""))

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

def eurorad_to_standard(eurorad_record):
    "Convert the Eurorad metadata to a more interoperable format."
    standard_patient = {
        "sex":eurorad_record["sex"],
        "age":eurorad_record["age"],
        "clinical_history":eurorad_record["CLINICAL HISTORY"],
        "finding":eurorad_record["FINAL DIAGNOSIS"]
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

def standard_to_metadata_format(standard_record):
    "Convert data in an interoperable format to the format in metadata.csv"
    all_rows = []
    images = standard_record["images"]
    standard_patient = standard_record["patient"]
    for image in images:
        patient_row = {}
        patient_row.update(standard_record["patient"])
        patient_row["clinical_notes"] = (
            patient_row.pop("clinical_history") + " " + image["image_description"]
        )
        patient_row.update(standard_record["document"])
        modality = image["modality"]
        if modality == "X-ray":
            folder = "images"
        elif modality == "CT":
            folder = "volumes"
        else:
            raise ValueError
        patient_row["modality"] = modality
        patient_row["folder"] = folder
        patient_row["filename"] = filename_from_url(image["url"])
        all_rows.append(patient_row)
    return all_rows

def metadata_from_search_terms(search_terms, browser):
    "Use browser to find the metadata from all search terms"
    result_pages = list(get_search_results(search_terms, browser))
    #print(result_pages)
    for result_page in result_pages:
        try:
            browser.get(result_page)
            wait()
            yield metadata_from_result_page(browser)
        except:
            print("Failed for", result_page)

class EuroRadCase():
    "An object representing an Eurorad case."
    def __init__(self, url):
        self.url = url
        self.data = None
    def _in(self, metadata):
        return self.url in list(metadata["url"])
    def extract_data(self):
        browser = get_browser()
        browser.get(self.url)
        data = metadata_from_result_page(browser)
        browser.close()
        return data
    def get_data(self):
        if self.data is None:
            self.data = self.extract_data()
        return self.data

def filename_from_url(url):
    "Determine the filename that the given url should be downloaded to."
    return os.path.basename(urlparse(url).path)

def find_new_eurorad_entries(old_data, new_cases):
    "Iterate through the URLs in new_cases and return metadata from the ones that are not already in old_data."
    new_data = []
    for new_case in new_cases:
        if not new_case._in(old_data):
            try:
                data = new_case.get_data()
                new_data.append(data)
                yield data
            except:
                print("failed")

def output_candidate_entries(standard, columns, out_name, img_dir):
    "Save the candidate entries to a file."
    pickle_name = out_name + "_pickled_data"
    out_df = pd.DataFrame(columns=columns)
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    all_records = []
    for record in standard:
        all_records.append(record)
        record = eurorad_to_standard(record)
        with open(pickle_name, "wb") as handle:
            pickle.dump(all_records, handle)
        patient = clean_standard_data(record)
        for image in patient["images"]:
            urllib.request.urlretrieve(
                image["url"],
                os.path.join(
                    img_dir,
                    filename_from_url(image["url"])
                )
            )
        out_df = out_df.append(standard_to_metadata_format(patient),
                               ignore_index=True)
        out_df.to_csv(out_name)

def append_metadata(out, *to_append):
    pd.concat(to_append).to_csv(out)

def clean_standard_data(standard_record):
    "Sanitize data already in an interoperable format."
    def sanitize_sex(sex):
        sex = sex.lower()
        if "f" in sex or "w" in sex:
            return "F"
        else:
            return "M"

    def sanitize_age(age):
        for possible_age in age.split(" "):
            try:
                return int(possible_age)
            except:
                pass
    def sanitize_finding(finding):
        if "covid19" in finding.lower().replace("-","").replace(" ",""):
            return "COVID-19"
        else:
            return finding
    sex = standard_record["patient"]["sex"]
    if not sex in ["M", "F"]:
        standard_record["patient"]["sex"] = sanitize_sex(sex)

    standard_record["patient"]["age"] = sanitize_age(
        standard_record["patient"]["age"]
    )

    standard_record["patient"]["finding"] = sanitize_finding(
        standard_record["patient"]["finding"]
    )
    return standard_record



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

    args = parser.parse_args()

    browser = get_browser()

    #Read in current metadata
    old_data = pd.read_table(args.csv, sep=",")

    #Build a generator of new case URLs
    new_cases = get_search_results(args.search.split(" "),
                                   browser)

    #Record metadata from the cases not already recorded
    found = find_new_eurorad_entries(old_data, new_cases)

    #Save new data to disk for examination.
    output_candidate_entries(
        found,
        old_data.columns,
        args.newcsv,
        args.newimg
    )
