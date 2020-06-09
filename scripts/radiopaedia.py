"""

Scrape radiographs from Radiopaedia, together with related metadata.

The scraper uses Selenium to enter terms on Radiopaedia's site search and
click through the results. It downloads the highest-resolution versions of
images available and places them in the same directory, under the same filename
they have on Radiopaedia (with the possible addition of -1, -2 etc. if multiple
images have the same name).

It also extracts metadata from these pages and saves them to a csv file compatible
with metadata.csv. Internally, it starts by converting this metadata to an
interoperable format that is easy to work with (referred to as "standard"), so
if you wish you can write a function to convert the metadata to an output format
suitable for your own applications.

There is also a scraper for Eurorad (see eurorad.py).

Usage:

First download the correct chromedriver for your operating system from here:
https://sites.google.com/a/chromium.org/chromedriver/

Make sure it is for the same version as your Chrome installation.

Extract it and put it in the parent directory of this file.

Then, run from the console as radiopaedia.py, ideally in the same directory.

Tested with Chrome 80.0.3987.87

"""

import os
import pickle
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from subprocess import check_output, run
from urllib.parse import urljoin, urlparse
from scipy.stats import truncnorm
import pandas as pd
import numpy as np
import sys
import time
import base64
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from urllib.request import urlretrieve
from copy import deepcopy
import pdb
import argparse
from PIL import Image
import urllib.request
import matplotlib.pyplot as plt


from urllib3.exceptions import ProtocolError
from urllib.request import urlopen
import json

max_results = 100

global_speedup = .25

def show(thing):
    print(thing)
    return thing

def filename_from_url(url):
    "Determine the filename that the given url should be downloaded to."
    return os.path.basename(urlparse(url).path)


def deduplicate_filename(retrieve_filename, img_dir):
    files = os.listdir(img_dir)
    test_filename = retrieve_filename
    name, ext = os.path.splitext(retrieve_filename)
    i = 1
    while test_filename in files:
        test_filename = name + "-" + str(i) + ext
        i += 1
    return test_filename

def wait(n):
    """Wait a random period of time"""
    time.sleep(truncnorm.rvs(0, n*2, loc=n, scale=n/4) / global_speedup)

browser_downloads = os.path.join(os.path.dirname(__file__),"downloads")

options = webdriver.ChromeOptions()
options.gpu = False
options.headless = False
options.add_experimental_option("prefs", {
    "download.default_directory" : ".",
    '.default_content_setting_values.automatic_downloads': 2,
    "browser.helperApps.neverAsk.saveToDisk": "image/jpeg"
})


chrome_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),"../chromedriver")
print(chrome_path)
chromedriver_path = chrome_path

def get_browser():
    "Return an instance of a Selenium browser."

    options = webdriver.ChromeOptions()
    options.gpu = False
    options.headless = False

    desired = options.to_capabilities()
    desired['loggingPrefs'] = { 'performance': 'ALL'}
    browser = webdriver.Chrome(desired_capabilities=desired,
                               executable_path=chromedriver_path)
    return browser

desired = options.to_capabilities()
desired['loggingPrefs'] = { 'performance': 'ALL'}
browser = webdriver.Chrome(desired_capabilities=desired,
                           executable_path=chrome_path)

def safe_get(url):
    wait()
    try:
        browser.get(url)
    except ProtocolError:
        assert browser.current_url == url

def find_new_entries(old_data, new_cases):
    "Iterate through the URLs in new_cases and return metadata from the ones that are not already in old_data."
    new_data = []
    for new_case in new_cases:
        if not new_case._in(old_data):
            data = new_case.get_data()
            new_data.append(data)
            yield data


def format_radiopaedia_search_url(search_terms, scope):
    base_url = "https://radiopaedia.org/search?utf8=%E2%9C%93&q={}&scope={}&lang=us"
    return base_url.format("+".join(search_terms), scope)

def format_search_url(search_terms):
    return format_radiopaedia_search_url(search_terms, "cases")

def extract_results_from_search_page(browser):
    out = []
    #Yield from playlists
    #Yield cases
    for a in browser.find_elements_by_xpath("//a[contains(@href,'/cases/') and @class = 'search-result search-result-case']"):
        out.append(a.get_attribute("href"))
    return list(set(out))

def get_next_search_page(browser):
    try:
        next_ref = browser.find_element_by_xpath(
            "//a[@class='next_page']"
        )
        return next_ref.get_attribute("href")
    except:
        return None

