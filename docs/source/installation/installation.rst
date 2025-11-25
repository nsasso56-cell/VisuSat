Installation
============

This page explains how to install **VisuSat** and prepare your environment.

Prerequisites
-------------

- Python 3.9 or higher
- A virtual environment (recommended)
- Git installed on your system

Install VisuSat
---------------

VisuSat is available on PyPl:

.. code-block:: bash

   pip install visusat

This will directly install visusat as a Python package with required dependencies.

Verify the installation:

.. code-block:: bash

   python -c "import visusat; print(visusat.__version__)"

Development installation
------------------------

You can also install Visusat as a GitHub project for development : 

.. code-block:: bash

   git clone https://github.com/nsasso56-cell/VisuSat
   cd VisuSat
   uv sync

This will create a virtual environment (``.venv/``) and install all required packages.

Activate the environment:

.. code-block:: bash

   source .venv/bin/activate

Verify the installation:

.. code-block:: bash

   python -c "import visusat; print(visusat.__version__)"

Optional: Install extra tools
-----------------------------

To build the documentation locally:

.. code-block:: bash

   uv pip install -r docs/requirements.txt
   make -C docs html

Next steps
----------

- Configure EUMETSAT & Copernicus credentials: :doc:`credentials`
- Explore the API reference
- Run example scripts in ``examples/``