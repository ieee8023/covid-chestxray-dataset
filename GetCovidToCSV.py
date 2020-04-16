'''
This code creates a CSV format of data set with resized images of your defined size (Height, Width)
We got labels for every image from metadata.csv and in new creted dataset, first attribute defines the label
label == 1 defines COVID-19 and Label == 0 defines all others
Since Excel contains XFD as last column and XFD equals 16384. Thus we have to look for the resized height and width
In this example we took 40 x 40 with 3 channels making total row size (40x40x3)+1 +1 is added because label is stored as first attribute of image

'''
import numpy as np
import pandas as pd
import csv
from keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt


#Defining image size
Height = 40
Width = 40


#defining dataset dir
DATASET_DIR = "./dataset/Images/" #Define paths as per your environment
metadata = "./dataset/metadata/metadata.csv" # Meta info - path to metadata file


# Resizing Training data images to 40 x 40
train_datagen = ImageDataGenerator()
train_generator = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=(Height, Width),
    batch_size=1,
    class_mode='binary',
    subset='training')


#Getting Labels
metadata_csv = pd.read_csv(metadata)
labels = []
for file in train_generator.filenames:
    for (x, row) in metadata_csv.iterrows():
        file_name = 'images\\'+ row["filename"] #file contains the directory path 'images\' as well. Thus prefixing images\ to row['filename'] for comparison
        if file_name == file:
            label = row['finding']
            if label == "COVID-19":
                label = 1 #label == 1 defines COVID-19
            else:
                label = 0
            break
    labels.append(label)

print('Total Images: ',len(labels))


#Writting pixel values to CSV file
with open('mydata.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    for i in range(len(train_generator)):
        image, label = train_generator[i]
        image = image.reshape(Height*Width*3) # Reshaping into single list
        label = labels[i]     
        row = [label] #Writting label as first element of the row 
        for i in range(len(image)): #Iterating over Height
            row.append(image[i]) #Adding all pixels of an image in a single row after the label
        writer.writerow(row)

print("CSV data genereated sucessfully !");


# Plot the first image from the input dataset to be sure that data is correctly transformed
#============================================================
# Take a single image, and remove the color dimension by reshaping
imgSize = Height*Width*3 + 1 #We used first element as label
image = row[1:imgSize] #Taking Image pixels from element 2
image = np.array(image)
image = image.reshape(Height,Width,3)


#Plotting here
plt.figure()
plt.imshow(image.astype(int), cmap=plt.cm.binary)
plt.colorbar()
plt.grid(False)
plt.title('First Image')
plt.show()

