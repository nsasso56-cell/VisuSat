import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from src.eumetsat_products_registry import *
from src import eumetsat

# Basic Logging configuration
LOG_FILE = Path(__file__).with_suffix(".log")
script_name = os.path.basename(__file__)
# logger = logging.getLogger(script_name)

logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_FILE, encoding="utf-8", mode="w"
        ),  # log dans un fichier
        logging.StreamHandler(sys.stdout),  # log aussi dans la console
    ],
    # crucial if VSCode or Ipython already touched the logging
    force=True,
)
# Name of the logger :
logger = logging.getLogger(Path(__file__).stem)

logger.info("Program launched.")

# Load EUMETSAT products registry :
load_registry()

start_time = datetime.utcnow() - timedelta(hours=6)
end_time = datetime.utcnow() - timedelta(hours=2)

# Collection required :
required_collection = ""  # Registry in data/EUMETSAT_products_registry
# Load EUMETSAT products registry :
load_registry()
product = PRODUCTS[required_collection]

output_files = eumetsat.download_data(
    required_collection, start_time, end_time, last=True
)

for file in output_files:
    eumetsat.plot(file, required_collection)

logger.info("End program.")
