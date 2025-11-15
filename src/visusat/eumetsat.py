"""
EUMETSAT module
===============

Tools for interacting with EUMETSAT Data Store and Data Tailor products.

This module provides high-level utilities to authenticate, download, customise,
and visualise EUMETSAT satellite data (e.g., MTG-FCI, Metop, MSG). It builds on
the official EUMDAC Python client and offers additional helper routines suited
for scientific workflows.

The main features include:

- Authentication with the EUMETSAT Data Store using locally stored credentials
  (``get_token``),
- Requesting and monitoring Data Tailor customisations (``customisation``),
- Downloading satellite files over a specified time window (``download_data``),
- Plotting Atmospheric Motion Vectors (AMVs) from Level-2 products
  (``plot_amvs``),
- Visualising radiance fields from FCI Level-1/Level-2 datasets
  (``plot_radiance``),
- General helper tools to facilitate EUMETSAT data processing within VisuSat.

This module centralizes all interactions with EUMETSAT services to ensure
consistent, robust, and reproducible satellite data workflows.
"""
from __future__ import annotations

# --- Standard library imports ---
import json
import logging
import os
import shutil
import time
from pathlib import Path

# --- Mandatory third-party dependencies ---
import eumdac
import numpy as np


# --- Third-party imports (wrapped in try/except so documentation builds gracefully) ---
try:
    import cartopy.crs as ccrs
except Exception:  
    ccrs = None

try:
    import matplotlib
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable
except Exception:  
    matplotlib = None
    plt = None
    make_axes_locatable = None


# --- Local dependencies ---
from visusat import utils

# --- Matplotlib config (conditional) ---
if matplotlib is not None:
    matplotlib.rcParams["figure.dpi"] = 200
    matplotlib.rcParams.update(
        {"text.usetex": False, "font.family": "serif", "font.size": 10}
    )

# -- Logger ---
logger = logging.getLogger(__name__)

# --- Project paths ---
project_root = Path(__file__).resolve().parent.parent.parent
DEFAULT_CREDENTIALS_PATH = Path.home() / ".config" / "visusat" / "id_EUMETSAT.json"

def get_token(credentials_path: Path = DEFAULT_CREDENTIALS_PATH):
    """
    Retrieve an EUMETSAT Data Store access token using local credentials.

    The function reads a JSON file containing the consumer key and secret,
    and returns a valid ``eumdac.AccessToken`` object for authenticating
    with the EUMETSAT Data Store (EUMDAC).

    Returns
    -------
    eumdac.AccessToken
        A valid authentication token for accessing EUMETSAT Data Store products.
    """
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Could not find EUMETSAT credentials. Please create the file at: {credentials_path}"
        )
    with open(credentials_path) as f:
        creds = json.load(f)
    token = eumdac.AccessToken((creds["consumer"], creds["secret"]))

    return token


def download_data(
    collection_id,
    start_time,
    end_time,
    last=False,
    output_file=None,
):
    """
    Download EUMETSAT satellite Data via the EUMDAC API.

    Parameters
    ----------
    collection_id : str
        Identifier of the desired collection, as listed in the EUMETSAT Data Store.
    start_time : datetime
        Start ot the requested time period.
    end_time : datetime
        End of the requested time period.
    last : bool, optional
        If True, only download the most recent file within the time period.
        Defaults to False.
    output_file : str, optional
        Specific output file path. Only valid if a single file is produced.
        Ignored when multiple files are downloaded.

    Returns
    -------
    list of str
        Paths of the downloaded files.
    """

    # EUMETSAT authentification
    logger.info("EUMETSAT authentification...")
    token = get_token()
    datastore = eumdac.DataStore(token)
    logger.info("Athentification succeed.")

    # Collection required :
    # required_collection =  "EO:EUM:DAT:MSG:HRSEVIRI" # 'EO:EUM:DAT:0677'
    logger.info(f"Get Collection {collection_id}")
    collection = datastore.get_collection(collection_id)

    # Research collection on a defined period :
    logger.info(
        f"Download data for {collection_id} between {start_time} and {end_time}"
    )
    results = collection.search(dtstart=start_time, dtend=end_time)

    if last:
        logger.info("last = True : Selection of only last product (more recent).")
        products = list(results)[:1]  # Select only last product

    outfiles = []

    for product in products:
        logger.info(f"Product : {product}")
        target_dir = os.path.join(project_root, "data", collection_id, product._id)
        os.makedirs(target_dir, exist_ok=True)

        for entry in product.entries:
            if entry.endswith(".nc"):
                logger.info(f"Download of NetCDF : {entry}")
            elif entry.endswith(".jpg"):
                logger.info(f"Download of .jpg image : {entry}")

            # Set target file path
            target_file = os.path.join(target_dir, entry)
            outfiles.append(target_file)

            if output_file is not None:
                if len(products) > 1:
                    logger.info(
                        "output_file is specified but products are mutliple : Conflict, return to default configuration."
                    )
                else:
                    target_file = output_file

            if not os.path.exists(target_file):
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                with product.open(entry) as fsrc, open(target_file, "wb") as fdst:
                    fdst.write(fsrc.read())
                logger.info(f"→ File saved : {target_file}")
            else:
                logger.info(f"Target file already existent : {target_file}")

    return outfiles


