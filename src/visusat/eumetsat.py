import json
import logging
import os
import shutil
import time
from pathlib import Path

import cartopy.crs as ccrs
import eumdac
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
from mpl_toolkits.axes_grid1 import make_axes_locatable

from visusat import utils

logger = logging.getLogger(__name__)
project_root = Path(__file__).resolve().parent.parent.parent

matplotlib.rcParams["figure.dpi"] = 200
matplotlib.rcParams.update(
    {"text.usetex": True, "font.family": "serif", "font.size": 10}
)


def get_token():
    id_file = os.path.join(project_root, "inputs", "id_EUMETSAT.json")
    with open(id_file) as f:
        d = json.load(f)
        # print(d)
    consumer_key = d["consumer"]
    consumer_secret = d["secret"]
    token = eumdac.AccessToken((consumer_key, consumer_secret))

    return token


def download_data(
    collection_id,
    start_time,
    end_time,
    last=False,
    output_file=None,
):
    """
    Download Eumetsat satellite Data via Eumdac API.

    Args :
        - collection_id : ID of the required collection, available in EUMETSAT data store (string).
        - start_time : start ot the desired time period (datetime)
        - end_time : end of the desired time period (datetime)
        - last : specify as True if you want only the last file of the period (ie more recent) (boolean, default = False)
        - output_file : specify if you want to save in a specific location (string, default = None)

    Returns output files path as a list of strings.
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
    Plot the brut mean_radiance data contained in downloaded EUMETSAT .netcdf file.
    Args :
        - filename : name of the .netcdf file to treat.
        - collection_id : Eumetsat collection ID from where data were extracted (mandatory).
        - outfile : Specification of .png plot output (default = None, autogeneration of output filename).
        - savefig : Specify False for no output save (default = True).
        - Display : if True, display the figure, not recommended if numerous files to treat. (boolean, default = False)
    """
    project_root = Path(__file__).resolve().parent.parent
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
    Plot the brut AMVs data contained in downloaded EUMETSAT .netcdf file.
    Args :
        - filename : name of the .netcdf file to treat.
        - collection_id : Eumetsat collection ID from where data were extracted (mandatory).
        - outfile : Specification of .png plot output (default = None, autogeneration of output filename).
        - savefig : Specify False for no output save (default = True).
        - box : set domain to zoom in [lon_min,lon_max, lat_min, lat_max] (list, default = None)
        - Display : if True, display the figure, not recommended if numerous files to treat. (boolean, default = False)
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
