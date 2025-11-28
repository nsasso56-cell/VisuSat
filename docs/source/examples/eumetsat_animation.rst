EUMETSAT animation example (MTG-FCI)
=====================================

This example demonstrates how to:

- Authenticate with EUMETSAT credentials.
- Search EUMETSAT products on a specific temporal window.
- Definition of EUMDAC Data Tailor Chain.
- Use :func:`visusat.eumetsat.download_custom_products` to **automatize Data Tailor customisation for
multiple products.**
- **Generate an animation** with :func:`visusat.plotting.animate_geotiff_sequence`.

.. literalinclude:: ../../../examples/demo_eumetsat_animation.py
   :language: python
   :linenos:
   :caption: Example script for generating Gif animation from MTG-FCI custom products.
   :name: example-eumetsat-animation