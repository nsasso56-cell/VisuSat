"""
VisuSat: Tools for accessing, processing, and visualizing satellite and oceanographic data.

Modules:
- copernicus: Download and plot CMEMS datasets
- eumetsat: Access and customize EUMETSAT / DataTailor data
- utils: Common utilities for radiance, currents, plotting, datasets
- eumetsat_products_registry: Register and load known EUMETSAT products
"""

from importlib.metadata import PackageNotFoundError, version

# from .plotting import plot_field

__all__ = ["copernicus", "eumetsat", "utils", "eumetsat_products_registry", "plotting"]

try:
    __version__ = version("visusat")
except PackageNotFoundError:
    __version__ = "0.0.0"
