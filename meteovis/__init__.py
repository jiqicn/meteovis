from .meteovis import *
from .dataset import DATASET_DIR

import os


if __import__("meteovis"):
    # get the current working directory
    cwd = os.getcwd()
    
    if not os.path.exists(DATASET_DIR):
        os.mkdir(DATASET_DIR)