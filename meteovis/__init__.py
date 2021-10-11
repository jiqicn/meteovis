from .meteovis import *
from .dataset import *
from .view import *
from .control import *

import os


if __import__("meteovis"):
    # get the current working directory
    cwd = os.getcwd()
    
    if not os.path.exists(DATASET_DIR):
        os.mkdir(DATASET_DIR)
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)