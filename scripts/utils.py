import os
import shutil
from urllib.parse import urlparse
from scipy.stats import truncnorm
from subprocess import run
import time
from tqdm import tqdm
import pickle
import os
import pandas as pd

global_speedup = 2

def string_or_empty(string):
    if string is None:
        return ""
    return string

def filename_from_url(url):
    "Determine the filename that the given url should be downloaded to."
    return os.path.basename(urlparse(url).path)

def find_new_entries(old_data, new_cases):
    "Iterate through the URLs in new_cases and return metadata from the ones that are not already in old_data."
    new_data = []
    for new_case in new_cases:
        if not new_case._in(old_data):
            data = new_case.get_data()
            new_data.append(data)
            yield data

def deduplicate_filename(retrieve_filename, img_dir):
    print("Starting deduplicate")
    files = os.listdir(img_dir)
    test_filename = retrieve_filename
    name, ext = os.path.splitext(retrieve_filename)
    i = 1
    while test_filename in files:
        test_filename = name + "-" + str(i) + ext
        i += 1
    print("Done deduplicating filename")
    return test_filename

def output_candidate_entries(standard, columns, out_name, img_dir, resource_cache, retry=False):
    "Save the candidate entries to a file."
    pickle_name = out_name + "_pickled_data"
    out_df = pd.DataFrame(columns=columns)
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    all_records = []
    for record in standard:
        all_records.append(record)
        with open(pickle_name, "wb") as handle:
            pickle.dump(all_records, handle)
        patient = clean_standard_data(record)
        all_filenames = []
        #print(patient)
        for image in patient["images"]:
            #print(image)
            for url in image["url"]:
                retrieve_filename = deduplicate_filename(
                    filename_from_url(url),
                    img_dir
                )
                try:
                    #print("ResourceCache", url, list(ResourceCache.data))
                    #print("being transferred to", retrieve_filename)
                    full_destination = os.path.join(img_dir, retrieve_filename)
                    #print("full_destination", full_destination)
                    source = resource_cache.get(url)
                    #print("source", source)
                    shutil.copyfile(
                        source,
                        full_destination
                    )
                except Exception as e:
                    print(e)
                    #pdb.set_trace()
                    print("Oh no! Failed to download!")
                    raise
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

def wget(src, filename):
    if run(["wget", src, "-O", filename]).returncode != 0:
        raise ValueError

def wait(n):
    """Wait a random period of time"""
    time_to_sleep = truncnorm.rvs(n/2, n*2, loc=n, scale=n/4) / global_speedup
    granularity = 10
    for i in tqdm(range(int(time_to_sleep * granularity))):
        time.sleep(1/granularity)

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
    print(standard_record)
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

def dictionary_walk(dictionary):
    for key, value in dictionary.items():
        if isinstance(value, dict):
            yield from dictionary_walk(value)
        else:
            yield (key, value)

def standard_to_metadata_format(standard_record, filenames):
    "Convert data in an interoperable format to the format in metadata.csv"
    all_rows = []
    images = standard_record["images"]
    standard_patient = standard_record["patient"]
    for image, filename in zip(images, filenames):
        patient_row = {}
        #Update with all entries. 'misc' will be removed on conversion to dataframe.
        for key, value in dictionary_walk(standard_patient):
            print(key, value)
            patient_row[key] = value
        patient_row["clinical_notes"] = (
            string_or_empty(patient_row.pop("clinical_history")) + " " + image["image_description"]
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
        patient_row["filename"] = filename
        print(patient_row)
        all_rows.append(patient_row)
    return all_rows
