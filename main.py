
from pathlib import Path
import os,sys
import eumdac
import json
import logging
import cartopy
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import h5py
import hdf5plugin
from src import eumetsat
from datetime import datetime, timedelta

from satpy import Scene
from satpy import find_files_and_readers


# Basic Logging configuration
LOG_FILE = Path(__file__).with_suffix('.log')
script_name = os.path.basename(__file__)
#logger = logging.getLogger(script_name)

logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8", mode="w"),  # log dans un fichier
        logging.StreamHandler(sys.stdout)  # log aussi dans la console
    ],
    # crucial if VSCode or Ipython already touched the logging
    force=True
)
# Name of the logger :
logger = logging.getLogger(Path(__file__).stem)

logger.info("Program launched.")

start_time = datetime.utcnow() - timedelta(hours=6)
end_time = datetime.utcnow() - timedelta(hours=2)

# Collection required :
required_collection = "EO:EUM:DAT:0677" # FCI AllSky radiance Level2 product
output_files = eumetsat.download_data(required_collection, start_time, end_time, last = True)



for file in output_files:
    eumetsat.plot(file, required_collection)


logger.info('End program.')
