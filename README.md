<img src="docs/covid19-share-image.jpg"/>

## COVID-19 image data collection

We are building a database of COVID-19 cases with chest X-ray or CT images. We are looking for COVID-19 cases as well as [MERS](https://en.wikipedia.org/wiki/Middle_East_respiratory_syndrome), [SARS](https://en.wikipedia.org/wiki/Severe_acute_respiratory_syndrome), and [ARDS](https://en.wikipedia.org/wiki/Acute_respiratory_distress_syndrome). 

All images and data will be released publicly in this GitHub repo. Currently we are building the database with images from publications as they are images that are already available. 

## View current [images](images) and [metadata](metadata.csv)


## Contribute

 - We can extract images from publications. Help identify publications which are not already included using a GitHub issue (DOIs we have are listed in the metadata file).

 - Submit your own cases (we are still working out the ethics protocol for this). First clear all ethics and consent requirements at your institution in order to make the data public and contact us.

*Formats:* For chest X-ray dcm, jpg, or png are preferred. For CT nifti (in gzip format) is preferred but also dcms. Please contact with any questions.


## Motivation

COVID is possibly better diagnosed using radiological imaging [Fang, 2020](https://pubs.rsna.org/doi/10.1148/radiol.2020200432). Companies are developing AI tools and deploying them at hospitals [Wired 2020](https://www.wired.com/story/chinese-hospitals-deploy-ai-help-diagnose-covid-19/). We should have an open database to develop free tools that will also provide assistance.

## Goal
Our goal is to use these images to develop AI based approaches to predict and understand the infection. Our group will work to release these models using the open source [Chester AI Radiology Assistant platform](https://mlmed.org/tools/xray/).

## Contact
Contact: [Joseph Paul Cohen. Postdoctoral Fellow, Mila, Univeristy of Montreal](https://josephpcohen.com/) 
