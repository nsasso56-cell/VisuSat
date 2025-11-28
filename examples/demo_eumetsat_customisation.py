"""
Example: Request a custom MTG-FCI product via EUMETSAT Data Tailor,
download the generated GeoTIFF, compute basic statistics, and plot the radiance.

This example demonstrates:
- Authentication using a local credential file,
- Product search on a temporal window,
- Submission and monitoring of a Data Tailor customisation,
- Reading GeoTIFF outputs with rioxarray,
- Basic radiance visualisation and statistics.

Requirements:
    pip install rioxarray matplotlib numpy
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import eumdac
import matplotlib.pyplot as plt
import rioxarray

from visusat import eumetsat, utils
from visusat.eumetsat_products_registry import PRODUCTS, load_registry

# ===============================================================
# Logging configuration
# ===============================================================
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
logger.info("Program launched.")

# Collection required :
load_registry()
required_collection = "EO:EUM:DAT:0665"
product = PRODUCTS[required_collection]

# ===============================================================
# Authenticate & search Data Store product
# ===============================================================
token = eumetsat.get_token()
datastore = eumdac.DataStore(token)

collection = datastore.get_collection(required_collection)

start = datetime(2025, 1, 26, 19, 30)
end = datetime(2025, 1, 26, 23, 30)

product = collection.search(dtstart=start, dtend=end).first()

if product is None:
    raise RuntimeError("No matching product found in this time window.")

logger.info(f"Found product: {product}")

# ===============================================================
# Define Data Tailor chain
# ===============================================================
chain = eumdac.tailor_models.Chain(
    product="FCIL1HRFI",
    format="geotiff",
    filter={"bands": ["ir_38_hr_effective_radiance"]},
    projection="geographic",
    roi="western_europe",
)
logger.info("Launching customisation request...")
output_file, customisation = eumetsat.customisation(product, chain)


# ===============================================================
# Read GeoTIFF using rioxarray
# ===============================================================
logger.info(f"Opening GeoTIFF: {output_file}")
ds = rioxarray.open_rasterio(output_file)

logger.info(ds)

# Replace FillValue by NaN if available
fill_value = ds.attrs.get("_FillValue", None)
if fill_value is not None:
    ds = ds.where(ds != fill_value)

band0 = ds.isel(band=0)

# ===============================================================
# Compute dataset statistics (custom util)
# ===============================================================
logger.info("Computing dataset statistics...")
utils.plot_dataset_stats(band0, cmap="jet")


# ===============================================================
# Display radiance image
# ===============================================================
plt.figure(figsize=(8, 8))
band0.plot(cmap="gray")
plt.title("MTG-FCI GeoTIFF radiance (Band 1)")
plt.tight_layout()
plt.show()

logger.info("End of program.")
