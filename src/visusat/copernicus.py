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

# --- Mandatory third-party dependencies ---
import numpy as np
import pandas as pd
import xarray as xr

# --- Optional heavy dependencies (imported safely for RTD and minimal installs) ---
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
except Exception:  # cartopy often missing on RTD / Windows
    ccrs = None
    cfeature = None

try:
    import matplotlib
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable
except Exception:  # matplotlib may not exist on RTD
    matplotlib = None
    plt = None
    make_axes_locatable = None

try:
    import cdsapi
except Exception:
    cdsapi = None  # allows the module to be imported without cdsapi installed

try:
    import copernicusmarine
except Exception:
    copernicusmarine = None  # allows docs to build without the library

# --- Local dependencies ---
from visusat import utils

# --- Global config (only executed if matplotlib is present) ---
if matplotlib is not None:
    matplotlib.rcParams["figure.dpi"] = 200
    matplotlib.rcParams.update(
        {"text.usetex": True, "font.family": "serif", "font.size": 10}
    )

# --- Project paths ---
logger = logging.getLogger(__name__)
project_root = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.path.join(project_root, "data","copernicus"))
OUT_DIR = Path(os.path.join(project_root, "outputs", "copernicus"))


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
    ...     output_filename="duacs_sla.nc",
    ... )
    >>> req.fetch()
    """

    def __init__(
        self,
        dataset_id: str,
        variables: List[str],
        start_datetime: str,
        end_datetime: str,
        minimum_latitude: float,
        maximum_latitude: float,
        minimum_longitude: float,
        maximum_longitude: float,
        minimum_depth: Optional[float] = None,
        maximum_depth: Optional[float] = None,
        output_filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        extra_params: Optional[Dict[str, str]] = None,
    ):
        self.dataset_id = dataset_id  # ex: "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D"
        self.variables = variables  # ex: ["sla", "adt"]
        self.start_datetime = start_datetime  # ex: "2025-01-01T00:00:00"
        self.end_datetime = end_datetime  # ex: "2025-01-10T00:00:00"
        self.minimum_latitude = minimum_latitude
        self.maximum_latitude = maximum_latitude
        self.minimum_longitude = minimum_longitude
        self.maximum_longitude = maximum_longitude
        self.minimum_depth = minimum_depth or None
        self.maximum_depth = maximum_depth or None
        self.output_filename = output_filename or "output.nc"
        self.output_dir = output_dir or os.path.join(
            DATA_DIR, self.dataset_id
        )
        self.extra_params = extra_params or {}

        # Set output_path :
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_path = (
            os.path.join(self.output_dir, self.output_filename)
            or f"./{self.output_filename}"
        )

    def fetch(self, force=False):
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
        logging.info(f"Output path : {self.output_path}")

        if not force and os.path.exists(self.output_path):
            logging.info(f"✅ {self.output_path} already existent, ignore download.")
            return

        logging.info(f"⏬ Downloading {self.output_path} ...")
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        copernicusmarine.subset(
            dataset_id=self.dataset_id,
            variables=self.variables,
            minimum_longitude=self.minimum_longitude,
            maximum_longitude=self.maximum_longitude,
            minimum_latitude=self.minimum_latitude,
            maximum_latitude=self.maximum_latitude,
            minimum_depth=self.minimum_depth,
            maximum_depth=self.maximum_depth,
            start_datetime=self.start_datetime,
            end_datetime=self.end_datetime,
            output_filename=self.output_path,
        )
        logging.info("✅ Download succesful.")


def get_copdataset(request, force=False) -> xr.Dataset:
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
    request.fetch(force)  # Download the data

    ds = xr.open_dataset(request.output_path)  # Open the downloaded .netcdf file
    logging.info(ds)

    return ds


def plot_copdataset(request, ds):
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

    if ccrs is None or plt is None:
        raise ImportError(
            "plot_copdataset() requires cartopy and matplotlib.\n"
            "Install them with: pip install visusat[full]"
        )

    figdir = os.path.join(OUT_DIR, request.dataset_id)
    os.makedirs(figdir, exist_ok=True)

    for variable in list(ds):

        lon = ds[variable].longitude.values
        lat = ds[variable].latitude.values
        val = ds[variable].squeeze().values
        longname = utils.str_replace(ds[variable].long_name)
        # units = ds[variable].units
        t = ds[variable].time.values[0]
        isotime = pd.Timestamp(t).isoformat()

        logging.info(f"Plot {longname} at {isotime}.")

        lon2d, lat2d = np.meshgrid(lon, lat)

        # Initiate figure
        proj = ccrs.PlateCarree()
        fig = plt.figure(figsize=(12, 6))
        ax = plt.axes(projection=proj)
        ax.set_global()

        im = ax.pcolormesh(
            lon, lat, val, transform=proj, cmap="Spectral_r", shading="auto"
        )
        # Cosmetics :
        ax.coastlines(resolution="110m", linewidth=1)
        ax.add_feature(cfeature.BORDERS, linewidth=0.4)
        gl = ax.gridlines(
            draw_labels=True, linewidth=1, color="lightgray", linestyle="--"
        )
        gl.top_labels = False
        gl.right_labels = False

        # Colorbar
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("bottom", size="2.5%", pad=0.3, axes_class=plt.Axes)
        cbar = plt.colorbar(im, cax=cax, orientation="horizontal", fraction=0.046)
        if hasattr(ds[variable], "units"):
            cbar.set_label(f"{longname} ({ds[variable].units})")
        else:
            cbar.set_label(f"{longname}")

        plt.suptitle(f"{ds.title}.\n{longname} - {isotime}")

        # Savefig
        savename = ds[variable].standard_name + "_" + isotime
        savepath = os.path.join(figdir, savename + ".png")
        fig.tight_layout()
        fig.savefig(savepath, format="png", dpi=300, bbox_inches="tight")
        logging.info(f"Successfully saved in {savepath}")
        plt.close()
        # plt.show()


def plot_field(
    lon,
    lat,
    val,
    title="",
    subdomain=None,
    cmap="Spectral_r",
    cbar_label="unknown",
    proj=None,
    savepath=None,
    saveformat="png",
):
    """
    Plot a geophysical field on a map using Cartopy.

    This function generates a 2D colormesh plot of a field defined on a regular
    longitude–latitude grid. It supports global plots as well as regional zooms,
    and includes coastlines, borders, and custom colorbar formatting. The output
    figure can optionally be saved to disk.

    Parameters
    ----------
    lon : array-like
        2D array of longitudes corresponding to ``val``.
    lat : array-like
        2D array of latitudes corresponding to ``val``.
    val : array-like
        2D data field to plot (e.g. radiance, SST, wind speed).
    title : str, optional
        Figure title. Defaults to an empty string.
    subdomain : list of float, optional
        Geographic extent specified as ``[lon_min, lon_max, lat_min, lat_max]``.
        If provided, the plot is zoomed to this region. Defaults to None.
    cmap : str, optional
        Matplotlib colormap name. Defaults to ``"Spectral_r"``.
    cbar_label : str, optional
        Label for the colorbar. Defaults to ``"unknown"``.
    proj : cartopy.crs.Projection, optional
        Map projection for the plot. Defaults to ``ccrs.PlateCarree()``.
    savepath : str or path-like, optional
        Path where the figure will be saved. If None, the figure is only returned.
        Defaults to None.
    saveformat : str, optional
        Output format for saving (e.g. ``"png"``, ``"pdf"``). Defaults to ``"png"``.

    Returns
    -------
    tuple
        A tuple ``(fig, ax)`` where:
            - ``fig`` is the created Matplotlib figure.
            - ``ax`` is the Cartopy GeoAxes object.

    Notes
    -----
    - ``lon`` and ``lat`` must match the shape of ``val``.
    - ``subdomain`` must follow Plate Carrée coordinates.
    - If ``savepath`` is provided, the figure is saved with the specified format.
    """
    if ccrs is None or plt is None:
        raise ImportError(
            "plot_field() requires cartopy and matplotlib.\n"
            "Install them with: pip install visusat[full]"
        )

    # Default value ccrs.PlateCaree() for proj :
    if proj is None :
        proj = ccrs.PlateCarree()

    logger.info(f"Plot figure with field {title}.")
    # Initiate figure
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=proj)
    ax.set_global()
    im = ax.pcolormesh(
        lon, lat, val, transform=ccrs.PlateCarree(), cmap=cmap, shading="auto"
    )

    # Cosmetics :

    gl = ax.gridlines(draw_labels=True, linewidth=1, color="lightgray", linestyle="--")
    gl.top_labels = False
    gl.right_labels = False

    # Colorbar
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="2.5%", pad=0.3, axes_class=plt.Axes)
    cbar = plt.colorbar(im, cax=cax, orientation="horizontal", fraction=0.046)
    cbar.set_label(cbar_label)

    if subdomain is not None:
        ax.set_extent(subdomain)
        ax.add_feature(cfeature.COASTLINE.with_scale("10m"), linewidth=0.6)
        ax.add_feature(cfeature.BORDERS.with_scale("10m"), linewidth=0.4)
        ax.add_feature(
            cfeature.LAKES.with_scale("10m"), linewidth=0.3, edgecolor="gray"
        )
        ax.add_feature(
            cfeature.RIVERS.with_scale("10m"), linewidth=0.3, edgecolor="lightblue"
        )
    else:
        ax.coastlines(resolution="110m", linewidth=0.6)
        ax.add_feature(cfeature.BORDERS, linewidth=0.4)

    fig.suptitle(title)
    fig.tight_layout()

    if savepath is not None:
        fig.savefig(savepath, format=saveformat, dpi=300, bbox_inches="tight")
        logger.info("Figure saved in {save_path}.")

    return fig, ax


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
    if ccrs is None or plt is None:
        raise ImportError(
            "plot_currents() requires cartopy and matplotlib.\n"
            "Install them with: pip install visusat[full]"
        )

    figdir = os.path.join(OUT_DIR, request.dataset_id)
    os.makedirs(figdir, exist_ok=True)

    for i in range(len(ds.time)):
        for j in range(len(ds.depth)):

            suffix = ""
            # Check velocity variables
            try:
                u_var, v_var = utils.check_velocity_cop(ds)
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
