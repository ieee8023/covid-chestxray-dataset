import os
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from copy import deepcopy
from urllib.parse import urlparse
import sys
import time
import pdb
import pandas as pd
import numpy as np
from PIL import Image
import urllib.request
import matplotlib.pyplot as plt

#Maximum number of results (reduce during development)
max_results = 10000000000

def wait():
    "Wait a period of time. TODO: Random period of time"
    time.sleep(1)

def get_browser():
    "Return an instance of a Selenium browser."
    browser_downloads = os.path.join(os.path.dirname(__file__),"downloads")

    options = webdriver.ChromeOptions()
    options.gpu = False
    options.headless = False
    options.add_experimental_option("prefs", {
        "download.default_directory" : browser_downloads,
        'profile.default_content_setting_values.automatic_downloads': 2,
    })

    chrome_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),"../chromedriver")
    print(chrome_path)

    desired = options.to_capabilities()
    desired['loggingPrefs'] = { 'performance': 'ALL'}
    browser = webdriver.Chrome(desired_capabilities=desired,
                               executable_path=chrome_path)
    return browser

browser = get_browser()

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
        print("using search page", next_search_page)
        browser.get(next_search_page)
        wait()
        results = list(extract_results_from_search_page(browser))
        n_results += len(results)
        for result in results:
            yield EuroRadCase(result)
        if n_results > max_results:
            print("Exiting due to overload")
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
    time.sleep(.25)
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(5)

    image_xpath = "//div[contains(@class,'figure-gallery__item')]/*/img[@typeof='foaf:Image']"
    description_xpath = "//div[contains(@class,'figure-gallery__item')]/div[@class='figure-gallery__item__label']/span[@class='mb-1 d-block']"

    images = browser.find_elements_by_xpath(image_xpath)
    image_descriptions = browser.find_elements_by_xpath(description_xpath)

    time.sleep(5)

    figure_label_xpath = "//li[@class='list-inline-item' and ./a[contains(@class, figure-gallery-paginator__link) and @href='#']]"
    figure_labels = browser.find_elements_by_xpath(figure_label_xpath)

    image_descriptions_text = []

    for image_description in image_descriptions:
        print("printing", image_description)
        try:
            browser.execute_script("arguments[0].scrollIntoView()", image_description)
        except:
            print("didn't work")
        image_descriptions_text.append(image_description.get_attribute("innerHTML"))

    images_src = []

    for image in images:
        browser.execute_script("arguments[0].scrollIntoView()", image)
        while image.get_attribute("src").startswith("data"):
            pass
        time.sleep(.1)
        print("image", image.get_attribute("innerHTML"))
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

def eurorad_to_standard(eurorad_data):
    "Convert the Eurorad metadata to a more interoperable format."
    standard_data = []
    for eurorad_record in eurorad_data:
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
        standard_data.append({
            "patient":standard_patient,
            "images":standard_images,
            "document":standard_document
        })
    return deepcopy(standard_data)

def standard_to_metadata_format(standard_data):
    "Convert data in an interoperable format to the format in metadata.csv"
    metadata = []
    for standard_record in standard_data:
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
            metadata.append(patient_row)
    return deepcopy(metadata)

def metadata_from_search_terms(search_terms, browser):
    "Use browser to find the metadata from all search terms"
    result_pages = list(get_search_results(search_terms, browser))
    print(result_pages)
    for result_page in result_pages:
        browser.get(result_page)
        wait()
        yield metadata_from_result_page(browser)

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
            data = new_case.get_data()
            new_data.append(data)
    return new_data

def output_candidate_entries(standard, columns, out_name, img_dir):
    "Save the candidate entries to a file."
    for record in standard:
        record["images"] = [i for i in record["images"] if i["modality"] == "X-ray"]
    out_data = pd.DataFrame(standard_to_metadata_format(standard))
    for column in columns:
        if not column in out_data:
            out_data[column] = pd.NA
    out_data = out_data[out_data["modality"] == "X-ray"]
    out_data = out_data.reindex(columns, axis=1)
    out_data.to_csv(out_name)

    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
        for patient in standard:
            for image in patient["images"]:
                print("retrieving", image)
                urllib.request.urlretrieve(
                    image["url"],
                    os.path.join(
                        img_dir,
                        filename_from_url(image["url"])
                    )
                )
                time.sleep(2)

def append_metadata(out, *to_append):
    pd.concat(to_append).to_csv(out)

def clean_standard_data(standard_data):
    "Sanitize data already in an interoperable format."
    standard_data = deepcopy(standard_data)
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
    for standard_record in standard_data:
        sex = standard_record["patient"]["sex"]
        if not sex in ["M", "F"]:
            standard_record["patient"]["sex"] = sanitize_sex(sex)

        standard_record["patient"]["age"] = sanitize_age(
            standard_record["patient"]["age"]
        )

        standard_record["patient"]["finding"] = sanitize_finding(
            standard_record["patient"]["finding"]
        )
    return standard_data



#Read in current metadata
old_data = pd.read_table("../metadata.csv",sep=",")

#Build a generator of new case URLs
new_cases = get_search_results(["COVID"],browser)

#Record metadata from the cases not already recorded
found = find_new_eurorad_entries(old_data, new_cases)

#Save new data to disk for examination.
output_candidate_entries(
    clean_standard_data(eurorad_to_standard(found)),
    old_data.columns,
    "../candidate_metadata.csv",
    "../candidate_images")
