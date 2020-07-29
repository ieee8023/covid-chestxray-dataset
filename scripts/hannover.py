import pandas as pd
import pdb
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
    """Convert the provided data to a format compatible with metadata.csv"""
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

    def choose_finding(offset):
        #In terms of original offset
        if offset > 14:
            return "No Finding"
        elif offset > 7:
            return "Unknown"
        else:
            return "COVID-19"
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
    projection = data["projection"].str.upper().map(
        lambda view: {"AP":"AP Supine"}.get(view, view)
    )
    
    new_data = pd.DataFrame({
                         "patientid":id_,
                         "sex":sex,
                         "view":projection,
                         "offset":offset,
                         "lymphocyte_count":lymph,
                         "pO2_saturation":po2.astype("Int64"),
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
    """Update a local clone of the Hannover repository."""
    if not os.path.exists(repo):
        run("git clone https://github.com/ml-workgroup/covid-19-image-repository.git".split(" "))
    curr = os.getcwd()
    os.chdir(repo)
    run("git pull origin master".split(" "))
    os.chdir(curr)

def fname_minus_extension(name):
    """Remove the extension from a filename"""
    return os.path.splitext(name)[0]

def update_data(metadata, hannover_data):
    """Incorporate the Hannover data into metadata"""
    def get_number(x):
        valid_characters = "1234567890"
        return float("".join(i for i in str(x) if i in valid_characters))
    #Copy data
    metadata = metadata.copy()
    hannover_data = hannover_data.copy()

    #Temporarily index by filename (without extension(
    metadata.index = metadata["filename"]
    hannover_data.index = hannover_data["filename"]

    #Default to existing ptids if available
    hannover_data = hannover_data.rename(columns={"patientid":"original_ptid"})
    hannover_data = hannover_data.join(metadata[["patientid"]],how="left")

    #For new entries, count up from the highest existing ptid.
    is_new = hannover_data["patientid"].isna()
    max_ptid = max(metadata["patientid"].map(get_number))
    arbitrary_ids_for_new_pts = hannover_data.loc[is_new, "original_ptid"]
    id_offsets_for_new_pts = pd.Series(
        arbitrary_ids_for_new_pts.astype("category").cat.codes.astype(int)
    ).copy()
    real_ids_for_new_pts = (max_ptid + id_offsets_for_new_pts + 1).astype(int)
    hannover_data.loc[is_new,"patientid"] = real_ids_for_new_pts
    hannover_data = hannover_data.drop("original_ptid",axis=1)

    #Combine data
    new_data = pd.concat([metadata, hannover_data])
    new_data = new_data[~new_data.index.duplicated(keep="last")]

    #Assume all NA ptids are at the end
    all_file_keys = list(metadata.index) + list(hannover_data.index[is_new])
    new_data = new_data.loc[all_file_keys, :]

    #Reset index before returning
    return new_data.reset_index(drop=True)

def remove_deleted_hannover_entries(metadata, hannover_data, mila_repo, ask_to_delete_images):
    """Remove Hannover entries from metadata if they are not in the
    most current version of the Hannover data."""
    #Extract file ids from old and new Hannover data
    hannover_entries_in_metadata = select_hannover_from_metadata(metadata)
    current_hannover_ids = list(
        hannover_data["filename"].map(fname_minus_extension)
    )
    old_hannover_ids = list(
        hannover_entries_in_metadata["filename"].map(fname_minus_extension)
    )
    #Collect entries that must be deleted
    to_remove = []
    for old_hannover_id in old_hannover_ids:
        if not old_hannover_id in current_hannover_ids:
            to_remove.append(old_hannover_id)
    print("Removed:", ", ".join(to_remove))
    #Delete them
    if input("Press y to delete these images") == "y" or not ask_to_delete_images:
        for id in to_remove:
            try:
                os.remove(os.path.join(mila_repo, "images", id + ".jpg"))
            except FileNotFoundError:
                pass
    else:
        print("Not deleting images")
    delete_mask = metadata["filename"].map(fname_minus_extension).apply(lambda i: i in to_remove)
    return to_remove, metadata[~delete_mask].reset_index(drop=True)

def select_hannover_from_metadata(metadata):
    """Select entries from Hannover"""
    return metadata.query('doi == "10.6084/m9.figshare.12275009"')

def check_hannover(merged_data, hannover_data):
    """Check whether any inaccuracies have been introduced into the the
    Hannover data during the merging process"""
    merged_data = merged_data.copy()
    hannover_data = hannover_data.copy()
    hannover_from_metadata = select_hannover_from_metadata(merged_data)
    hannover_from_metadata = hannover_from_metadata[hannover_data.columns].drop("patientid",axis=1).sort_values(by=["filename"]).fillna(0).to_numpy()
    hannover_data = hannover_data.drop("patientid",axis=1).sort_values(by=["filename"]).fillna(0).to_numpy()
    return np.array_equiv(hannover_data, hannover_from_metadata)

def add_hannover(hannover_repo,
                 mila_repo,
                 exclude_path,
                 filename=None):
    """Update dataset to incorporate Hannover images"""
    excluded_images = list(pd.read_csv(exclude_path).iloc[:, 0])

    pull_repo(hannover_repo)

    #Open hannover data
    hannover_csv_path = os.path.join(hannover_repo, "data.csv")
    hannover_data = pd.read_csv(hannover_csv_path)
    print("shape of hannover data", hannover_data.shape)

    #Open mila data
    mila_csv_path = os.path.join(mila_repo, "metadata.csv")
    metadata = pd.read_table(mila_csv_path,sep=",", dtype="str")
    print("shape of original data", metadata.shape)

    #Filter out excluded entries back in.
    exclusion_mask = hannover_data["image_id"].map(
        lambda i: i in excluded_images
    )
    hannover_data = hannover_data.loc[~exclusion_mask,:]
    hannover_data = hannover_data.reset_index(drop=True)

    #Convert Hannover data
    hannover_data = convert_metadata(hannover_data, starting_ptid=0)

    #If old entries are deleted, take them out of metadata.csv
    removed, metadata = remove_deleted_hannover_entries(
        metadata,
        hannover_data,
        mila_repo,
        ask_to_delete_images=True
    )

    #Merge the data
    merged_data = update_data(metadata, hannover_data)
    print("shape of merged data", merged_data.shape)

    #Copy images. Currently this step is not automated.
    #mila_img_path = os.path.join(mila_repo, "images")
    #hannover_img_path = os.path.join(hannover_repo, "png")
    #for image in hannover_data["filename"]:
    #    if not os.path.exists(os.path.join(mila_img_path, image)):
    #        print(image)
    #        shutil.copyfile(os.path.join(hannover_img_path, image),
    #                        os.path.join(mila_img_path, image))
    #Write new metadata

    assert check_hannover(merged_data, hannover_data)

    merged_data.to_csv(mila_csv_path, index=False)

    return merged_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("hannover_repo", help="path to covid-19-image-repository")
    parser.add_argument("mila_repo", help="path to covid-chestxray-dataset")
    parser.add_argument("exclude_path", help="file containing images to exclude")
    args = parser.parse_args()
    add_hannover(args.hannover_repo, args.mila_repo, args.exclude_path)