def get_search_results(search_terms):
    next_search_page = format_search_url(search_terms)
    while next_search_page:
        browser.get(next_search_page)
        wait()
        yield from extract_results_from_search_page()
        next_search_page = get_next_search_page()
        print("Proceed to next?", next_search_page)
        #if input() == "n":
        #    break

search_terms = ["COVID"]

def metadata_from_search_terms(search_terms):
    result_pages = get_search_results(search_terms)
    print(result_pages)
    for result_page in result_pages:
        result_browser = get_browser()
        result_browser.get(result_page)
        wait()
        yield metadata_from_result_page(result_browser)
        result_browser.close()

temp_folder = os.path.join(
    os.path.dirname(__file__),
    "radio_tmp"
)

def get_temp_filename(folder):
    #Not thread-safe
    ls = os.listdir(folder)
    i = 0
    while True:
        name = str(i)
        if not name in ls:
            return name
        i += 1

def metadata_from_result_page(browser, image_folder):
    characteristics = [i.text for i in browser.find_elements_by_xpath("//div[@class='data-item']")]
    characteristic_dict = {}
    for characteristic in characteristics:
        name, value = characteristic.split(": ")
        characteristic_dict[name] = value

    presentation = browser.find_element_by_xpath("//div[@class='case-section view-section']").text

    image_text = [study_finding.text for study_finding in browser.find_elements_by_xpath("//div[@class='sub-section study-findings body']")]

    title = browser.find_element_by_xpath("//h1[@class='header-title']").text

    images = get_image_urls_from_current_page(browser, image_folder)

    data = {"images":images,
            "image_descriptions":image_text,
            "clinical_history":presentation,
            "demographic_information":characteristic_dict,
            "title":title,
            "url":browser.current_url
    }
    return data

def convert_view(view):
    return {"Frontal":"PA"}.get(view, view)

def radiopaedia_to_standard(radiopaedia_record):
    standard_patient = {
        "sex":radiopaedia_record["demographic_information"]["GENDER"],
        "age":radiopaedia_record["demographic_information"]["AGE"],
        "clinical_history":radiopaedia_record["clinical_history"],
        "finding":radiopaedia_record["title"],
    }
    standard_document = {
        "doi":None,
        "url":radiopaedia_record["url"],
        "license":"CC BY-NC-SA"
    }
    images = []
    image_sets = radiopaedia_record["images"]
    print(image_sets)
    for image_set in image_sets:
        images.extend(image_set)
    descriptions = radiopaedia_record["image_descriptions"]
    standard_images = []
    for viewer, description in zip(image_sets, descriptions):
        for figure_group in viewer:
            image_extracted = [img["fullscreen_filename"] for img in figure_group["images"]], #wrong
            if figure_group["modality"] == "X-ray":
                #It would only make sense for this to fire once. But just in case
                #for image in figure_group["images"]:
                for image in figure_group["images"]:
                    standard_images.append(show({
                        "url":[image["fullscreen_filename"]],
                        "image_description":description,
                        "modality":figure_group["modality"],
                        "view":convert_view(image["plane_projection"])
                    }))
            else:
                pass
    data = {
        "patient":standard_patient,
        "images":standard_images,
        "document":standard_document
    }
    return data

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
            results = list(extract_results_from_search_page(browser))
        for result in results:
            try:
                yield RadiopaediaCase(result)
            except:
                pass
            n_results += 1
            if n_results >= max_results:
                break
        next_search_page = get_next_search_page(browser)

def url_no_query(url_string):
    parsed = urlparse(url_string)
    return parsed.netloc + parsed.path

class RadiopaediaCase():
    "An object representing a Radiopaedia case."
    def __init__(self, url):
        self.url = url
        self.data = None
    def _in(self, metadata):
        source = url_no_query(self.url)
        all_sources = list(metadata["url"].map(url_no_query))
        return source in all_sources
    def extract_data(self):
        browser = get_browser()
        browser.get(self.url)
        data = metadata_from_result_page(browser, temp_folder)
        browser.close()
        return data
    def get_data(self):
        if self.data is None:
            self.data = self.extract_data()
        return self.data

