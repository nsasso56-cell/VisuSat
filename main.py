
from pathlib import Path
import os,sys
import eumdac
import json
import logging

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


# Exemple : MTG-FCI
required_collection = 'EO:EUM:DAT:0677'
logger.info(f'Get Collection {required_collection}')
collection = datastore.get_collection(required_collection)

# Research on a recent period (last day)
results = collection.search(
    dtstart="2025-09-16T00:00:00Z",
    dtend="2025-09-17T00:00:00Z"
)
products = list(results)[-1:]   # Select last product

for product in products:
    logger.info(f"Product : {product}")

    target_dir = "./meteosat_data"
    os.makedirs(target_dir, exist_ok=True)


    # Ouverture du produit (renvoie un flux HTTP)
    with product.open() as response:
        outfile = os.path.join(target_dir, f"{product._id}.nc")
        with open(outfile, "wb") as f:
            f.write(response.read())
        logger.info(f"Product saved : {outfile}")

logger.info('End program.')



