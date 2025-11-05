import logging
from datetime import datetime

import xarray as xr

logger = logging.getLogger(__name__)


def safe_open_dataset(path):
    """Open .netcdf file with best backend available."""
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
    """
    dt = datetime.strptime(date, "%Y%m%d%H%M%S")
    iso_date = dt.isoformat()
    return iso_date


def check_velocity_cop(ds: xr.Dataset):
    """
    Check if velocity pairs (u,v) are available in dataset.
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