def get_image_urls_from_current_page(browser, image_folder):

    case_name = filename_from_url(browser.current_url)

    study_ids = [element.get_attribute("data-study-id") for element in browser.find_elements_by_xpath("//div[@data-study-id]")]
    json_objs = []
    for study_id in study_ids:
        print(study_id)
        stacks_url = "https://radiopaedia.org/studies/{}/stacks?lang=us".format(study_id)
        stacks_browser = get_browser()
        stacks_browser.get(stacks_url)
        json_text = stacks_browser.find_element_by_xpath("/*").text
        json_obj = json.loads(json_text)
        json_objs.append(json_obj)
        stacks_browser.close()
        wait(4)

    viewers = []
    for viewer, study_id in zip(json_objs, study_ids):
        slides = []
        for index, slide in enumerate(viewer):
            #for slice_ in slide["images"]:
            #    temp_filename = get_temp_filename(image_folder)
            #    wget(slice_["fullscreen_filename"],
            #         os.path.join(image_folder,
            #                      temp_filename)
            #         )
            #    wait(.1)
            #    slice_["disk_filename"] = temp_filename
            if slide["modality"] == "X-ray":
                slides.append(slide)
                #slides.append(CXR(data=slide))
            elif slide["modality"] == "CT":
                pass
                #slides.append(CT(case=case_name,
                #                 stackid=study_id,
                #                 index=index,
                #                 data=slide))
        viewers.append(slides)

    return viewers

def wget(src, filename):
    if run(["wget", src, "-O", filename]).returncode != 0:
        raise ValueError

def standard_to_metadata_format(standard_record, filenames):
    "Convert data in an interoperable format to the format in metadata.csv"
    all_rows = []
    images = standard_record["images"]
    standard_patient = standard_record["patient"]
    for image, filename in zip(images, filenames):
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
            folder = "Not sure what to do with this"
        patient_row["modality"] = modality
        patient_row["folder"] = folder
        patient_row["filename"] = filename
        all_rows.append(patient_row)
    return all_rows

def output_candidate_entries(standard, columns, out_name, img_dir):
    "Save the candidate entries to a file."
    pickle_name = out_name + "_pickled_data"
    out_df = pd.DataFrame(columns=columns)
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    all_records = []
    for record in standard:
        try:
            all_records.append(record)
            record = radiopaedia_to_standard(record)
            with open(pickle_name, "wb") as handle:
                pickle.dump(all_records, handle)
            patient = clean_standard_data(record)
            all_filenames = []
            for media in patient["images"]:
                media_url = media["url"][0]
                filename = deduplicate_filename(
                    filename_from_url(
                        media_url,
                    ),
                    img_dir
                )
                new_path = os.path.join(
                    img_dir,
                    filename,
                )
                wget(media_url, new_path)
                all_filenames.append(filename)
            out_df = out_df.append(
                standard_to_metadata_format(
                    patient,
                    all_filenames
                ),
                ignore_index=True
            )
            out_df.to_csv(out_name)
        except Exception as e:
            print("Exception: ", e)

def output_candidate_entries(standard, columns, out_name, img_dir):
    "Save the candidate entries to a file."
    pickle_name = out_name + "_pickled_data"
    out_df = pd.DataFrame(columns=columns)
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    all_records = []
    for record in standard:
        all_records.append(record)
        record = radiopaedia_to_standard(record)
        with open(pickle_name, "wb") as handle:
            pickle.dump(all_records, handle)
        patient = clean_standard_data(record)
        all_filenames = []
        for image in patient["images"]:
            for url in image["url"]:
                retrieve_filename = deduplicate_filename(
                    filename_from_url(url),
                    img_dir
                )
                try:
                    wget(
                        url,
                        os.path.join(
                            img_dir,
                            retrieve_filename
                        )
                    )
                except ValueError:
                    print("failed")
                else:
                    all_filenames.append(retrieve_filename)
                    break
            else:
                all_filenames.append("")
        out_df = out_df.append(
            standard_to_metadata_format(
                patient,
                all_filenames
            ),
            ignore_index=True
        )
        out_df.to_csv(out_name)

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

    try:

        if os.path.exists(args.newimg):
            raise ValueError("Image folder already contains images.")

        #Read in current metadata
        old_data = pd.read_table(args.csv, sep=",")

        #Build a generator of new case URLs
        new_cases = get_search_results(args.search.split(" "),
                                       browser)

        #Record metadata from the cases not already recorded
        found = find_new_entries(old_data, new_cases)

        #Save new data to disk for examination.
        output_candidate_entries(
            found,
            old_data.columns,
            args.newcsv,
            args.newimg
        )

        browser.close()

    except:
        browser.close()
        raise
