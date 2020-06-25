import pandas as pd
import numpy as np
import argparse
from subprocess import run
import os
import shutil

#Initial clone

def where_offset_zero(val, offset):
    val = val.copy()
    val[offset!=0] = pd.NA
    return val

def tf_to_yn(arg):
    if pd.isna(arg):
        return arg
    else:
        return "Y" if arg else "N"

def coerce_numeric(row):
    row = row.replace([np.inf, -np.inf], np.nan)
    return pd.to_numeric(row, errors="coerce")

def convert_metadata(data, starting_ptid):
    #Id: Count up from highest in metadata.csv
    id_ = data["patient_id"].astype("category").cat.codes
    id_ += starting_ptid + 1
    
    #Use Admission Offset as offset
    offset = -pd.to_numeric(data["admission_offset"],errors="coerce")
    
    #Image names from image ids
    file_col = data["image_id"].apply(lambda i: i + ".jpg")

    #ICU data
    
    went_icu = data.groupby("patient_id").aggregate({"icu_admission_offset":lambda column: any(~column.isna())})
    went_icu = went_icu.loc[data["patient_id"]]["icu_admission_offset"].reset_index(drop=True)

    in_icu = went_icu & (data["icu_admission_offset"] <= 0) & (data["icu_release_offset"] > 0)
    
    went_icu = went_icu.apply(tf_to_yn)
    in_icu = in_icu.apply(tf_to_yn)
    
    #COVID-19 or No Finding
    
    def choose_finding(

    finding = data["admission_offset"].apply(choose_finding) #lambda i: "COVID-19" if i <= 0 else "No Finding")
    
    #Survival data
    
    def survived(row):
        if not pd.isna(row["death_offset"]):
            return "N"
        elif not pd.isna(row["icu_release_offset"]):
            return "Y"
        else:
            return pd.NA
    
    survival = data.apply(survived,axis=1)
    
    #Take clinical data where the offset is zero
    
    lymph = where_offset_zero(
        data["lymphocytes_val"],
        data["lymphocytes_offset"]
    )
    lymph = coerce_numeric(lymph)
    
    
    po2 = where_offset_zero(
        data["po2_val"],
        data["po2_offset"]
    )
    po2 = coerce_numeric(po2)
    
    neutro = where_offset_zero(
        data["neutrophils_val"],
        data["neutrophils_offset"]
    )
    neutro = coerce_numeric(neutro)
    
    #Uppercase
    sex = data["sex"].str.upper()
    projection = data["projection"].str.upper()
    
    new_data = pd.DataFrame({
                         "patientid":id_,
                         "sex":sex,
                         "view":projection,
                         "offset":offset,
                         "lymphocyte_count":lymph,
                         "pO2_saturation":po2,
                         "neutrophil_count":neutro,
                         "in_icu":in_icu,
                         "went_icu":went_icu,
                         "survival":survival,
                         "url":"https://github.com/ml-workgroup/covid-19-image-repository",
                         "license":"CC BY 3.0",
                         "location":"Hannover Medical School, Hannover, Germany",
                         "doi":"10.6084/m9.figshare.12275009",
                         "finding":finding,
                         "filename":file_col,
                         "folder":"images",
                         "modality":"X-ray",
                         "date":2020
    })

    new_data.sort_values(["patientid","offset"])

    return new_data


def pull_repo(repo):
    if not os.path.exists("covid-19-image-repository"):
        run("git clone https://github.com/ml-workgroup/covid-19-image-repository.git".split(" "))
    curr = os.getcwd()
    os.chdir(repo)
    run("git pull origin master".split(" "))
    os.chdir(curr)

def add_hannover(hannover_repo,
                 mila_repo,
                 exclude_path,
                 filename=None):
    excluded_images = pd.read_csv(exclude_path)

    pull_repo(hannover_repo)
    #Open hannover data
    hannover_csv_path = os.path.join(hannover_repo, "data.csv")
    data = pd.read_csv(hannover_csv_path)

    #Open mila data
    mila_csv_path = os.path.join(mila_repo, "metadata.csv")
    metadata = pd.read_table(mila_csv_path,sep=",", dtype="str")

    print("metadata shape", metadata.shape)

    #Convert and append hannover data
    hannover_data = convert_metadata(data,
                                starting_ptid=int(max(metadata["patientid"])))

    print(hannover_data)

    print("hannover shape", hannover_data.shape)

    drop_mask = hannover_data["filename"].map(lambda name: name[name.index(".")] in excluded_images)
    hannover_data = hannover_data[~drop_mask]

    print("dropping", sum(drop_mask))
    print("hannover shape", hannover_data.shape)

    def get_number(x):
        valid_characters = "1234567890"
        return float("".join(i for i in str(x) if i in valid_characters))

    def fill_rest_of_ptids(data):
        max_ptid = max(data, key=get_number)
        na_ptid_mask = data["ptid"].isna()
        ptid_order = data["ptid"].cat.codes
        data.loc[na_ptid_mask,"ptid"] = max_ptid + ptid_order

    def update_data(metadata, hannover_data):
        metadata = metadata.copy()
        hannover_data = hannover_data.copy()
        metadata.index = metadata["filename"].apply(lambda name: os.path.splitext(name)[0])
        hannover_data.index = hannover_data["filename"].apply(lambda name: os.path.splitext(name)[0])
        #Use same ptids in Hannover data
        #hannover_data = hannover_data.drop("patientid",axis=1)
        hannover_data = hannover_data.rename(columns={"patientid":"original_ptid"})
        print(hannover_data.columns)
        hannover_data = hannover_data.join(metadata[["patientid"]],how="left")
        print(hannover_data.columns)
        max_ptid = max(metadata["patientid"], key=get_number)
        is_new = hannover_data["patientid"] == hannover_data["original_ptid"]
        temp_ids_for_new_pts = hannover_data.loc[is_new, "patientid"].astype("category").cat.codes
        hannover_data.loc[is_new,"patientid"] = max_ptid + temp_ids_for_new_pts + 1
        hannover_data = hannover_data.drop("original_ptid",axis=1)
        #new_data = pd.DataFrame(index=list(set(hannover_data.index).union(metadata.index)))
        #new_data = new_data.merge(metadata).merge(hannover_data)
        new_data = pd.concat([metadata, hannover_data])
        new_data = new_data.drop_duplicates(keep="last")
        #Assume all NA ptids are at the end
        row_order = np.argsort(new_data["patientid"].str.pad(width=int(max(new_data["patientid"].str.len()))))
        new_data = new_data.iloc[row_order,:]
        return new_data.reset_index(drop=True)

    merged_data = update_data(metadata, hannover_data)
    print("merged shape", merged_data.shape)
    #filename in @existing_images")
    mila_img_path = os.path.join(mila_repo, "images")
    hannover_img_path = os.path.join(hannover_repo, "jpg")
    for image in hannover_data["filename"]:
        if not os.path.exists(os.path.join(mila_img_path, image)):
            print(image)
            shutil.copyfile(os.path.join(hannover_img_path, image),
                            os.path.join(mila_img_path, image))
    #Write new metadata
    merged_data.to_csv(mila_csv_path, index=False)

    return merged_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("hannover_repo", help="path to covid-19-image-repository")
    parser.add_argument("mila_repo", help="path to covid-chestxray-dataset")
    parser.add_argument("exclude_path", help="file containing images to exclude")
    args = parser.parse_args()
    add_hannover(args.hannover_repo, args.mila_repo, args.exclude_path)
