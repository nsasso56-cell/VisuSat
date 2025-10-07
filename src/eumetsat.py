import json
import logging
import os
from pathlib import Path

import eumdac
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)


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
    project_root = Path(__file__).resolve().parent.parent
    id_file = os.path.join(project_root, "inputs", "id_EUMETSAT.json")
    with open(id_file) as f:
        d = json.load(f)
        print(d)
    consumer_key = d["consumer"]
    consumer_secret = d["secret"]
    token = eumdac.AccessToken((consumer_key, consumer_secret))
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
        target_dir = os.path.join(project_root, "data", collection_id)
        os.makedirs(target_dir, exist_ok=True)

        for entry in product.entries:
            if entry.endswith(".nc"):
                logger.info("Download of NetCDF :", entry)
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
                    with product.open(entry) as fsrc, open(target_file, "wb") as fdst:
                        fdst.write(fsrc.read())
                    logger.info(f"→ File saved : {target_file}")
                else:
                    logger.info(f"Target file already existent : {target_file}")

    return outfiles


def plot(filename, collection_id, outfile=None, savefig=True, display=False):
    """
    Plot the brut data contained in downloaded EUMETSAT .netcdf file.
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

    ds = xr.open_dataset(filename)

    arr = ds["radiance_mean"].values
    logger.info(f"All NaN ? -> {np.isnan(arr).all()}")
    logger.info(f"Proportion of NaN -> { np.isnan(arr).sum() / arr.size}")

    # lats = ds["latitude"].values
    # lons = ds["longitude"].values
    # val = ds["data"].values

    # logger.info(f"Lat shape : {lats.shape}")
    # logger.info(f"Lon shape : {lons.shape}")
    # logger.info(f"data shape : {val.shape}")

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
