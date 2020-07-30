import pandas as pd
import sys, os
import numpy as np
import os
from pathlib import Path

metadata = pd.read_csv("../metadata.csv")
images = sorted(Path("../images").iterdir(), key=os.path.getmtime, reverse=True)

header = """
<html><head>
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap-theme.min.css">
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
</head>
<body>
<div class="container">
"""

footer = "</div></body></html>\n"

with open("database.htm","w") as f:
    f.write(header)
    for i, image in enumerate(images):
        print(image.name)
        m = metadata[metadata.filename == image.name]
        if m.iloc[0].modality != "X-ray":
            continue
        f.write("<div class='row'>")
        
        f.write("<div class='col-sm-6'>")
        f.write("<center>{}</center>".format(image.name))
        f.write("<img style='width:100%' src='../images/{}'>".format(image.name))
        f.write("</div>")
        
        
        f.write("<div class='col-sm-6'>")
        f.write(m.T.to_html(classes="table small") + "\n")
        f.write("</div>")
        f.write("</div>")
        f.write("<hr>")
        if i > 10:
            break
    f.write(footer)

