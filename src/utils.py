import logging
from datetime import datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)
project_root = Path(__file__).resolve().parent.parent

matplotlib.rcParams["figure.dpi"] = 200
matplotlib.rcParams.update(
    {"text.usetex": True, "font.family": "serif", "font.size": 10}
)


def safe_open_dataset(path):
    """
    Open .netcdf file with best backend available.
    Inputs : path (str)
    """
    for engine in ("h5netcdf", "netcdf4", "scipy"):
        try:
            ds = xr.open_dataset(path, engine=engine)
            logger.info(f"Open with engine '{engine}'")
            return ds
        except Exception as e:
            logger.warning(f" Fail with engine '{engine}': {e}")
    raise RuntimeError("No compatible backend for this file.")


def isodate(date):
    """
    Returns the isoformat of a date.
    Inputs : - date (datetime).
    Returns : iso_date (str), isoformat of specified date.
    """
    dt = datetime.strptime(date, "%Y%m%d%H%M%S")
    iso_date = dt.isoformat()
    return iso_date


def check_velocity_cop(ds: xr.Dataset):
    """
    Check if velocity pairs (u,v) are available in dataset.
    Inputs :
        - ds (xr.Dataset) : xarray dataset
    """
    possible_pairs = [
        ("ugos", "vgos"),  # geostrophic winds from altimetry
        ("uo", "vo"),  # total winds from models
        ("eastward_velocity", "northward_velocity"),  # sometimes from CMEMS
    ]

    for u_var, v_var in possible_pairs:
        if u_var in ds and v_var in ds:
            logging.info(f"✅ Velocity variables detected : {u_var}, {v_var}")
            return u_var, v_var

        msg = (
            "❌ No velocity variable found in dataset.\n"
            "Variables available : " + ", ".join(list(ds.data_vars))
        )
    logging.error(msg)
    raise KeyError("Missing velocitty variables in dataset. (uo/vo or ugos/vgos).")


def str_replace(str):
    """
    Replace some string components in a Latex-friendly way, useful for labels in matplotlib figures for instance.
    """
    new_str = str.replace("%", "\%")
    return new_str


def stats_dataset(data: xr.DataArray, cmap="viridis"):
    """
    Compute and display basic histograms for a geographic dataset.
    Inputs : - data (xr.DataArray)
    """
    logger.info("Beginning computation and plotting of dataset statistics...")

    low, high = np.nanpercentile(data, [1, 99])
    data_filtered = data.where((data >= low) & (data <= high))
    # fig, ax = plt.subplots(figsize=(8, 8))
    data_filtered.plot.hist(bins=50)

    # plt.show()

    # LON,LAT = np.meshgrid(data.x.values.flatten(), data.y.values.flatten())
    # lon = data.x.values.flatten()
    low, high = np.nanpercentile(data, [1, 99])
    data_filtered = data.where((data >= low) & (data <= high))
    val = data_filtered.values.flatten()
    LON, LAT = np.meshgrid(
        data_filtered.x.values.flatten(), data_filtered.y.values.flatten()
    )

    mask = ~np.isnan(LON.flatten()) & ~np.isnan(val)
    LON_clean = LON.flatten()[mask.flatten()]
    val_clean = val.flatten()[mask.flatten()]

    fig, ax = plt.subplots(figsize=(8, 8))
    plt.hist2d(LON_clean, val_clean, bins=(50, 100), cmap=cmap)
    plt.ylabel(f"{data.long_name}\n({data.unit}) ")
    plt.xlabel("Longitude (°)")
    plt.colorbar(label="Counts")
    # plt.show()

    mask = ~np.isnan(LAT.flatten()) & ~np.isnan(val)
    LAT_clean = LAT.flatten()[mask.flatten()]
    val_clean = val.flatten()[mask.flatten()]

    fig, ax = plt.subplots(figsize=(8, 8))
    plt.hist2d(val_clean, LAT_clean, bins=(100, 50), cmap=cmap)
    plt.xlabel(f"{data.long_name}\n({data.unit}) ")
    plt.ylabel("Lattiude (°)")
    plt.colorbar(label="Counts")
    # plt.show()
