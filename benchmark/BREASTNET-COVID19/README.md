# BREASTNET-COVID19

## Technical Summary
- ### Light & Hard Data Augmentation
- ### BreastNet Model
- ### SGDR Learning Rate Scheduler
- ### Stratified 3-FOLD Training

## Results
BreastNet model was trained on "covid-chestxray-dataset" as multiclass.
- #### Best Scored Fold Results in Unseen Test Dataset - Confusion Matrix - Original Multiclass
<img src="results/Confusion Matrix - 2. FOLD (BEST) - Multiclass.jpg">

- #### Best Scored Fold Results in Unseen Test Dataset - Confusion Matrix - Binary (Converted from Multiclass predictions[COVID19, OTHER])
<img src="results/Confusion Matrix - 2. FOLD - Binary.jpg">

- #### Best Scored Fold Training and Validation Graphs from Tensorboard
<img src="results/Model Accuracy Graph - 2. Fold.png">
<img src="results/Model Loss Graph - 2. Fold.png">
