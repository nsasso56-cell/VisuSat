
from pathlib import Path
import os,sys
import eumdac
import json
import logging
import cartopy
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import h5py
import hdf5plugin

from satpy import Scene
from satpy import find_files_and_readers


# Basic Logging configuration
LOG_FILE = Path(__file__).with_suffix('.log')
script_name = os.path.basename(__file__)
#logger = logging.getLogger(script_name)

logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8", mode="w"),  # log dans un fichier
        logging.StreamHandler(sys.stdout)  # log aussi dans la console
    ],
    # crucial if VSCode or Ipython already touched the logging
    force=True
)
# Name of the logger :
logger = logging.getLogger(Path(__file__).stem)

logger.info("Program launched.")
# EUMETSAT authentification
with open('inputs/id_EUMETSAT.json') as f:
    d = json.load(f)
    print(d)
consumer_key = d["consumer"]
consumer_secret = d["secret"]
token = eumdac.AccessToken((consumer_key, consumer_secret))

datastore = eumdac.DataStore(token)
logger.info('Athentification succeed.')


# Collection required :
required_collection = "EO:EUM:DAT:0677" # FCI AllSky radiance Level2 product
# required_collection =  "EO:EUM:DAT:MSG:HRSEVIRI" # 'EO:EUM:DAT:0677'
logger.info(f'Get Collection {required_collection}')
collection = datastore.get_collection(required_collection)

# Research on a recent period (last day)
results = collection.search(
    dtstart="2025-09-20T00:00:00Z",
    dtend="2025-09-20T12:00:00Z"
)

products = list(results)[:1]   # Select last product

for product in products:
    logger.info(f"Product : {product}")

    target_dir = "./meteosat_data"
    os.makedirs(target_dir, exist_ok=True)


    # Ouverture du produit (renvoie un flux HTTP)
    # with product.open() as response:
    #     outfile = os.path.join(target_dir, f"{product._id}.nc")
    #     if os.path.exists(outfile) == False:
    #         with open(outfile, "wb") as f:
    #             f.write(response.read())
    #         logger.info(f"Product saved : {outfile}")
    #     else :
    #         logger.info(f'Output file already exists : {outfile}')
    for entry in product.entries:

        if entry.endswith(".nc"):
            logger.info("Download of NetCDF :", entry)
            target_file = os.path.join(target_dir, entry)
            if os.path.exists(target_file) == False:
                with product.open(entry) as fsrc, open(target_file, "wb") as fdst:
                    fdst.write(fsrc.read())
                logger.info("→ File saved :", target_file)
            else : 
                logger.info(f"Target file already existent : {target_file}")
    

# ds = xr.open_dataarray(outfile, engine = "netcdf4")


# with h5py.File(outfile, "r") as f:
#     print("Groupes au niveau racine :", list(f.keys()))

#     # Explorer récursivement
#     def explore(name, obj):
#         print(name, obj.shape if hasattr(obj, 'shape') else '')
#     f.visititems(explore)


# ds = Dataset(outfile, "r")
# print(ds)
# print(ds.variables.keys())


# Find readers for sat files in Satpy :
# files, readers = find_files_and_readers(
#     base_dir="./meteosat_data", 
#     reader=None,   # Satpy va deviner
#     reader_kwargs={})

# logger.info("Readers possibles :", readers)
# logger.info("Fichiers trouvés :", files)

# Afficher

ds = xr.open_dataset(target_file)

arr = ds["radiance_mean"].values
logger.info("All NaN ? ->", np.isnan(arr).all())
logger.info("Proportion of NaN ->", np.isnan(arr).sum() / arr.size)

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
plt.show()

logger.info('End program.')
