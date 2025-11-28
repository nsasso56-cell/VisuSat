"""
Utils module
============

Utility functions for consistent and robust handling of satellite and oceanographic data.

This module provides a collection of helper routines used across the VisuSat
package. These utilities include:

- Safe opening of NetCDF files using several possible backends
  (``safe_open_dataset``),
- Conversion of compact timestamp strings into ISO 8601 format (``parse_isodate``),
- Detection of velocity component variable names in Copernicus Marine datasets
  (``detect_velocity_vars``),
- Escaping of LaTeX-sensitive characters for Matplotlib labels (``escape_latex``),
- Compute and display basic statistical histograms for a geospatial dataset (``plot_dataset_stats``).
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
from typing import Tuple

# --- Madantory third-party dependencies ---
import numpy as np
import pandas as pd


# --- Optional heavy dependencies (imported safely for RTD and minimal installs) ---
def _require_xarray():
    try:
        import xarray as xr
    except ImportError as exc:
        raise ImportError(
            "xarray is required for dataset utilities in visusat.utils."
        ) from exc
    return xr


def _require_matplotlib():
    try:
        import matplotlib
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "Matplotlib is required for plotting in visusat.utils."
        ) from exc
    return matplotlib, plt


# --- Logger ---
logger = logging.getLogger(__name__)

# --- Public API ---------------------------------------------------------------
__all__ = [
    "escape_latex",
    "parse_isodate",
    "safe_open_dataset",
    "detect_velocity_vars",
    "plot_dataset_stats",
]

# --- Project paths ---
project_root = Path(__file__).resolve().parent.parent.parent


# ------------------------------------------------------------------------------
# STRING UTILITIES
# ------------------------------------------------------------------------------
def escape_latex(text: str) -> str:
    """
    Escape LaTeX-sensitive characters in a string.


    Parameters
    ----------
    text : str
        Input string to sanitize for LaTeX compatibility.

    Returns
    -------
    str
        Escaped string, safe to use in LaTeX environments.

    Notes
    -----
    - Currently only escapes the percent symbol (``%``).
    - The function can be extended to support more LaTeX-sensitive characters.
    """
    return text.replace("%", "\%")


# ------------------------------------------------------------------------------
# TIME UTILITIES
# ------------------------------------------------------------------------------


def parse_isodate(date) -> str:
    """
    Convert different date-like objects into a clean ISO8601 string.

    Accepted inputs:
        - numpy.datetime64
        - pandas.Timestamp
        - datetime.datetime
        - str (ISO8601 or compact YYYYMMDDhhmmss)

    Parameters
    ----------
    date : Any
        Date or datetime-like object to be converted.

    Returns
    -------
    str
        The corresponding ISO 8601 date-time string, e.g. ``"2025-01-13T12:30:00"``.

    Raises
    ------
    ValueError
        If the input value cannot be interpreted as a valid date.

    Notes
    -----
    This helper function is typically used to format metadata extracted from
    satellite or model filenames.
    """
    # 1) pandas Timestamp (common with xarray)
    if isinstance(date, pd.Timestamp):
        return date.isoformat()

    # 2) numpy.datetime64 → convert using pandas
    if isinstance(date, np.datetime64):
        return pd.Timestamp(date).isoformat()

    # 3) Already a datetime object
    if isinstance(date, datetime):
        return date.isoformat()

    # 4) String already ISO
    if isinstance(date, str):
        # If already ISO-like
        if "T" in date:
            return date

        # Try compact format YYYYMMDDHHMMSS
        for fmt in ("%Y%m%d%H%M%S", "%Y%m%d"):
            try:
                return datetime.strptime(date, fmt).isoformat()
            except ValueError:
                pass

        raise ValueError(f"Unrecognized date string format: {date}")

    raise TypeError(f"Unsupported date type: {type(date)}")


# ------------------------------------------------------------------------------
# DATASET LOADING
# ------------------------------------------------------------------------------


def safe_open_dataset(path: str | Path):
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
    path : str or Path
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
    # --- Third party dependencies ---
    xr = _require_xarray()

    engines = ("h5netcdf", "netcdf4", "scipy")
    for engine in engines:
        try:
            ds = xr.open_dataset(path, engine=engine)
            logger.info(f"Open with engine '{engine}'")
            return ds
        except Exception as e:
            logger.warning(f" Fail with engine '{engine}': {e}")

    raise RuntimeError(
        f"Could not open dataset {path}. No compatible backend for this file."
    )


# ------------------------------------------------------------------------------
# COPERNICUS / OCEAN VELOCITY UTILITIES
# ------------------------------------------------------------------------------


def detect_velocity_vars(ds: "xr.Dataset") -> Tuple[str, str]:
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
    (str, str)
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
            logging.info(f"Velocity variables detected : {u_var}, {v_var}")
            return u_var, v_var

    valid_vars = ", ".join(ds.data_vars)
    raise KeyError(
        f"Missing velocitty variables in dataset. Available variable : {valid_vars}."
    )


# ------------------------------------------------------------------------------
# STATISTICS / DIAGNOSTICS
# ------------------------------------------------------------------------------
def plot_dataset_stats(data: "xr.DataArray", cmap: str = "viridis"):
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
    - Requires Matplotlib.
    - Does not call ``plt.show()`` (left to the user).
    - Outlier filtering uses the 1st and 99th percentiles of the dataset.
    - The 2D histograms use flattened grids and ignore missing values.
    - Useful as an initial visual inspection or quality check of CMEMS or model fields.
    """
    matplotlib, plt = _require_matplotlib()

    # --- Matplotlib config (conditional) ---
    if matplotlib is not None:
        matplotlib.rcParams["figure.dpi"] = 200
        matplotlib.rcParams.update(
            {"text.usetex": False, "font.family": "serif", "font.size": 10}
        )

    logger.info("Beginning computation and plotting of dataset statistics...")

    # --- Filter extremes ---
    low, high = np.nanpercentile(data, [1, 99])
    filtered = data.where((data >= low) & (data <= high))

    # --- 1D Histogram ---
    filtered.plot.hist(bins=50)

    # --- 2D Longitude vs Value ---
    if {"x", "y"}.issubset(filtered.coords):
        LON, LAT = np.meshgrid(filtered.x.values.flatten(), filtered.y.values.flatten())
        val = filtered.values.flatten()

        mask = ~np.isnan(val)

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.hist2d(LON.flatten()[mask], val[mask], bins=(50, 50), cmap=cmap)
        ax.set_ylabel(f"{data.long_name}\n({data.unit}) ")
        ax.set_xlabel("Longitude (°)")
        ax.colorbar(label="Counts")

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.hist2d(val[mask], LAT.flatten()[mask], bins=(50, 50), cmap=cmap)
        ax.xlabel(f"{data.long_name}\n({data.unit}) ")
        ax.ylabel("Lattiude (°)")
        ax.colorbar(label="Counts")
