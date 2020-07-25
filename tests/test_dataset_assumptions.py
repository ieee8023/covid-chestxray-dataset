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
    assert set(all_images).difference(set(linked_images)) == set()

def test_no_pediatric():
    assert min(metadata["age"]) >= 18
