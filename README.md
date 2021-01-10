
#### 🛑 Note: please do not claim diagnostic performance of a model without a clinical study! This is not a kaggle competition dataset. Please read this paper about evaluation issues: [https://arxiv.org/abs/2004.12823](https://arxiv.org/abs/2004.12823) and [https://arxiv.org/abs/2004.05405](https://arxiv.org/abs/2004.05405)


## COVID-19 image data collection ([🎬 video about the project](https://www.youtube.com/watch?v=ineWmqfelEQ))

Project Summary: To build a public open dataset of chest X-ray and CT images of patients which are positive or suspected of COVID-19 or other viral and bacterial pneumonias ([MERS](https://en.wikipedia.org/wiki/Middle_East_respiratory_syndrome), [SARS](https://en.wikipedia.org/wiki/Severe_acute_respiratory_syndrome), and [ARDS](https://en.wikipedia.org/wiki/Acute_respiratory_distress_syndrome).). Data will be collected from public sources as well as through indirect collection from hospitals and physicians. All images and data will be released publicly in this GitHub repo. 

This project is approved by the University of Montreal's Ethics Committee #CERSES-20-058-D

## View current [images](images) and [metadata](metadata.csv) and [a dataloader example](https://colab.research.google.com/drive/1A-gIZ6Xp-eh2b4CGS6BHH7-OgZtyjeP2)

The labels are arranged in a hierarchy:

<img width=300 src="docs/hierarchy.jpg"/>


Current stats of PA, AP, and AP Supine views. Labels 0=No or 1=Yes. Data loader is [here](https://github.com/mlmed/torchxrayvision/blob/master/torchxrayvision/datasets.py#L867)
``` 
COVID19_Dataset num_samples=481 views=['PA', 'AP']
{'ARDS': {0.0: 465, 1.0: 16},
 'Bacterial': {0.0: 445, 1.0: 36},
 'COVID-19': {0.0: 162, 1.0: 319},
 'Chlamydophila': {0.0: 480, 1.0: 1},
 'E.Coli': {0.0: 481},
 'Fungal': {0.0: 459, 1.0: 22},
 'Influenza': {0.0: 478, 1.0: 3},
 'Klebsiella': {0.0: 474, 1.0: 7},
 'Legionella': {0.0: 474, 1.0: 7},
 'Lipoid': {0.0: 473, 1.0: 8},
 'MERS': {0.0: 481},
 'Mycoplasma': {0.0: 476, 1.0: 5},
 'No Finding': {0.0: 467, 1.0: 14},
 'Pneumocystis': {0.0: 459, 1.0: 22},
 'Pneumonia': {0.0: 36, 1.0: 445},
 'SARS': {0.0: 465, 1.0: 16},
 'Streptococcus': {0.0: 467, 1.0: 14},
 'Varicella': {0.0: 476, 1.0: 5},
 'Viral': {0.0: 138, 1.0: 343}}

COVID19_Dataset num_samples=173 views=['AP Supine']
{'ARDS': {0.0: 170, 1.0: 3},
 'Bacterial': {0.0: 169, 1.0: 4},
 'COVID-19': {0.0: 41, 1.0: 132},
 'Chlamydophila': {0.0: 173},
 'E.Coli': {0.0: 169, 1.0: 4},
 'Fungal': {0.0: 171, 1.0: 2},
 'Influenza': {0.0: 173},
 'Klebsiella': {0.0: 173},
 'Legionella': {0.0: 173},
 'Lipoid': {0.0: 173},
 'MERS': {0.0: 173},
 'Mycoplasma': {0.0: 173},
 'No Finding': {0.0: 170, 1.0: 3},
 'Pneumocystis': {0.0: 171, 1.0: 2},
 'Pneumonia': {0.0: 26, 1.0: 147},
 'SARS': {0.0: 173},
 'Streptococcus': {0.0: 173},
 'Varicella': {0.0: 173},
 'Viral': {0.0: 41, 1.0: 132}}

 ```
 
## Annotations

[Lung Bounding Boxes](https://github.com/GeneralBlockchain/covid-19-chest-xray-lung-bounding-boxes-dataset) and [Chest X-ray Segmentation](https://github.com/GeneralBlockchain/covid-19-chest-xray-segmentations-dataset) (license: CC BY 4.0) contributed by [General Blockchain, Inc.](https://github.com/GeneralBlockchain)

[Pneumonia severity scores for 94 images](annotations/covid-severity-scores.csv) (license: CC BY-SA) from the paper [Predicting COVID-19 Pneumonia Severity on Chest X-ray with Deep Learning](http://arxiv.org/abs/2005.11856)

[Generated Lung Segmentations](annotations/lungVAE-masks) (license: CC BY-SA) from the paper [Lung Segmentation from Chest X-rays using Variational Data Imputation](https://arxiv.org/abs/2005.10052)

[Brixia score for 192 images](https://github.com/BrixIA/Brixia-score-COVID-19) (license: CC BY-NC-SA) from the paper [End-to-end learning for semiquantitative rating of COVID-19 severity on Chest X-rays](https://arxiv.org/abs/2006.04603)

[Lung and other segmentations for 517 images](https://github.com/v7labs/covid-19-xray-dataset/tree/master/annotations) (license: CC BY) in COCO and raster formats by [v7labs](https://github.com/v7labs/covid-19-xray-dataset)

## Contribute

 - Submit data directly to the project. View our [research protocol](https://docs.google.com/document/d/14b7cou98YhYcJ2jwOKznChtn5y6-mi9bgjeFv2DxOt0/edit). Contact us to start the process.
 - We can extract images from publications. Help identify publications which are not already included using a GitHub issue (DOIs we have are listed in the metadata file). There is a searchable database of COVID-19 papers [here](https://www.who.int/emergencies/diseases/novel-coronavirus-2019/global-research-on-novel-coronavirus-2019-ncov), and a non-searchable one (requires download) [here](https://pages.semanticscholar.org/coronavirus-research).
 
 - Submit data to these sites (we can scrape the data from them):
    - https://radiopaedia.org/ (license CC BY-NC-SA)
    - https://www.sirm.org/category/senza-categoria/covid-19/ 
    - https://www.eurorad.org/ (license CC BY-NC-SA)
    - https://coronacases.org/ (preferred for CT scans, license Apache 2.0)
 
 - Provide bounding box/masks for the detection of problematic regions in images already collected.

 - See [SCHEMA.md](SCHEMA.md) for more information on the metadata schema.

*Formats:* For chest X-ray dcm, jpg, or png are preferred. For CT nifti (in gzip format) is preferred but also dcms. Please contact with any questions.

## Background 

In the context of a COVID-19 pandemic, we want to improve prognostic predictions to triage and manage patient care. Data is the first step to developing any diagnostic/prognostic tool. While there exist large public datasets of more typical chest X-rays from the NIH [Wang 2017], Spain [Bustos 2019], Stanford [Irvin 2019], MIT [Johnson 2019] and Indiana University [Demner-Fushman 2016], there is no collection of COVID-19 chest X-rays or CT scans designed to be used for computational analysis.

The 2019 novel coronavirus (COVID-19) presents several unique features [Fang, 2020](https://pubs.rsna.org/doi/10.1148/radiol.2020200432) and [Ai 2020](https://pubs.rsna.org/doi/10.1148/radiol.2020200642). While the diagnosis is confirmed using polymerase chain reaction (PCR), infected patients with pneumonia may present on chest X-ray and computed tomography (CT) images with a pattern that is only moderately characteristic for the human eye [Ng, 2020](https://pubs.rsna.org/doi/10.1148/ryct.2020200034). In late January, a Chinese team published a paper detailing the clinical and paraclinical features of COVID-19. They reported that patients present abnormalities in chest CT images with most having bilateral involvement [Huang 2020](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30183-5/fulltext). Bilateral multiple lobular and subsegmental areas of consolidation constitute the typical findings in chest CT images of intensive care unit (ICU) patients on admission [Huang 2020](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30183-5/fulltext). In comparison, non-ICU patients show bilateral ground-glass opacity and subsegmental areas of consolidation in their chest CT images [Huang 2020](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30183-5/fulltext). In these patients, later chest CT images display bilateral ground-glass opacity with resolved consolidation [Huang 2020](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30183-5/fulltext). 


## Goal

Our goal is to use these images to develop AI based approaches to predict and understand the infection. Our group will work to release these models using our open source [Chester AI Radiology Assistant platform](https://mlmed.org/tools/xray/).

The tasks are as follows using chest X-ray or CT (preference for X-ray) as input to predict these tasks:

- Healthy vs Pneumonia (prototype already implemented [Chester](https://mlmed.org/tools/xray/) with ~74% AUC, validation study [here](https://arxiv.org/abs/2002.02497))

- ~~Bacterial vs Viral vs COVID-19 Pneumonia~~ (not relevant enough for the clinical workflows)

- Prognostic/severity predictions (survival, need for intubation, need for supplemental oxygen)

## Expected outcomes

Tool impact: This would give physicians an edge and allow them to act with more confidence while they wait for the analysis of a radiologist by having a digital second opinion confirm their assessment of a patient's condition. Also, these tools can provide quantitative scores to consider and use in studies.

Data impact: Image data linked with clinically relevant attributes in a public dataset that is designed for ML will enable parallel development of these tools and rapid local validation of models. Furthermore, this data can be used for completely different tasks.


## Contact
PI: [Joseph Paul Cohen. Postdoctoral Fellow, Mila, University of Montreal](https://josephpcohen.com/) 

## Citations

Second Paper available [here](http://arxiv.org/abs/2006.11988) and [source code for baselines](https://github.com/mlmed/torchxrayvision/tree/master/scripts/covid-baselines)

```
COVID-19 Image Data Collection: Prospective Predictions Are the Future
Joseph Paul Cohen and Paul Morrison and Lan Dao and Karsten Roth and Tim Q Duong and Marzyeh Ghassemi
arXiv:2006.11988, https://github.com/ieee8023/covid-chestxray-dataset, 2020
```

```
@article{cohen2020covidProspective,
  title={COVID-19 Image Data Collection: Prospective Predictions Are the Future},
  author={Joseph Paul Cohen and Paul Morrison and Lan Dao and Karsten Roth and Tim Q Duong and Marzyeh Ghassemi},
  journal={arXiv 2006.11988},
  url={https://github.com/ieee8023/covid-chestxray-dataset},
  year={2020}
}
```

Paper available [here](https://arxiv.org/abs/2003.11597)

```
COVID-19 image data collection, arXiv:2003.11597, 2020
Joseph Paul Cohen and Paul Morrison and Lan Dao
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

## License

Each image has license specified in the metadata.csv file. Including Apache 2.0, CC BY-NC-SA 4.0, CC BY 4.0.

The metadata.csv, scripts, and other documents are released under a CC BY-NC-SA 4.0 license. Companies are free to perform research. Beyond that contact us.
