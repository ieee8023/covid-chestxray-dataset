**metadata**

Here is a list of each metadata field, with explanations where relevant

| Attribute | Description |
|------|-----|
| patientid | Internal identifier |
| offset | Number of days since the start of symptoms or hospitalization for each image. If a report indicates "after a few days", then 5 days is assumed. This is very important to have when there are multiple images for the same patient to track progression. |
| sex | Male (M), Female (F), or blank |
| age | Age of the patient in years |
| finding | Type of pneumonia |
| RT_PCR_positive | Yes (Y) or no (N) or blank if not reported/taken |
| survival | Yes (Y) or no (N) or blank if unknown|
| intubated | Yes (Y) if the patient was intubated (or ventilated) at any point during this illness or No (N) or blank if unknown. |
| went_icu | Yes (Y) if the patient was in the ICU (intensive care unit) or CCU (critical care unit) at any point during this illness or No (N) or blank if unknown.|
| needed_supplemental_O2 | Yes (Y) if the patient required supplemental oxygen at any point during this illness or No (N) or blank if unknown |
| extubated | Yes (Y) if the patient was successfully extubated or No (N) or blank if unknown |
| temperature | Temperature of the patient in Celsius at the time of the image|
| pO2 saturation | partial pressure of oxygen saturation in % at the time of the image |
| wbc count | white blood cell count in units of 10^3/uL at the time of the image |
| neutrophil count | neutrophil cell count in units of 10^3/uL at the time of the image |
| lymphocyte count | lymphocyte cell count in units of 10^3/uL at the time of the image |
| view | Posteroanterior (PA), Anteroposterior (AP), AP Supine (APS), or Lateral (L) for X-rays; Axial or Coronal for CT scans. Translations: Bettaufnahme->Supine, Liegend->Supine|
| modality | CT, X-ray, or something else |
| date | Date on which the image was acquired |
| location | Hospital name, city, state, country |
| filename | Name with extension |
| doi | Digital object identifier ([DOI](https://en.wikipedia.org/wiki/Digital_object_identifier)) of the research article |
| url | URL of the paper or website where the image came from |
| license | License of the image such as CC BY-NC-SA. Blank if unknown |
| clinical notes | Clinical notes about the image and/or the patient |
| other notes | e.g. credit |

Within the finding field, the following mappings have been used to simplify the findings in the source:

|       Original Finding        |       Simplified Finding      |
|       ------------------      |       -------------------     |
| Tuberculous spondylodiscitis | Spinal Tuberculosis |
| No Finding | No Finding |
| COVID-19 | COVID-19 |
| Swine-Origin Influenza A (H1N1) Viral Pneumonia | Swine-Origin Influenza A (H1N1) Viral Pneumonia |
| Complicated Legionnaires' disease. | Legionella |
| No Finding | No Finding |
| Disseminated "miliary" tuberculosis during biologic (adalimumab) treatment for Crohn's disease | Tuberculosis |
| Invasive Aspergillosis and Aspergilloma causing Pneumopericardium. | Invasive Aspergillosis |
| Herpes pneumonia and ARDS | "Herpes pneumonia" or "Herpes pneumonia, ARDS" based on sequence
| Acute Respiratory Distress Syndrome: a Sequela of Asphyxiation Injury | ARDS |
| ARDS secondary to fat embolism | ARDS |
| Accelerated Phase Usual Interstitial Pneumonia | Accelerated Phase Usual Interstitial Pneumonia |
| Cystic form of pneumocystis jirovecii pneumonia. | Pneumocystis |
| Round pneumonia | Round pneumonia |
| Pneumocytis jiroveci pneumonia | Pneumocystis |
| Lymphocytic interstitial pneumonia | Lymphocytic interstitial pneumonia |
| Idiopathic cryptogenic organizing pneumonia (COP) | Cryptogenic Organizing Pneumonia |
| Streptococcus pneumonia and multiple pulmonary emboli | Streptococcus |
| Fire-eater's pneumonia. | Lipoid |
| Allergic bronchopulmonary aspergillosis | Allergic bronchopulmonary aspergillosis |
| Cryptogenic organising pneumonia | Cryptogenic organising pneumonia |
| Chronic eosinophilic pneumonia | Chronic eosinophilic pneumonia |
| Aspiration pneumonia | Aspiration pneumonia |
| Pneumocystis Jirovecci Infection in an HIV patient. | Pneumocystis |
| Endobronchial tuberculosis (EBTB). | Tuberculosis |
| Endobronchial spread of tuberculosis. | Tuberculosis |
| Hydropneumothorax as the initial manifestation of postprimary tuberculosis. | Tuberculosis |
| Pulmonary nocardia infection in HIV | Nocardia |
| Empyema necessitans as manifestation of tuberculosis | Tuberculosis |
| MERS-CoV | MERS |
| Tuberculosis with consolidation | Tuberculosis |
| Klebsiella pneumonia | Klebsiella |
| Acute eosinophilic pneumonia | Eosinophilic pneumonia |
| Miliary tuberculosis | Tuberculosis |
| Bilateral pulmonary nodules - tuberculous granulomas | Tuberculosis |
| Pneumonia in transplant lungs (description mentions Mycoplasma) | Mycoplasma Bacterial Pneumonia |
| Tuberculosis - left upper lobe | Tuberculosis |
| Cavitating pneumonia - lingular segments | Pneumonia |
| Community acquired methicillin resistant staphylococcus aureus pneumonia | MRSA |
| Streptococcus | Pneumococcal pneumonia |
| Klebsiella pneumonia causing a bulging fissure | Klebsiella |
| Tree-in-bud caused by haemophilus influenzae | Influenza |
| Right middle lobe pneumonia | Pneumonia |
| Left lower lobe pneumonia | Pneumonia |
| Silhouette sign of Felson: right middle lobe pneumonia | Pneumonia |
| Left lower lobe pneumonia | Pneumonia |

When the view field is provided in the text/image, but is not explicit, the following mappings have been used:

| Original view | Simplified view |
| ------------- | --------------- |
| (AP) (Mobile) Sitting | AP |
| (AP) Seduto | AP |
| (AP) Seduto a letto | AP |
| (AP) (Mobile) AP Semi-Erect | AP |
| (AP) (Mobile) Semi-Erect | AP |
| (AP) Semiseduto | AP |
| (AP) (Mobile) Supine | AP Supine |
| (AP) Supino | AP Supine |
| SUP | AP Supine |
| Semi-Supine | AP Supine |
