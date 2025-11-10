import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import eumdac
import matplotlib.pyplot as plt
import numpy as np
import rioxarray
import xarray as xr
from src import eumetsat, utils
from src.eumetsat_products_registry import *

# Basic Logging configuration
LOG_FILE = Path(__file__).with_suffix(".log")
script_name = os.path.basename(__file__)
# logger = logging.getLogger(script_name)

logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_FILE, encoding="utf-8", mode="w"
        ),  # log dans un fichier
        logging.StreamHandler(sys.stdout),  # log aussi dans la console
    ],
    # crucial if VSCode or Ipython already touched the logging
    force=True,
)
# Name of the logger :
logger = logging.getLogger(Path(__file__).stem)

logger.info("Program launched.")

# Collection required :
required_collection = "EO:EUM:DAT:0665"  # Registry in data/EUMETSAT_products_registry
# Load EUMETSAT products registry :
load_registry()
product = PRODUCTS[required_collection]


token = eumetsat.get_token()
# Create datatailor object with with your token
datatailor = eumdac.DataTailor(token)

datastore = eumdac.DataStore(token)
# Select an FCI collection, eg "FCI Level 1c High Resolution Image Data - MTG - 0 degree" - "EO:EUM:DAT:0665"
selected_collection = datastore.get_collection("EO:EUM:DAT:0665")

# Set sensing start and end time
start = datetime(2025, 1, 26, 19, 30)
end = datetime(2025, 1, 26, 23, 30)

# Retrieve latest product that matches the filter
product = selected_collection.search(dtstart=start, dtend=end).first()

# Define the chain configuration
chain = eumdac.tailor_models.Chain(
    product="FCIL1HRFI",
    format="geotiff",
    filter={"bands": ["ir_38_hr_effective_radiance"]},
    projection="geographic",
    roi="western_europe",
)

output_file, customisation = eumetsat.customisation(product, chain)
# output_file = '/Users/nicolassasso/Documents/Python_projects/VisuSat/data/eumetsat/custom/EO:EUM:DAT:0665/FCIL1HRFI-FPC-a0533003/FCIL1HRFI_20250126T232729Z_20250126T232919Z_epct_a0533003_FPC.tif'


# Open geotiff
ds = rioxarray.open_rasterio(output_file)

print(ds)

ds = ds.where(ds != ds.attrs.get("_FillValue", np.nan))

# Deal the error values
# for ib in range(len(ds.band)):
#    ds.isel(band=ib).values = ds.isel(band=ib).where(ds.isel(band=ib)!=ds._FillValue).values

data = ds.isel(band=0)

utils.stats_dataset(data, cmap="jet")


# Affichage
img = ds.isel(band=0)


plt.figure(figsize=(8, 8))
img.plot(vmin=-0.5, vmax=0, cmap="gray")
plt.title("Image GeoTIFF - Bande 1")
plt.show()

sys.exit()

output_files = eumetsat.download_data(
    required_collection, start_time, end_time, last=True
)

ds = xr.open_dataset(output_files[0])


for file in output_files:

    eumetsat.plot_amvs(file, product, display=False)

    eumetsat.plot_amvs(file, product, box=[-40, 20, 20, 80], display=False)

logger.info("End program.")
