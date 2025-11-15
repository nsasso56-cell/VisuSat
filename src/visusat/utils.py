"""
Utils module
============

Utility functions for consistent and robust handling of satellite and oceanographic data.

This module provides a collection of helper routines used across the VisuSat
package. These utilities include:

- Safe opening of NetCDF files using several possible backends 
  (``safe_open_dataset``),
- Conversion of compact timestamp strings into ISO 8601 format (``isodate``),
- Detection of velocity component variable names in Copernicus Marine datasets
  (``check_velocity_cop``),
- Escaping of LaTeX-sensitive characters for Matplotlib labels (``str_replace``),
- General-purpose functions used by plotting and data-access routines.

The goal of this module is to centralize small but essential operations to keep
the rest of the codebase clean, consistent, and resilient across various data
sources (EUMETSAT, CMEMS, CDSAPI, etc.).
"""
from __future__ import annotations

# --- Standard Library --- 
import logging
from datetime import datetime
from pathlib import Path

# --- Madantory third-party dependencies --- 
import numpy as np
import xarray as xr

# --- Optional heavy dependencies (imported safely for RTD and minimal installs) ---
try:
    import matplotlib
    import matplotlib.pyplot as plt
except Exception:  
    matplotlib = None
    plt = None

# --- Matplotlib config (conditional) ---
if matplotlib is not None:
    matplotlib.rcParams["figure.dpi"] = 200
    matplotlib.rcParams.update(
        {"text.usetex": False, "font.family": "serif", "font.size": 10}
    )

# --- Logger ---
logger = logging.getLogger(__name__)

# --- Project paths ---
project_root = Path(__file__).resolve().parent.parent.parent


def safe_open_dataset(path):
    """
    Open a NetCDF file using the first available compatible backend.

    This function attempts to open the dataset sequentially using several
    xarray-compatible NetCDF engines. This is useful because different
    datasets may require different backends depending on how the file was
    encoded (NetCDF3, NetCDF4/HDF5, CF conventions, etc.).

    The engines are tested in the following order:
      1. ``h5netcdf``
      2. ``netcdf4``
      3. ``scipy``

    The first successful engine is used to load and return the dataset.
    If none of the engines works, a ``RuntimeError`` is raised.

    Parameters
    ----------
    path : str or path-like
        Path to the input NetCDF file.

    Returns
    -------
    xarray.Dataset
        The opened dataset.

    Raises
    ------
    RuntimeError
        If none of the available backends can open the file.

    Notes
    -----
    - ``h5netcdf`` is often the fastest backend and works well with modern
      NetCDF4/HDF5 files.
    - ``scipy`` can only read classic NetCDF3 files.
    - This function logs which backend succeeded or failed.
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
    Convert a timestamp string formatted as ``YYYYMMDDHHMMSS`` into ISO 8601 format.

    Parameters
    ----------
    date : str
        Timestamp expressed as a 14-digit string, e.g. ``"20250113123000"``.

    Returns
    -------
    str
        The corresponding ISO 8601 date-time string, e.g. ``"2025-01-13T12:30:00"``.

    Raises
    ------
    ValueError
        If the input string does not match the expected ``YYYYMMDDHHMMSS`` format.

    Notes
    -----
    This helper function is typically used to format metadata extracted from
    satellite or model filenames.
    """
    dt = datetime.strptime(date, "%Y%m%d%H%M%S")
    iso_date = dt.isoformat()
    return iso_date


def check_velocity_cop(ds: xr.Dataset):
    """
    Detect available ocean velocity components in a Copernicus Marine dataset.

    The function inspects the dataset to determine whether a valid pair of 
    horizontal velocity variables is present. Several common CMEMS conventions
    are checked, including:

    - ``("ugos", "vgos")`` : geostrophic currents from altimetry
    - ``("uo", "vo")`` : total ocean currents from reanalyses or models
    - ``("eastward_velocity", "northward_velocity")`` : alternative naming

    The first matching pair is returned. If no valid pair is found, a 
    ``KeyError`` is raised with a list of available variables.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset in which to search for velocity component variables.

    Returns
    -------
    tuple of str
        A tuple ``(u_var, v_var)`` giving the names of the detected
        eastward and northward velocity variables.

    Raises
    ------
    KeyError
        If no known velocity variable pair is present in ``ds``.

    Notes
    -----
    This helper function is mainly used by plotting routines to ensure that
    the correct velocity fields are extracted regardless of dataset naming 
    conventions.
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


def str_replace(text):
    """
    Escape LaTeX-sensitive characters in a string for safe use in Matplotlib labels.

    This function replaces certain special characters that conflict with
    Matplotlib's LaTeX rendering engine (e.g. the percent symbol ``%``), making
    the string safe to use in figure titles, axis labels, or annotations.

    Parameters
    ----------
    text : str
        Input string to sanitize for LaTeX compatibility.

    Returns
    -------
    str
        A LaTeX-safe version of the input string.

    Notes
    -----
    - Currently only escapes the percent symbol (``%``).
    - The function can be extended to support more LaTeX-sensitive characters.
    """
    new_str = text.replace("%", "\%")
    return new_str


def stats_dataset(data: xr.DataArray, cmap="viridis"):
    """
    Compute and display basic statistical histograms for a geospatial dataset.

    This function generates three diagnostic plots for a given
    ``xarray.DataArray``:

    1. A 1D histogram of the data values, filtered between the 1st and 99th
       percentiles to reduce the influence of outliers.

    2. A 2D histogram of longitude vs. data values, useful for identifying
       longitudinal biases or zonal structures.

    3. A 2D histogram of data values vs. latitude, useful for detecting
       latitudinal patterns.

    Pixels outside the percentile-based threshold are removed before plotting.
    NaN values are automatically masked.

    Parameters
    ----------
    data : xarray.DataArray
        Input geospatial field. Must contain coordinates ``x`` (longitude) and
        ``y`` (latitude), and ideally attributes ``long_name`` and ``unit`` for
        axis labeling.
    cmap : str, optional
        Colormap used for the 2D histograms. Defaults to ``"viridis"``.

    Returns
    -------
    None
        The function produces diagnostic figures but does not return any object.

    Notes
    -----
    - Outlier filtering uses the 1st and 99th percentiles of the dataset.
    - The 2D histograms use flattened grids and ignore missing values.
    - Useful as an initial visual inspection or quality check of CMEMS or model fields.
    """
    if plt is None:
        raise ImportError(
            "stats_dataset() requires matplotlib.\n"
            "Install it with: pip install visusat[full]"
        )

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
