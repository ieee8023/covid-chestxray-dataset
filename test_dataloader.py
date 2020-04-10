import torch
import torchvision
import torchxrayvision as xrv
from tqdm import tqdm
import sys

d_covid19 = xrv.datasets.COVID19_Dataset(views=["PA", "AP", "AP Supine"],
                                         imgpath="./images",
                                         csvpath="./metadata.csv")
print(d_covid19)

for i in tqdm(range(len(d_covid19))):
    try:
        a = d_covid19[i]
    except KeyboardInterrupt:
        break;
    except:
        print("Error with {}".format(i) + d_covid19.csv.iloc[i].filename)
        print(sys.exc_info()[1])