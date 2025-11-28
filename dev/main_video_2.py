"""
Develloper playground for a video utilitary.

Notes
-----
- For now, it is based only on MTG FCI L1c (High Res) EUMETSAT products.
- Will be extended to other type of datas.
"""

import logging
import os
import glob
import sys
from datetime import datetime
from pathlib import Path
import shutil

import numpy as np
import rioxarray
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from visusat.utils import parse_isodate
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
logger.info(">>> Dev script started.")

# --- Get the files in "movie" directory ---
movie_dir = '/Users/nicolassasso/Documents/Python_projects/VisuSat/outputs/movie/Benjamin2'

path = animate_geotiff_sequence(movie_dir)

logger.info(">>> End of script.")



