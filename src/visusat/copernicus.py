"""
Copernicus module
=================

Interface utilities for interacting with the Copernicus Marine Service (CMEMS).

This module provides high-level tools to define, execute, and process data
requests to the Copernicus Marine Data Store using the
``copernicusmarine`` Python client. It streamlines the creation of spatial,
temporal, and vertical subset requests, handles caching, and enables easy
post-processing through xarray.

Main features include:

- Construction of structured CMEMS subset requests through the
  :class:`~visusat.copernicus.CopernicusRequest` class,
- Execution of download requests with automatic output management
  (``CopernicusRequest.fetch``),
- Loading of downloaded datasets directly into xarray (``get_copdataset``),
- Plotting utilities for ocean surface and subsurface currents
  (``plot_currents``),
- Additional helpers to support CMEMS velocity variable detection and dataset
  inspection.

This module centralizes CMEMS-related operations to ensure consistent,
transparent, and reproducible oceanographic workflows within VisuSat.
"""

from __future__ import annotations

# --- Standard library ---
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# --- Mandatory third-party dependencies ---
import numpy as np
import pandas as pd
import xarray as xr



try:
    import cdsapi
except Exception:
    cdsapi = None  # allows the module to be imported without cdsapi installed

try:
    import copernicusmarine
except Exception:
    copernicusmarine = None  # allows docs to build without the library

# --- Local utilities ---
from .utils import safe_open_dataset, escape_latex, check_velocity_cop, isodate
from .plotting import plot_field

# --- Public API ---
__all__ = [
    "CopernicusRequest",
    "load_dataset",
    "plot_fields",
    "plot_currents",
]

# --- Logger ---
logger = logging.getLogger(__name__)

# --- Project paths ---
project_root = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.path.join(project_root, "data","copernicus"))
OUT_DIR = Path(os.path.join(project_root, "outputs", "copernicus"))

# ==============================================================================
# Dataclass for request
# ==============================================================================
@dataclass
class CopernicusRequest:
    """
    Build and manage a data extraction request to the Copernicus Marine Data Store.

    This class defines a complete subset request (spatial, temporal, vertical,
    and variable selection) and provides a convenient interface to download the
    corresponding dataset using ``copernicusmarine.subset``.

    The request can be executed via the :meth:`fetch` method, which downloads the
    data to the configured output path, unless the file already exists (this can
    be overridden with ``force=True``).

    Parameters
    ----------
    dataset_id : str
        Identifier of the CMEMS dataset (e.g.
        ``"cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D"``).
    variables : list of str
        List of variable names to extract from the dataset.
    start_datetime : str
        Start date-time in ISO8601 format (e.g. ``"2025-01-01T00:00:00"``).
    end_datetime : str
        End date-time in the same format.
    minimum_latitude : float
        Minimum latitude of the requested spatial domain.
    maximum_latitude : float
        Maximum latitude of the requested spatial domain.
    minimum_longitude : float
        Minimum longitude of the requested domain.
    maximum_longitude : float
        Maximum longitude.
    minimum_depth : float, optional
        Minimum depth for the request (if applicable). Defaults to None.
    maximum_depth : float, optional
        Maximum depth. Defaults to None.
    output_filename : str, optional
        Name of the output NetCDF file. Defaults to ``"output.nc"``.
    output_dir : str, optional
        Directory where the output file will be saved. If None, a dataset-specific
        directory under the project data folder is created automatically.
    extra_params : dict, optional
        Additional keyword arguments passed directly to ``copernicusmarine.subset``.

    Attributes
    ----------
    output_path : str
        Full path to the resulting NetCDF file.

    Examples
    --------
    Create a request and download DUACS SLA:

    >>> from visusat.copernicus import CopernicusRequest
    >>> req = CopernicusRequest(
    ...     dataset_id="cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
    ...     variables=["sla", "err_sla"],
    ...     minimum_longitude=1,
    ...     maximum_longitude=359,
    ...     minimum_latitude=-70,
    ...     maximum_latitude=80,
    ...     start_datetime="2025-10-22T00:00:00",
    ...     end_datetime="2025-10-22T00:00:00",
    ...     minimum_depth=None,
    ...     maximum_depth=None,
    ...     output_filename="duacs_sla.nc",
    ... )
    >>> req.fetch()
    """
    dataset_id: str
    variables: List[str]
    minimum_longitude: float
    maximum_longitude: float
    minimum_latitude: float
    maximum_latitude: float
    start_datetime: str
    end_datetime: str
    minimum_depth: Optional[float] = None
    maximum_depth: Optional[float] = None
    output_filename: Optional[str] = "copernicus_output.nc"

    def fetch(self, force: bool = False) -> Path:
        """
        Download the requested dataset from the Copernicus Marine Data Store.

        Parameters
        ----------
        force : bool, optional
            If True, overwrite the file even if it already exists. Defaults to False.

        Returns
        -------
        str
            Path to the downloaded NetCDF file.
        """
        logger.info(f"Fetching Copernicus dataset: {self.dataset_id}")

        filepath = Path(self.output_filename).resolve()

        # Manage overwrite manually
        if filepath.exists() and not force:
            logger.info(f"File already exists → {filepath}, skipping download.")
            return filepath
    
        request_kwargs = {
            "dataset_id": self.dataset_id,
            "variables": self.variables,
            "minimum_longitude": self.minimum_longitude,
            "maximum_longitude": self.maximum_longitude,
            "minimum_latitude": self.minimum_latitude,
            "maximum_latitude": self.maximum_latitude,
            "start_datetime": self.start_datetime,
            "end_datetime": self.end_datetime,
            "output_filename": self.output_filename,
        }

        # Add optional depth selection
        if self.minimum_depth is not None and self.maximum_depth is not None:
            request_kwargs["minimum_depth"] = self.minimum_depth
            request_kwargs["maximum_depth"] = self.maximum_depth

        # Perform download
        logger.info(f"→ Downloading with params: {request_kwargs}")
        response = copernicusmarine.subset(**request_kwargs)
        output = response.filepaths[0]
        logger.info(f"Download complete → {output}")
        
        return Path(output)

