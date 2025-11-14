EUMETSAT Data Tailor Example (MTG-FCI)
======================================

This example demonstrates how to:

- Authenticate to the **EUMETSAT Data Store (EUMDAC)**,
- Search for **MTG-FCI Level 1C High Resolution** products,
- Submit a **Data Tailor customisation** request (GeoTIFF export),
- Download the customised product,
- Open the GeoTIFF with ``rioxarray`` and visualise it,
- Analyse the radiance statistics using :func:`visusat.utils.stats_dataset`.

.. note::

   This example uses operational MTG-FCI data and requires a valid EUMDAC
   API key stored locally in ``inputs/id_EUMETSAT.json``.
   A template version is available in ``inputs/id_EUMETSAT_template.json``.


.. literalinclude:: ../../../examples/demo_eumetsat_customisation.py
   :language: python
   :linenos:
   :caption: Example script for downloading and plotting MTG-FCI data via the EUMETSAT Data Tailor.
   :name: example-eumetsat-datatailor
