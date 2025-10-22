import cdsapi
import copernicusmarine
import xarray as xr
import logging
from typing import List, Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)
project_root = Path(__file__).resolve().parent.parent

class CopernicusRequest:
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
        extra_params: Optional[Dict[str, str]] = None
    ):
        self.dataset_id = dataset_id                # ex: "SEALEVEL_GLO_PHY_L4_MY_008_047"
        self.variables = variables                  # ex: ["sla", "adt"]
        self.start_datetime = start_datetime         # ex: "2025-01-01T00:00:00"
        self.end_datetime = end_datetime             # ex: "2025-01-10T00:00:00"
        self.minimum_latitude = minimum_latitude
        self.maximum_latitude = maximum_latitude
        self.minimum_longitude = minimum_longitude
        self.maximum_longitude = maximum_longitude
        self.output_filename = output_filename or "output.nc"
        self.extra_params = extra_params or {}


def get_copdataset(request):
    '''
    Get the .netcdf dataset from Copernicus Marine Service. 
    - request : (class CopernicusRequest)

    Returns ds : dataset from .netcdf output. 
    '''


    # Download dataset :
    copernicusmarine.subset(dataset_id=request.dataset_id,
    variables=request.variables,
    minimum_latitude=request.minimum_latitude,
    maximum_latitude=request.maximum_latitude,
    minimum_longitude=-request.minimum_longitude,
    maximum_longitude=request.maximum_longitude,
    start_datetime=request.start_datetime,
    end_datetime=request.end_datetime,
    output_filename=request.output_filename)    

    ds = xr.open_dataset(request.output_filename)

    return ds



def get_cdsdataset(dataset,request):
    client = cdsapi.Client()
    ds = client.retrieve(dataset, request).download()
    return ds