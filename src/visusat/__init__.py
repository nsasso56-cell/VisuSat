"""
VisuSat: Tools for accessing, processing, and visualizing satellite and oceanographic data.

VisuSat provides a unified interface for working with multiple Earth observation
data sources, including:

- EUMETSAT Data Store and Data Tailor products (radiances, AMVs, FCI, MSG),
- Copernicus Marine Service (CMEMS) datasets and derived fields,
- Copernicus Climate Data Store (CDS) extractions,
- Generic utilities for NetCDF handling, plotting, and metadata processing.

The package includes:

- High-level request and download classes (e.g. ``CopernicusRequest``),
- Robust wrappers for dataset opening (``safe_open_dataset``),
- Diagnostic and plotting routines for geophysical fields,
- Helper tools for inspecting velocity fields, timestamps, and LaTeX-formatted labels.

VisuSat aims to provide a coherent, reproducible, and user-friendly workflow
for satellite and ocean data analysis in Python, leveraging xarray, cartopy,
copernicusmarine, cdsapi, and EUMDAC.
"""

__version__ = "0.2.0"
