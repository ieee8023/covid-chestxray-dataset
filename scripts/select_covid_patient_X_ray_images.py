'''
This code finds all images of patients of a specified VIRUS and X-Ray view and stores selected image to an OUTPUT directory
The specs are to be given in the virus_view dictionary. (key = virus value = list of desired views) 
+ It uses metadata.csv for searching and retrieving images name
+ Using ./images folder it selects the retrieved images and copies them into the output folder in a hierarchial format
+ All views for a virus are stored in outputDir/virusname/viewname/
+ During every extraction the previous output folder is cleared (if exists)
Code can be modified for any combination of selection of images
'''

import pandas as pd
import shutil
import os
import os.path

# Output Specs
virus_view = {"COVID-19":["PA"],"SARS":["AP","PA"]}
outputDir = '../output' # Output directory to store selected images

# Helper that creates a directory if it does not exist
def createdir(dir):
  if not os.path.exists(dir):
    os.mkdir(dir)	

# Helper to clear a directory 
def cleardir(dir):
    if os.path.exists(dir):
      shutil.rmtree(dir) 


metadata = "../metadata.csv" # Meta info
imageDir = "../images" # Directory of images


metadata_csv = pd.read_csv(metadata)

# Clear the previous extraction and create a new outdir
cleardir(outputDir)
createdir(outputDir)


for virus in virus_view:
  cur_outdir = outputDir + "/" + virus
  createdir(cur_outdir)
  for x_ray_view in virus_view[virus]:
    cur_viewdir = cur_outdir + "/" + x_ray_view
    createdir(cur_viewdir)
	# loop over the rows of the COVID-19 data frame
    for (i, row) in metadata_csv.iterrows():
      if row["finding"] != virus or row["view"] != x_ray_view:
        continue
      filename = row["filename"].split(os.path.sep)[-1]
      filePath = os.path.sep.join([imageDir, filename])
      shutil.copy2(filePath, cur_viewdir)
				