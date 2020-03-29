**metadata**

Here is a list of each metadata field, with explanations where relevant

| Attribute | Description |
|------|-----|
| patientid | Internal identifier |
| offset | Number of days since the start of symptoms or hospitalization for each image. If a report indicates "after a few days", then 5 days is assumed. This is very important to have when there are multiple images for the same patient to track progression. |
| sex | Male (M), Female (F), or blank |
| age | Age of the patient in years |
| finding | Type of pneumonia |
| survival | Yes (Y) or no (N) |
| view | Posteroanterior (PA), Anteroposterior (AP), AP Supine (APS), or Lateral (L) for X-rays; Axial or Coronal for CT scans |
| modality | CT, X-ray, or something else |
| date | Date on which the image was acquired |
| location | Hospital name, city, state, country |
| filename | Name with extension |
| doi | Digital object identifier ([DOI](https://en.wikipedia.org/wiki/Digital_object_identifier)) of the research article |
| url | URL of the paper or website where the image came from |
| license | License of the image such as CC BY-NC-SA. Blank if unknown |
| clinical notes | Clinical notes about the image and/or the patient |
| other notes | e.g. credit |