def customisation(product, chain):
    """
    Request and download a customised EUMETSAT product using the EUMDAC Data Tailor API.

    This function submits a customisation request to the EUMETSAT Data Tailor Web
    Services using the EUMDAC Python client. It monitors the job until completion,
    handles possible error states, and downloads all generated output files to the
    local data directory.

    Parameters
    ----------
    product : eumdac.DataItem
        The EUMETSAT product to customise. This is typically obtained via a search
        in the EUMETSAT Data Store client.
    chain : eumdac.tailor_models.Chain
        Data Tailor processing chain describing the desired customisation
        (e.g., spatial subset, spectral bands selection, projection, etc.).

    Returns
    -------
    tuple of (str, eumdac.Customisation)
        A tuple containing:
            - The path to the last downloaded file.
            - The ``Customisation`` object returned by the Data Tailor Web Service.
    """

    token = get_token()
    # Create datatailor object with your token
    datatailor = eumdac.DataTailor(token)

    # Send the customisation to Data Tailor Web Services
    customisation = datatailor.new_customisation(product, chain=chain)

    status = customisation.status
    sleep_time = 10  # seconds

    # Customisation loop to read current status of the customisation
    logger.info("Starting customisation process...")
    while status:
        # Get the status of the ongoing customisation
        status = customisation.status
        if "DONE" in status:
            logger.info(f"Customisation {customisation._id} is successfully completed.")
            break
        elif status in ["ERROR", "FAILED", "DELETED", "KILLED", "INACTIVE"]:
            logger.info(
                f"Customisation {customisation._id} was unsuccessful. Customisation log is printed.\n"
            )
            logger.info(customisation.logfile)
            break
        elif "QUEUED" in status:
            logger.info(f"Customisation {customisation._id} is queued.")
        elif "RUNNING" in status:
            logger.info(f"Customisation {customisation._id} is running.")
        time.sleep(sleep_time)

    #
    datadir = os.path.join(
        project_root, "data", "eumetsat", "custom", product.collection._id
    )

    logger.info("Starting download of customised products...")
    for product in customisation.outputs:
        savepath = os.path.join(datadir, product)
        os.makedirs(os.path.dirname(savepath), exist_ok=True)
        logger.info(f"Downloading product: {product}")
        with (
            customisation.stream_output(product) as source_file,
            open(savepath, "wb") as destination_file,
        ):
            shutil.copyfileobj(source_file, destination_file)
        logger.info(f"Product {product} downloaded successfully.")

    return savepath, customisation


def plot_radiance(filename, collection_id, outfile=None, savefig=True, display=False):
    """
    Plot mean radiance fields from an EUMETSAT FCI AllSkyRadiance NetCDF product.

    This function loads an FCI AllSkyRadiance dataset and visualises the
    radiance distribution across the six AllSky categories for a given
    spectral channel. Each category is displayed as a separate subplot.
    The function supports automatic output naming and optional file saving
    or on-screen display.

    Parameters
    ----------
    filename : str or path-like
        Path to the input NetCDF file containing ``radiance_mean`` data.
    collection_id : str
        EUMETSAT collection identifier from which the dataset was retrieved.
        Used to determine the default output directory.
    outfile : str or path-like, optional
        Output filename for saving the generated figure. If None, a filename
        is automatically constructed based on the input file. Defaults to None.
    savefig : bool, optional
        If True, save the figure to ``outfile``. Defaults to True.
    display : bool, optional
        If True, display the figure with ``plt.show()``. Defaults to False.

    Returns
    -------
    None
        The function creates and optionally saves a figure but does not 
        return any object.
    """

    if outfile is None:
        outdir = os.path.join(project_root, "outputs", collection_id)
        os.makedirs(outdir, exist_ok=True)
        outfile = os.path.join(outdir, Path(filename).stem + ".png")

    ds = utils.safe_open_dataset(filename)

    arr = ds["radiance_mean"].values
    logger.info(f"All NaN ? -> {np.isnan(arr).all()}")
    logger.info(f"Proportion of NaN -> { np.isnan(arr).sum() / arr.size}")

    vals = ds["radiance_mean"].values
    channel = 7
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    for cat in range(6):
        ax = axes.flat[cat]
        img = vals[:, :, channel, cat]
        im = ax.imshow(img, origin="lower")
        ax.set_title(f"Category {cat}")
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.suptitle(f"FCI AllSkyRadiance - Channel {channel}")
    if savefig:
        fig.tight_layout()
        fig.savefig(outfile + ".png", format="png", bbox_inches="tight", dpi=300)
    if display:
        plt.show()


