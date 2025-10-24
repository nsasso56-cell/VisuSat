import os, sys
import cdsapi
import copernicusmarine
import xarray as xr
import logging
from typing import List, Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)
project_root = Path(__file__).resolve().parent.parent
DATA_DIR = Path(
    os.path.join(project_root, "data")
    )



class CopernicusRequest:
    '''
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

    CopernicusRequest.fetch() to download the data to 

)
    '''
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
        output_filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        extra_params: Optional[Dict[str, str]] = None
    ):
        self.dataset_id = dataset_id                # ex: "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D"
        self.variables = variables                  # ex: ["sla", "adt"]
        self.start_datetime = start_datetime         # ex: "2025-01-01T00:00:00"
        self.end_datetime = end_datetime             # ex: "2025-01-10T00:00:00"
        self.minimum_latitude = minimum_latitude
        self.maximum_latitude = maximum_latitude
        self.minimum_longitude = minimum_longitude
        self.maximum_longitude = maximum_longitude
        self.output_filename = output_filename or "output.nc"
        self.output_dir = output_dir or os.path.join(project_root, "data", "copernicus", self.dataset_id)
        self.extra_params = extra_params or {}

        # Set output_path :
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_path = os.path.join(self.output_dir,self.output_filename) or f"./{self.output_filename}"


    def fetch(self, force=False):
        """Download dataset except if file is already existent (can be bypass with force=True)."""
        
        logging.info(f"Output path : {self.output_path}")
        
        if not force and os.path.exists(self.output_path):
            logging.info(f"✅ {self.output_path} already existent, ignore download.")
            return

        logging.info(f"⏬ Downloading {output_path} ...")
        copernicusmarine.subset(
            dataset_id=self.dataset_id,
            variables=self.variables,
            minimum_longitude=self.minimum_longitude,
            maximum_longitude=self.maximum_longitude,
            minimum_latitude=self.minimum_latitude,
            maximum_latitude=self.maximum_latitude,
            start_datetime=self.start_datetime,
            end_datetime=self.end_datetime,
            output_filename=self.output_path,
        )
        logging.info("✅ Download succesful.")


def get_copdataset(request):
    '''
    Get the .netcdf dataset from Copernicus Marine Service. 
    - request : (class CopernicusRequest)

    Returns ds : dataset from .netcdf output. 
    '''
    
    request.fetch() #Download the data

    ds = xr.open_dataset(request.output_path) # Open the downloaded .netcdf file
    logging.info(print(ds))

    return ds



def get_cdsdataset(dataset,request):
    client = cdsapi.Client()
    ds = client.retrieve(dataset, request).download()
    return ds