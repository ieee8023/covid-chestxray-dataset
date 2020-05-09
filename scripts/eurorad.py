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

max_results = 10000000000

def wait():
    time.sleep(1)

def get_browser():

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
    return "https://www.eurorad.org/advanced-search?search=" + "+".join(search_terms)

def extract_results_from_search_page(browser):
    out = []
    for a in browser.find_elements_by_xpath("//a[contains(@href,'/case/')]"):
        out.append(a.get_attribute("href"))
    return list(set(out))

def get_next_search_page(browser):
    try:
        next_ref = browser.find_element_by_xpath(
            "//div[@class='pagination']/a[@title='Go to next page']"
        )
        return next_ref.get_attribute("href")
    except:
        return None

def get_search_results(search_terms, browser):
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

    debug = False

    if debug:

        print("images")
        for image in images:
            pdb.set_trace()

        print("image descriptions")
        for description in image_descriptions:
            pdb.set_trace()

    time.sleep(5)

    figure_label_xpath = "//li[@class='list-inline-item' and ./a[contains(@class, figure-gallery-paginator__link) and @href='#']]"
    figure_labels = browser.find_elements_by_xpath(figure_label_xpath)

    image_descriptions_text = []

    print("figure_labels")
    print(figure_labels)
    print("image_descriptions")
    print(image_descriptions)

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
            print(description)
            print("CT" if "CT" in description else "X-ray")
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
    result_pages = list(get_search_results(search_terms, browser))
    print(result_pages)
    for result_page in result_pages:
        browser.get(result_page)
        wait()
        yield metadata_from_result_page(browser)

def metadata_from_search_terms(search_terms, browser):
    result_pages = list(get_search_results(search_terms))
    print(result_pages)
    for result_page in result_pages:
        browser.get(result_page)
        wait()
        yield metadata_from_result_page()

class EuroRadCase():
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
    return os.path.basename(urlparse(url).path)

def find_new_eurorad_entries(old_data, new_cases):
    new_data = []
    for new_case in new_cases:
        if not new_case._in(old_data):
            data = new_case.get_data()
            new_data.append(data)
    return new_data

def output_candidate_entries(standard, columns, out_name, img_dir):
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
                print(image)
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

import numpy as np
from PIL import Image
import urllib.request
import matplotlib.pyplot as plt

def split_image(img, horiz=None, vert=None):
    img = np.array(img)
    #1. Find borders
    if horiz and vert:
        vert_borders = (img.shape[0] * np.array(range(vert+1))/vert).astype(int)
        horiz_borders = (img.shape[1] * np.array(range(horiz+1))/horiz).astype(int)
    else:
    #2. Split images
        horiz_borders, vert_borders = find_borders(img,
                                                   threshold=.9,
                                                   blur_range=10)
        horiz_borders = [0] + list(horiz_borders) + [img.shape[0]]
        vert_borders = [0] + list(vert_borders) + [img.shape[0]]
    print(horiz_borders)
    print(vert_borders)
    for vert_idx in range(len(vert_borders)-1):
        for horiz_idx in range(len(horiz_borders)-1):
            x_start = vert_borders[vert_idx]
            x_end = vert_borders[vert_idx+1]
            y_start = horiz_borders[horiz_idx]
            y_end = horiz_borders[horiz_idx+1]
            print(x_start, x_end, y_start, y_end)
            yield img[x_start:x_end, y_start:y_end]

def blur_boolean(array, b, operation="or"):
    l = array.shape[0]
    out_array = array[:l-b]
    print(array.shape)
    print(out_array.shape)
    for i in range(1, b + 1):
        print(i)
        if operation == "or":
            out_array = out_array | array[i:l-b+i]
        elif operation == "and":
            out_array = out_array & array[i:l-b+i]
    return out_array

def find_maximi(horiz_contrast, threshold = .9, blur_range=None):
    if blur_range is None:
        blur_range = 10
    over = horiz_contrast > threshold
    over = blur_boolean(over, blur_range)
    start = np.where(over[1:] & ~over[:-1])[0]
    stop = np.where(~over[1:] & over[:-1])[0]
    return np.mean([start, stop],axis=0).astype(int)

def find_borders(img, threshold = .9, blur_range=10):
    horiz_contrast = np.mean(np.abs((lambda img, n: np.array(img)[:,n:] - np.array(img)[:,:-n])(img, 3)),axis=0)
    vert_contrast = np.mean(np.abs((lambda img, n: np.array(img)[n:] - np.array(img)[:-n])(img, 3)),axis=0)
    mx = max(horiz_contrast.max(), vert_contrast.max())
    print("max",mx)
    horiz_borders = find_maximi(horiz_contrast/mx, threshold, blur_range)
    vert_borders = find_maximi(vert_contrast/mx, threshold, blur_range)
    return horiz_borders, vert_borders

def crop(img, thresh=.05):
    def crop_downwards(img, thresh):
        cropped = False
        while variance(img[0]) < thresh:
            img = img[1:]
            cropped = True
        return img, cropped
    def crop_upwards(img, thresh):
        cropped = False
        while variance(img[-1]) < thresh:
            img = img[:-1]
            cropped = True
        return img, cropped
    def crop_horizontal(img, thresh):
        cropped = False
        while variance(img[:,0]) < thresh:
            img = img[:,1:]
            cropped = True
        return img, cropped
    def crop_vertical(img, thresh):
        cropped = False
        while variance(img[:,-1]) < thresh:
            img = img[:,:-1]
            cropped = True
        return img, cropped
    any_cropped = False
    total_variation_in_image = variance(img)
    thresh = thresh * total_variation_in_image
    for crop_func in [crop_horizontal,
                      crop_vertical,
                      crop_upwards,
                      crop_downwards]:
        img, cropped = crop_func(img, thresh)
        any_cropped |= cropped
    if any_cropped:
        return crop_border(img, thresh)
    return img

def variance(arr):
    return np.abs(arr - arr.mean()).mean()

def clean_standard_data(standard_data):
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


old_data = pd.read_table("../metadata.csv",sep=",")

new_cases = get_search_results(["COVID"],browser)

found = find_new_eurorad_entries(old_data, new_cases)

output_candidate_entries(
    clean_standard_data(eurorad_to_standard(found)),
    old_data.columns,
    "../candidate_metadata.csv",
    "../candidate_images")
