import pytest
import os
import pandas as pd

metadata = pd.read_csv("metadata.csv")

def test_no_duplicate_images():
    filenames = metadata["filename"]
    assert len(set(filenames)) == len(filenames)

def test_no_unlinked_images():
    linked_images = metadata["filename"]
    all_images = os.listdir("images")
    #The only unlinked image should be the warning image
    assert set(all_images).difference(set(linked_images)) == set(['FAFA-A1BF-49A8-A1D3-66FAFA41B7345D.jpg'])

def test_no_pediatric():
    assert min(metadata["age"]) >= 18
