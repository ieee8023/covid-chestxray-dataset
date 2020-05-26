import pytest
import torch
import torchvision
import torchxrayvision as xrv
from tqdm import tqdm
import sys


def test_dataloader_stats():
    # print stats
    for views in [["PA","AP"],["AP Supine"]]:
        print(xrv.datasets.COVID19_Dataset(views=views,
                                             imgpath="images",
                                             csvpath="metadata.csv"))
        
def test_dataloader():
    d_covid19 = xrv.datasets.COVID19_Dataset(views=["PA", "AP", "AP Supine"],
                                             imgpath="images",
                                             csvpath="metadata.csv")
    print(d_covid19)

    for i in tqdm(range(len(d_covid19))):
        # start from the most recent
        a = d_covid19[len(d_covid19)-i-1]