# ==============================================================================
# Dataset loader
# ==============================================================================
def load_dataset(request : CopernicusRequest, force : bool = False) -> xr.Dataset:
    """
    Download and open a Copernicus Marine dataset as an ``xarray.Dataset``.

    This function triggers the download associated with a
    :class:`~visusat.copernicus.CopernicusRequest` object and returns the
    resulting NetCDF file as an opened ``xarray.Dataset``. If the file already
    exists, the download is skipped unless ``force=True`` is provided.

    Parameters
    ----------
    request : CopernicusRequest
        A configured request describing the dataset subset to download.
    force : bool, optional
        If True, force redownload even if the file already exists.
        Defaults to False.

    Returns
    -------
    xarray.Dataset
        The dataset opened from the downloaded NetCDF file.
    """
    filepath = request.fetch(force)  # Download the data
    ds = safe_open_dataset(filepath)
    logger.info(f"Dataset opened with dims {dict(ds.dims)} and vars {list(ds.data_vars)}")
    return ds

# ==============================================================================
# PLOTS
# ==============================================================================
def _require_matplotlib():
    """Raise an error if Matplotlib is not installed."""
    try:
        import matplotlib.pyplot as plt
        from mpl_toolkits.axes_grid1 import make_axes_locatable
    except ImportError:
        raise ImportError(
            "Matplotlib is required for plotting functions in visusat.copernicus."
        )
    return plt, make_axes_locatable


def _require_cartopy():
    """Raise an error if cartopy is missing."""
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
    except ImportError:
        raise ImportError("Cartopy is required for geographic plotting.")
    return ccrs, cfeature


# ------------------------------------------------------------------------------

def plot_fields(request: CopernicusRequest, ds: xr.Dataset):
    """
    Plot each variable of a Copernicus Marine dataset retrieved via ``copernicusmarine``.

    Parameters
    ----------
    request : CopernicusRequest
        The request used to download the dataset.
    ds : xarray.Dataset
        Dataset containing the requested variables.

    Notes
    -----
    All heavy imports (cartopy, matplotlib, numpy) are performed inside the
    function to ensure ReadTheDocs compatibility.
    """

    plt, make_axes_locatable = _require_matplotlib()
    ccrs, cfeature = _require_cartopy()

    outdir = Path("outputs") / "copernicus" / request.dataset_id
    os.makedirs(outdir, exist_ok=True)

    for var in ds.data_vars:
        da = ds[var].squeeze()
        longname = escape_latex(getattr(da, "long_name", var))
        shortname = getattr(da, "short_name", var)
        isotime = isodate(da.time.values)
        logger.info(f"Plotting variable '{var}' ({longname}) at {isotime}.")

        lon = da.longitude.values
        lat = da.latitude.values
        val = da.values

        if hasattr(da, "units"):
            cbar_label = f"{longname}\n({da.units})"
        else:
            cbar_label = longname

        savepath = outdir / f"{shortname}_{isotime}.png"

        logger.info(f"Plot {longname} at {isotime}.")
        plot_field(lon, lat, val, title=f"{ds.title}.\n{longname} - {isotime}", cbar_label=cbar_label, savepath=savepath)
        


