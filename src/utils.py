import logging
from datetime import datetime

import xarray as xr

logger = logging.getLogger(__name__)


def safe_open_dataset(path):
    """Open .netcdf file with best backend available."""
    for engine in ("h5netcdf", "netcdf4", "scipy"):
        try:
            ds = xr.open_dataset(path, engine=engine)
            logger.info(f"Open with engine '{engine}'")
            return ds
        except Exception as e:
            logger.warning(f" Fail with engine '{engine}': {e}")
    raise RuntimeError("No compatible backend for this file.")


def isodate(date):
    dt = datetime.strptime(date, "%Y%m%d%H%M%S")
    iso_date = dt.isoformat()
    return iso_date