def plot_amvs(filename, product, box=None, outfile=None, savefig=True, display=False):
    """
    Plot Atmospheric Motion Vectors (AMVs) from an EUMETSAT AMV NetCDF product.

    This function loads the AMV dataset, extracts the zonal (u) and meridional (v)
    wind components, and visualises them as scatter plots on a map using a
    Plate Carrée projection. Two subplots are generated: one for the zonal 
    component and one for the meridional component. A zoomed domain can be
    specified via the ``box`` argument.

    Parameters
    ----------
    filename : str or path-like
        Path to the input NetCDF file containing AMVs.
    product : object
        EUMETSAT product metadata object. Must contain ``collection_id`` and
        ``description`` attributes.
    box : list of float, optional
        Geographic subset defined as ``[lon_min, lon_max, lat_min, lat_max]``.
        If provided, the map will zoom into this region. Defaults to None.
    outfile : str or path-like, optional
        Output filename for the generated PNG figure. If None, a default name is
        automatically constructed based on the input file. Defaults to None.
    savefig : bool, optional
        If True, save the figure to ``outfile``. Defaults to True.
    display : bool, optional
        If True, display the figure interactively using ``plt.show()``.
        Not recommended when processing many files. Defaults to False.

    Returns
    -------
    None
        The function generates and optionally saves a figure, but does not 
        return an object.
    """
    prefix = ""
    if outfile is None:
        outdir = os.path.join(project_root, "outputs", product.collection_id)
        os.makedirs(outdir, exist_ok=True)
        outfile = os.path.join(outdir, "map_uv_" + Path(filename).stem + ".png")

    ds = utils.safe_open_dataset(filename)

    fig, axes = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(10, 5),
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    ax = axes.flat

    t_start = utils.isodate(ds.time_coverage_start)
    t_end = utils.isodate(ds.time_coverage_end)

    u_velocity = ds["speed_u_component"].values
    v_velocity = ds["speed_v_component"].values
    latitude = ds["latitude"].values
    longitude = ds["longitude"].values

    cmap = plt.get_cmap("jet", 21)
    cmap.set_over("w"), cmap.set_under("k")
    vmin = -200
    vmax = -vmin

    im = ax[0].scatter(
        longitude, latitude, c=u_velocity, vmin=vmin, vmax=vmax, s=0.5, cmap=cmap
    )
    ax[0].set_title("(a) Zonal wind")
    divider = make_axes_locatable(ax[0])
    cax = divider.append_axes("right", size="2%", pad=0.05, axes_class=plt.Axes)
    fig.add_axes(cax)
    cbar = fig.colorbar(im, cax=cax)
    cbar.ax.tick_params()
    cbar.set_ticks(np.linspace(vmin, vmax, 11))
    cbar.set_ticklabels(np.linspace(vmin, vmax, 11))
    cbar.set_label("(m/s)")

    #
    im = ax[1].scatter(
        longitude, latitude, c=v_velocity, vmin=vmin, vmax=vmax, s=0.5, cmap=cmap
    )
    ax[1].set_title("(b) Meridional wind")
    divider = make_axes_locatable(ax[1])
    cax = divider.append_axes("right", size="2%", pad=0.05, axes_class=plt.Axes)
    fig.add_axes(cax)
    cbar = fig.colorbar(im, cax=cax)
    cbar.ax.tick_params()
    cbar.set_ticks(np.linspace(vmin, vmax, 11))
    cbar.set_ticklabels(np.linspace(vmin, vmax, 11))
    cbar.set_label("(m/s)")

    # set graphical parameters
    for i in range(len(ax)):
        ax[i].coastlines(resolution="50m")
        gl = ax[i].gridlines(
            draw_labels=True, linestyle="--", linewidth=0.5, color="grey"
        )

        # add these before plotting
        gl.top_labels = False  # suppress top labels
        gl.right_labels = False  # suppress right labels
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER

    if box is not None:
        logger.info(f"Zoom on box {box}.")
        prefix = prefix + "zoom_"
        for i in range(len(ax)):
            ax[i].set_extent(box)

    fig.subplots_adjust(wspace=0.2)
    fig.suptitle(product.description + "\n" + t_start + "  -  " + t_end)

    if savefig:
        fig.tight_layout()
        pathout = Path(outfile)
        pathout = pathout.with_name(prefix + pathout.name + ".png")

        fig.savefig(pathout, format="png", dpi=300)
        logger.info(f"Figure saved ➡️ {pathout}")

    if display:
        plt.show()
