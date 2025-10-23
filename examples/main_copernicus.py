import logging
import os
import sys
import xarray as xr
import cartopy
from datetime import datetime, timedelta
from pathlib import Path
from src.eumetsat_products_registry import *
from src import copernicus
import matplotlib.pyplot as plt

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

# Path to Registry path
REGISTRY_PATH = Path(
    os.path.join(
        Path(__file__).resolve().parent.parent, "data", "copernicus_datasets.json"
    )
)



request = copernicus.CopernicusRequest(
    dataset_id="cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
    variables=["sla", "err_sla", "flag_ice"],
    minimum_longitude=1,
    maximum_longitude=359,
    minimum_latitude=-71.81717698546082,
    maximum_latitude=82.52141057014119,
    start_datetime="2025-10-22T00:00:00",
    end_datetime="2025-10-22T00:00:00",
    output_filename="globaloceanidentifier_oct2025.nc"
)

ds = copernicus.get_copdataset(request)
print(ds)




sys.exit()


# COPERNICUS dataset required :
dataset = "projections-cordex-domains-single-levels"
request = {
    "domain": "europe",
    "experiment": "rcp_2_6",
    "horizontal_resolution": "0_11_degree_x_0_11_degree",
    "temporal_resolution": "daily_mean",
    "variable": ["2m_air_temperature"],
    "gcm_model": "cnrm_cerfacs_cm5",
    "rcm_model": "cnrm_aladin63",
    "ensemble_member": "r1i1p1",
    "start_year": ["2026"],
    "end_year": ["2030"]
}

# Download dataset
ds = copernicus.get_dataset(dataset,request)

logger.info("End program.")
