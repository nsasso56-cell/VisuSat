"""
Developer playground for VisuSat.

This script is NOT part of the official package.
Use it to test features locally without polluting the library API.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import shutil

import eumdac
import matplotlib.pyplot as plt
import rioxarray

from visusat.eumetsat import download_custom_products, get_token
from visusat.eumetsat_products_registry import load_registry, PRODUCTS

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
LOG_FILE = Path(__file__).with_suffix(".log")
script_name = os.path.basename(__file__)
logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8", mode="w"),  
        logging.StreamHandler(sys.stdout), 
    ],
    force=True,
)
logger = logging.getLogger(Path(__file__).stem)
logger.info(">>> Dev script started.")

# Collection required :
load_registry()
required_collection = "EO:EUM:DAT:0665" 
product = PRODUCTS[required_collection]

# ===============================================================
# Authenticate & search Data Store product
# ===============================================================
token = get_token()
datastore = eumdac.DataStore(token)

collection = datastore.get_collection(required_collection)

start = datetime(2025, 10, 22, 12, 00)
end = datetime(2025, 10, 22, 18, 00)

products = collection.search(dtstart=start, dtend=end)


if products is None:
    raise RuntimeError("No matching products found in this time window.")

# ===============================================================
# Define Data Tailor chain
# ===============================================================
chain = eumdac.tailor_models.Chain(
    product="FCIL1HRFI",
    format="geotiff",
    filter={"bands": ["vis_06_hr_effective_radiance"]},
    projection="geographic",
    roi="western_europe",
)

# --- Make "movie" dir in outputs ---
movie_dir = '/Users/nicolassasso/Documents/Python_projects/VisuSat/outputs/movie/Benjamin2'

download_custom_products(products, chain, movie_dir)




