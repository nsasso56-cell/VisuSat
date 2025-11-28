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
movie_dir = '/Users/nicolassasso/Documents/Python_projects/VisuSat/outputs/movie/movie2'

# -------------------------------
# List and sort files by timestamp
# -------------------------------
geotiffs = [f for f in Path(movie_dir).iterdir() if f.suffix == ".tif"]

def extract_timestamp(file):
        # file pattern: NAME_YYYYMMDDhhmmss_YYYYMMDDhhmmss.tif
        parts = file.stem.split("_")
        return parse_isodate(parts[1])
geotiffs.sort(key=extract_timestamp)

# -------------------------------
# Load first frame → setup CRS & extent
# -------------------------------
first = rioxarray.open_rasterio(os.path.join(movie_dir, geotiffs[0])).isel(band=0)
fill_value = first.attrs.get("_FillValue", None)
if fill_value is not None:
    first = first.where(first != fill_value)

lon2d, lat2d, extent = get_lonlat(first)


# --- Get CRS + transform + extent ---
crs = first.rio.crs
transform = first.rio.transform()
width = first.rio.width
height = first.rio.height

x_min = transform[2]
y_max = transform[5]
x_max = x_min + transform[0] * width
y_min = y_max + transform[4] * height
extent2 = [x_min, x_max, y_min, y_max]

# -------------------------------
# Compute global min/max (percentile clip)
# -------------------------------
vmin, vmax = np.inf, -np.inf
for f in geotiffs:
    tmp = rioxarray.open_rasterio(os.path.join(movie_dir, f)).isel(band=0)
    # Replace FillValue by NaN if available
    fill_value = tmp.attrs.get("_FillValue", None)
    if fill_value is not None:
        tmp = tmp.where(tmp != fill_value)
    vmin = min(vmin, float(np.nanpercentile(tmp,1)))
    vmax = max(vmax, float(np.nanpercentile(tmp,99)))


# -------------------------------
# Setup figure for animation
# -------------------------------
# --- Definition of projection ---
proj = ccrs.PlateCarree()

fig, ax = plt.subplots(subplot_kw={"projection":proj}, figsize=(6, 6))
ax.set_extent(extent2, crs=proj)

im = ax.imshow(first, cmap="Blues", transform=proj, extent=extent, origin="upper", vmin=vmin, vmax=vmax)

# --- Colorbar ---
cbar = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.07, fraction=0.046, aspect=30)
cbar.set_label(f"{first.long_name}\n({first.unit})")

# --- Cosmetics ---
ax.coastlines(resolution="50m")
ax.add_feature(cfeature.BORDERS)
ax.add_feature(cfeature.LAND, facecolor="lightgray")
ax.set_xlabel("Longitude (°)")
ax.set_ylabel("Latitude (°)")
gl = ax.gridlines(
    draw_labels=True,
    linewidth=0.6,
    color="gray",
    alpha=1,
    linestyle="--"
)
gl.top_labels = False    
gl.right_labels = False

title = ax.set_title("Loading...")
fig.tight_layout()

# --------------------------
# Animation function
# --------------------------
def update(i):
    tif = geotiffs[i]
    
    arr = rioxarray.open_rasterio(tif).isel(band=0)
    if fill_value is not None:
        arr = arr.where(arr != fill_value)

    im.set_data(arr.values)

    parts = tif.stem.split("_")
    t1 = parse_isodate(parts[1])
    t2 = parse_isodate(parts[2])

    # Update title
    title.set_text(f"{arr.description}\n{t1} -> {t2}")

    return [im, title]

ani = animation.FuncAnimation(
    fig, update, frames=len(geotiffs),
    blit=False, interval=300
)

# --------------------------
# Save animation
# --------------------------
outfile = os.path.join(movie_dir, 'movie.gif')
ani.save(outfile, fps=2, dpi=200, writer='Pillow')
logger.info(f"Animation saved -> {outfile}")

logger.info(">>> End of script.")