def plot_currents(request, ds: xr.Dataset, domain=None, vectors=False):
    """
    Plot ocean currents from a Copernicus Marine dataset and save one figure
    per time–depth combination.

    This function reads a velocity field (u, v) from a CMEMS dataset, computes
    the current magnitude, and produces a figure for each time step and each
    depth level. The output figures are automatically saved into a dataset-
    specific directory. Optional vector arrows can be added to visualise flow
    direction.

    Parameters
    ----------
    request : CopernicusRequest
        Request object used to download the dataset. Its ``dataset_id`` is used
        to determine the output directory for the generated figures.
    ds : xarray.Dataset
        The dataset containing velocity components. The function automatically
        detects the velocity variable names via ``utils.check_velocity_cop``.
        Expected dimensions: ``time``, ``depth``, ``latitude``, ``longitude``.
    domain : list of float, optional
        Geographic subdomain specified as ``[lon_min, lon_max, lat_min, lat_max]``.
        If provided, plots are zoomed to this region. Defaults to None.
    vectors : bool, optional
        If True, overlay quiver arrows (u, v) to show current direction.
        Defaults to False.

    Returns
    -------
    None
        The function generates and saves figures but does not return an object.

    Notes
    -----
    - A separate PNG file is produced for each combination of time and depth.
    - Velocity components are automatically identified using
      ``utils.check_velocity_cop()``.
    - Depth and time values are embedded into the output filename.
    """
    plt, make_axes_locatable = _require_matplotlib()
    ccrs, cfeature = _require_cartopy()

    figdir = os.path.join(OUT_DIR, request.dataset_id)
    os.makedirs(figdir, exist_ok=True)

    for i in range(len(ds.time)):
        for j in range(len(ds.depth)):

            suffix = ""
            # Check velocity variables
            try:
                u_var, v_var = check_velocity_cop(ds)
                u = ds[u_var][i, j, :, :].values
                v = ds[v_var][i, j, :, :].values
            except KeyError as e:
                logging.error("Error:", e)

            current_speed = np.sqrt(u**2 + v**2)
            depth = ds[u_var].depth.values[j]
            t = ds[u_var].time.values[i]
            isotime = pd.Timestamp(t).isoformat()
            lon = ds[u_var].longitude.values
            lat = ds[u_var].latitude.values

            # Beginning of plot
            proj = ccrs.PlateCarree()
            fig = plt.figure(figsize=(12, 6))
            ax = plt.axes(projection=proj)
            ax.set_global()

            im = ax.pcolormesh(
                lon,
                lat,
                current_speed,
                transform=proj,
                cmap="Spectral_r",
                shading="auto",
            )
            if vectors:
                suffix = suffix + "_wvectors"
                step = 6
                plt.quiver(
                    lon[::step],
                    lat[::step],
                    u[::step, ::step],
                    v[::step, ::step],
                    scale=25,
                    color="black",
                    width=0.002,
                    alpha=0.7,
                )
            # Cosmetics :
            ax.coastlines(resolution="110m", linewidth=0.6)
            ax.add_feature(cfeature.BORDERS, linewidth=0.4)
            gl = ax.gridlines(
                draw_labels=True, linewidth=1, color="lightgray", linestyle="--"
            )
            gl.top_labels = False
            gl.right_labels = False

            # Colorbar
            divider = make_axes_locatable(ax)
            cax = divider.append_axes(
                "bottom", size="2.5%", pad=0.3, axes_class=plt.Axes
            )
            cbar = plt.colorbar(im, cax=cax, orientation="horizontal", fraction=0.046)
            cbar.set_label(r"Ocean surface velocity (m.s$^{-1}$)")

            plt.suptitle(f"{isotime}")
            if domain is not None:
                suffix = suffix + "_subdomain"
                ax.set_extent(domain)
            else:
                suffix = suffix + "_earth"

            # Savefig
            savename = "surfacecurrents_" + isotime + f"_depth{depth}" + suffix
            savepath = os.path.join(figdir, savename + ".png")
            fig.tight_layout()
            fig.savefig(savepath, format="png", dpi=300, bbox_inches="tight")
            logging.info(f"Successfully saved in {savepath}")
            plt.close()


def get_cdsdataset(dataset, request):
    """
    Retrieve a dataset from the Copernicus Climate Data Store (CDS) via CDSAPI.

    This function sends a retrieval request to the CDS API and downloads the
    corresponding dataset to a local file. The CDS API handles caching, so
    repeated requests with identical parameters will not trigger additional
    downloads.

    Parameters
    ----------
    dataset : str
        Identifier of the dataset hosted on the Copernicus Climate Data Store.
        Examples include ``"reanalysis-era5-single-levels"`` or 
        ``"satellite-sea-surface-temperature"``.
    request : dict
        Dictionary of request parameters following CDSAPI conventions.
        Must include spatial, temporal, and variable selection keys depending on 
        the dataset.

    Returns
    -------
    str
        Path to the downloaded file produced by ``client.retrieve().download()``.
    """
    client = cdsapi.Client()
    ds = client.retrieve(dataset, request).download()
    return ds
