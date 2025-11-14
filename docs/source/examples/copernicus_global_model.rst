Copernicus Global Ocean Model Example
=====================================

This example demonstrates how to:

- Build a request to the **Copernicus Marine Service (CMEMS)**,
- Download a subset of the **global ocean physics model**,
- Visualise physical fields (salinity, temperature, SSH, currents),
- Plot surface currents with and without vectors,
- Save diagnostic plots automatically.

The example uses the :class:`visusat.copernicus.CopernicusRequest` class and high-level plotting utilities.

.. literalinclude:: ../../../examples/demo_copernicus_globmodel.py
   :language: python
   :linenos:
   :caption: Example script for downloading and plotting CMEMS global model data.
   :name: example-copernicus-global-ocean
