import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cdsapi
import copernicusmarine
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from mpl_toolkits.axes_grid1 import make_axes_locatable
from src import utils

matplotlib.rcParams["figure.dpi"] = 200
matplotlib.rcParams.update(
    {"text.usetex": True, "font.family": "serif", "font.size": 10}
)

logger = logging.getLogger(__name__)
project_root = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.path.join(project_root, "data"))
OUT_DIR = Path(os.path.join(project_root, "outputs", "copernicus"))


class CopernicusRequest:
    """
    Copernicus request class is used to define a proper request to be proposed to Copernicus Data Store.

    Example of use :
    request = copernicus.CopernicusRequest(
    dataset_id="cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
    variables=["sla", "err_sla", "flag_ice"],
    minimum_longitude=1,
    maximum_longitude=359,
    minimum_latitude=-71.81717698546082,
    maximum_latitude=82.52141057014119,
    start_datetime="2025-10-22T00:00:00",
    end_datetime="2025-10-22T00:00:00",
    output_filename="globaloceanidentifier_oct2025.nc"

    CopernicusRequest.fetch() to download the data from Copernicus data store following request.
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
            project_root, "data", "copernicus", self.dataset_id
        )
        self.extra_params = extra_params or {}

        # Set output_path :
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_path = (
            os.path.join(self.output_dir, self.output_filename)
            or f"./{self.output_filename}"
        )

    def fetch(self, force=False):
        """Download dataset except if file is already existent (can be bypass with force=True)."""

        logging.info(f"Output path : {self.output_path}")

        if not force and os.path.exists(self.output_path):
            logging.info(f"✅ {self.output_path} already existent, ignore download.")
            return

        logging.info(f"⏬ Downloading {self.output_path} ...")
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


def get_copdataset(request, force=False):
    """
    Get the .netcdf dataset from Copernicus Marine Service.
    - request : (class CopernicusRequest)

    Returns ds : dataset from .netcdf output.
    """

    request.fetch(force)  # Download the data

    ds = xr.open_dataset(request.output_path)  # Open the downloaded .netcdf file
    logging.info(ds)

    return ds


def plot_copdataset(request, ds):

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
    proj=ccrs.PlateCarree(),
    savepath = None,
    saveformat = 'png'
):
    logger.info(f"Plot figure with field {title}.")
    # Initiate figure
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=proj)
    ax.set_global()
    im = ax.pcolormesh(lon, lat, val, transform=ccrs.PlateCarree(), cmap=cmap, shading="auto")

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
        ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=0.6)
        ax.add_feature(cfeature.BORDERS.with_scale('10m'), linewidth=0.4)
        ax.add_feature(cfeature.LAKES.with_scale('10m'), linewidth=0.3, edgecolor='gray')
        ax.add_feature(cfeature.RIVERS.with_scale('10m'), linewidth=0.3, edgecolor='lightblue')
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
    client = cdsapi.Client()
    ds = client.retrieve(dataset, request).download()
    return ds
