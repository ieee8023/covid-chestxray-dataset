
# 🛑 Note: please do not claim diagnostic performance of a model without a clinical study! This is not a kaggle competition dataset. 


## COVID-19 image data collection

We are building a database of COVID-19 cases with chest X-ray or CT images. We are looking for COVID-19 cases as well as [MERS](https://en.wikipedia.org/wiki/Middle_East_respiratory_syndrome), [SARS](https://en.wikipedia.org/wiki/Severe_acute_respiratory_syndrome), and [ARDS](https://en.wikipedia.org/wiki/Acute_respiratory_distress_syndrome). 

All images and data will be released publicly in this GitHub repo. Currently we are building the database with images from publications as they are images that are already available. 

## View current [images](images) and [metadata](metadata.csv)

Current stats of PA, AP, and AP Supine views. Labels 0=No or 1=Yes. Data loader is [here](https://github.com/mlmed/torchxrayvision/blob/master/torchxrayvision/datasets.py#L867)
``` 
COVID19_Dataset num_samples=201 views=['PA', 'AP']
{'ARDS': {0.0: 187, 1.0: 14},
 'Bacterial Pneumonia': {0.0: 184, 1.0: 17},
 'COVID-19': {0.0: 46, 1.0: 155},
 'Chlamydophila': {0.0: 200, 1.0: 1},
 'Fungal Pneumonia': {0.0: 188, 1.0: 13},
 'Klebsiella': {0.0: 200, 1.0: 1},
 'Legionella': {0.0: 199, 1.0: 2},
 'MERS': {0.0: 201},
 'No Finding': {0.0: 200, 1.0: 1},
 'Pneumocystis': {0.0: 188, 1.0: 13},
 'Pneumonia': {0.0: 1, 1.0: 200},
 'SARS': {0.0: 190, 1.0: 11},
 'Streptococcus': {0.0: 188, 1.0: 13},
 'Viral Pneumonia': {0.0: 35, 1.0: 166}}

COVID19_Dataset num_samples=28 views=['AP Supine']
{'ARDS': {0.0: 27, 1.0: 1},
 'Bacterial Pneumonia': {0.0: 28},
 'COVID-19': {0.0: 4, 1.0: 24},
 'Chlamydophila': {0.0: 28},
 'Fungal Pneumonia': {0.0: 28},
 'Klebsiella': {0.0: 28},
 'Legionella': {0.0: 28},
 'MERS': {0.0: 28},
 'No Finding': {0.0: 28},
 'Pneumocystis': {0.0: 28},
 'Pneumonia': {0.0: 4, 1.0: 24},
 'SARS': {0.0: 28},
 'Streptococcus': {0.0: 28},
 'Viral Pneumonia': {0.0: 4, 1.0: 24}}

 ```

## Contribute

 - We can extract images from publications. Help identify publications which are not already included using a GitHub issue (DOIs we have are listed in the metadata file). There is a searchable database of COVID-19 papers [here](https://www.who.int/emergencies/diseases/novel-coronavirus-2019/global-research-on-novel-coronavirus-2019-ncov), and a non-searchable one (requires download) [here](https://pages.semanticscholar.org/coronavirus-research).
 
 - Submit data to these sites (we can scrape the data from them):
    - https://radiopaedia.org/ (license CC BY-NC-SA)
    - https://www.sirm.org/category/senza-categoria/covid-19/ 
    - https://www.eurorad.org/ (license CC BY-NC-SA)
 
 - Provide bounding box/masks for the detection of problematic regions in images already collected.

 - See [SCHEMA.md](SCHEMA.md) for more information on the metadata schema.

*Formats:* For chest X-ray dcm, jpg, or png are preferred. For CT nifti (in gzip format) is preferred but also dcms. Please contact with any questions.

## Background 
The 2019 novel coronavirus (COVID-19) presents several unique features. While the diagnosis is confirmed using polymerase chain reaction (PCR), infected patients with pneumonia may present on chest X-ray and computed tomography (CT) images with a pattern that is only moderately characteristic for the human eye [Ng, 2020](https://pubs.rsna.org/doi/10.1148/ryct.2020200034). COVID-19’s rate of transmission depends on our capacity to reliably identify infected patients with a low rate of false negatives. In addition, a low rate of false positives is required to avoid further increasing the burden on the healthcare system by unnecessarily exposing patients to quarantine if that is not required. Along with proper infection control, it is evident that timely detection of the disease would enable the implementation of all the supportive care required by patients affected by COVID-19.

In late January, a Chinese team published a paper detailing the clinical and paraclinical features of COVID-19. They reported that patients present abnormalities in chest CT images with most having bilateral involvement [Huang 2020](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30183-5/fulltext). Bilateral multiple lobular and subsegmental areas of consolidation constitute the typical findings in chest CT images of intensive care unit (ICU) patients on admission [Huang 2020](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30183-5/fulltext). In comparison, non-ICU patients show bilateral ground-glass opacity and subsegmental areas of consolidation in their chest CT images [Huang 2020](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30183-5/fulltext). In these patients, later chest CT images display bilateral ground-glass opacity with resolved consolidation [Huang 2020](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30183-5/fulltext). 

COVID is possibly better diagnosed using radiological imaging [Fang, 2020](https://pubs.rsna.org/doi/10.1148/radiol.2020200432) and [Ai 2020](https://pubs.rsna.org/doi/10.1148/radiol.2020200642).

## Motivation

While PCR tests offer many advantages they are physical things that require shipping the test or the sample. X-ray machines can be plugged in to screen patients as long as they have electricity. 

Imagine a future where we run out of tests and then the majority of radiologists get sick. AI tools can help general practitioners to triage and treat patients.

Companies are developing AI tools and deploying them at hospitals [Wired 2020](https://www.wired.com/story/chinese-hospitals-deploy-ai-help-diagnose-covid-19/). We should have an open database to develop free tools that will also provide assistance.

## Goal

Our goal is to use these images to develop AI based approaches to predict and understand the infection. Our group will work to release these models using our open source [Chester AI Radiology Assistant platform](https://mlmed.org/tools/xray/) which is designed to scale to a global need by performing the computation locally.

The tasks are as follows using chest X-ray or CT (preference for X-ray) as input to predict these tasks:

- Healthy vs Pneumonia (prototype already implemented [Chester](https://mlmed.org/tools/xray/) with ~74% AUC, validation study [here](https://arxiv.org/abs/2002.02497))

- Bacterial vs Viral vs COVID-19 Pneumonia

- Survival of patient




## Contact
Contact: [Joseph Paul Cohen. Postdoctoral Fellow, Mila, University of Montreal](https://josephpcohen.com/) 

## Initial results

![](docs/covid-xray-umap.png)

## Citation

Paper availabe [here](https://arxiv.org/abs/2003.11597)

```
Joseph Paul Cohen and Paul Morrison and Lan Dao
COVID-19 image data collection, arXiv:2003.11597, 2020
https://github.com/ieee8023/covid-chestxray-dataset
```

```
@article{cohen2020covid,
  title={COVID-19 image data collection},
  author={Joseph Paul Cohen and Paul Morrison and Lan Dao},
  journal={arXiv 2003.11597},
  url={https://github.com/ieee8023/covid-chestxray-dataset},
  year={2020}
}
```

<meta name="citation_title" content="COVID-19 image data collection" />
<meta name="citation_publication_date" content="2020" />
<meta name="citation_author" content="Joseph Paul Cohen and Paul Morrison and Lan Dao" />
