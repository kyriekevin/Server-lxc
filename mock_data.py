import pandas as pd
import numpy as np
from io import StringIO

# Mock data as CSV for ground truth (GT) and inference results
gt_csv = """image_id,x1,y1,x2,y2,defect_type
image1,10,10,50,50,defect1
image1,60,60,100,100,defect2
image2,15,15,55,55,defect1
image2,65,65,105,105,defect2
"""

inference_csv = """image_id,x1,y1,x2,y2,defect_type,inference_time
image1,12,14,51,49,defect1,0.03
image1,59,61,99,101,defect2,0.03
image2,16,17,53,54,defect1,0.04
image2,63,64,104,106,defect2,0.04
"""

# Write the mock data to CSV files for demonstration purposes
gt_file_path = "./gt.csv"
inference_file_path = "./inference.csv"

# Save the GT CSV to a file
with open(gt_file_path, "w") as file:
    file.write(gt_csv)

# Save the inference CSV to a file
with open(inference_file_path, "w") as file:
    file.write(inference_csv)
