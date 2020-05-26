import torch
import torchvision
import torchxrayvision as xrv
from tqdm import tqdm
import sys

# print stats
for views in [["PA","AP"],["AP Supine"]]:
    print(xrv.datasets.COVID19_Dataset(views=views,
                                         imgpath="../images",
                                         csvpath="../metadata.csv"))

d_covid19 = xrv.datasets.COVID19_Dataset(views=["PA", "AP", "AP Supine"],
                                         imgpath="../images",
                                         csvpath="../metadata.csv")
print(d_covid19)

for i in tqdm(range(len(d_covid19))):
    idx = len(d_covid19)-i-1
    try:
        # start from the most recent
        a = d_covid19[idx]
    except KeyboardInterrupt:
        break;
    except:
        print("Error with {}".format(i) + d_covid19.csv.iloc[idx].filename)
        print(sys.exc_info()[1])
