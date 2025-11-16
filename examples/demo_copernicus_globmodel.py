"""
Example — CMEMS Global Physical Model (ANFC) extraction & plotting.

This example demonstrates:
    - how to request a single-depth subset of the 1/12° global model,
    - how to download and open the dataset using VisuSat,
    - how to plot scalar fields (SST, Salinity, SSH...),
    - how to plot ocean surface currents.

Logs are saved both to the terminal and to a .log file.
"""

import logging
import os
import sys
from pathlib import Path

from visusat import copernicus

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

# ---------------------------------------------------------------------------
# Copernicus request — CMEMS GLOBAL 1/12° physical model (ANFC)
# ---------------------------------------------------------------------------

request = copernicus.CopernicusRequest(
    dataset_id="cmems_mod_glo_phy_anfc_0.083deg_PT1H-m",
    variables=["so", "thetao", "uo", "vo", "zos"], # salinity, temp, u, v, SSH
    minimum_longitude=-180,
    maximum_longitude=179.91668701171875,
    minimum_latitude=-80,
    maximum_latitude=90,
    start_datetime="2025-10-27T12:00:00",
    end_datetime="2025-10-27T12:00:00",
    minimum_depth=None, # (surface layer by default)
    maximum_depth=None,
    output_filename="glo_anfc_surface_20251027.nc",
)
logger.info("Request initialised.")

# ---------------------------------------------------------------------------
# Download + Open dataset
# ---------------------------------------------------------------------------
ds = copernicus.load_dataset(request, force=False)
logger.info(f"Dataset opened successfully:\n{ds}")

# ---------------------------------------------------------------------------
# Plot all scalar fields
# ---------------------------------------------------------------------------
logger.info("Plotting scalar variables (temperature, salinity, SSH)...")
copernicus.plot_fields(request, ds)

# ---------------------------------------------------------------------------
# Plot currents
# ---------------------------------------------------------------------------
logger.info("Plotting global currents...")
copernicus.plot_currents(request, ds, vectors = False)

logger.info("Plotting currents over Mexican Golfe (with vectors)...")
copernicus.plot_currents(request, ds, domain = [-100,-60,0,30], vectors = True)

logger.info(">>> Example script completed successfully.")
