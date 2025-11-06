import logging
import os
import numpy as np
import sys
from datetime import datetime, timedelta
from pathlib import Path
from src.eumetsat_products_registry import *
from src import copernicus
from src import utils
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.axes_grid1 import make_axes_locatable

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
    dataset_id="cmems_mod_glo_phy_anfc_0.083deg_PT1H-m",
    variables=["so", "thetao", "uo", "vo", "zos"],
    minimum_longitude=-180,
    maximum_longitude=179.91668701171875,
    minimum_latitude=-80,
    maximum_latitude=90,
    start_datetime="2025-10-27T12:00:00",
    end_datetime="2025-10-27T15:00:00",
    minimum_depth=0.49402499198913574,
    maximum_depth=0.49402499198913574,
    output_filename="output_(1).nc",
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
    output_filename="globaloceanidentifier_oct2025.nc",
)

ds = copernicus.get_copdataset(request, force=False)


# Gradient de Sea Level Altitude: identifier les zones à forts gradients (instables, forte houle potentielle)
# Setup projection and colormap :
proj = ccrs.Mollweide()
cmap = "jet"
# Compute gradient of SLA field :
lon = ds.sla.longitude
lat = ds.sla.latitude
LON, LAT = np.meshgrid(lon,lat)
dsla_dlat, dsla_dlon = np.gradient(ds.sla.squeeze(),np.diff(lat)[0],np.diff(lon)[0])

grad = np.sqrt(dsla_dlon**2 + dsla_dlat**2)

# Display gradients global field :
copernicus.plot_field(
    lon,
    lat,
    dsla_dlat,
    cbar_label="(m/$^{\circ}$)",
    cmap = cmap,
    title="Gradient of Sea Level Altitude as a function of Latitude",
    proj=proj,
)
copernicus.plot_field(
    lon,
    lat,
    dsla_dlon,
    cmap=cmap,
    cbar_label="(m/$^{\circ}$)",
    title="Gradient of Sea Level Altitude as a function of Longitude",
)
domain = [-10, 12, 40.0, 60] 


copernicus.plot_field(
    lon,
    lat,
    grad,
    cmap=cmap,
    subdomain=domain,
    cbar_label="(m/$^{\circ}$)",
    title="Gradient norm of Sea Level Anomaly",
)

# Plot fields from copernicus dataset request :
copernicus.plot_copdataset(request, ds)

# copernicus.plot_currents(request, ds, vectors = False)
# copernicus.plot_currents(request, ds, domain = [-100,-60,0,30], vectors = True)

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
    "end_year": ["2030"],
}

# Download dataset
ds = copernicus.get_dataset(dataset, request)


logger.info("End program.")
