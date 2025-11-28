"""
Example script to produce an animation from EUMETSAT products download through Data Tailor customisation.

This example shows :
- Authentication with EUMETSAT credentials.
- Product search on a specific temporal window.
- Definition of Data Tailor Chain.
- Use of ``download_custom_products`` to automatize Data Tailor customisation for
multiple products.
- Generation of animation with ``animate_geotiff_sequence``.

Requirements:
pip install visusat numpy eumdac
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import eumdac
import numpy as np

from visusat.eumetsat import download_custom_products, get_token
from visusat.plotting import animate_geotiff_sequence


def get_lonlat(ds):
    """Return 2D lon/lat arrays from a rioxarray dataset."""
    bounds = ds.rio.bounds()
    minx, miny, maxx, maxy = bounds
    ny, nx = ds.shape[-2:]

    lon = np.linspace(minx, maxx, nx)
    lat = np.linspace(miny, maxy, ny)
    lon2d, lat2d = np.meshgrid(lon, lat)
    return lon2d, lat2d, [minx, maxx, miny, maxy]


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
logger.info(">>> Example script started.")

# ===============================================================
# Authenticate & search Data Store product
# ===============================================================
token = get_token()
datastore = eumdac.DataStore(token)
required_collection = "EO:EUM:DAT:0665"  # MTG FCI L1c HR
collection = datastore.get_collection(required_collection)

start = datetime(2025, 10, 22, 12, 00)
end = datetime(2025, 10, 22, 12, 30)

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

# ===============================================================
# Download series of custom products in target directory
# ===============================================================
dir = "../outputs/animations/test"
download_custom_products(products, chain, dir)

# ===============================================================
# Produce animation within the target directory
# ===============================================================
path = animate_geotiff_sequence(dir, cmap="Blues")

logger.info(">>> End of example script.")
