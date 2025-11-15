# 🛰️ VisuSat project : 

[![Documentation Status](https://readthedocs.org/projects/visusat/badge/?version=latest)](https://visusat.readthedocs.io/en/latest/)
![Python Versions](https://img.shields.io/badge/python-3.9+-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

VisuSat is a Python toolkit for visualising, handling and processing satellite and oceanographic data, with dedicated pipelines for :

- **EUMETSAT Data Store & Data Tailor**
- **Copernicus Marine Service (CMEMS)**

It provides high-level wrappers around `eumdac`, `copernicusmarine`, `xarray`,  
and advanced visualisation utilities using `cartopy` and `matplotlib`.

📘 Full documentation: https://visusat.readthedocs.io/en/latest/

# 🌍 Examples of Visualisations :

## 🌦️ EUMETSAT Data Store - AMVs (Atmospheric Motion Vectors)

Derived from MTG-FCI Level 2 wind products :

<p align="center">
  <img src="examples/images/example_AMVs_FCI2.png" width="420">
  <img src="examples/images/zoom_exampleAMVs_FCI2.png" width="420">
</p>
## 🌊 Copernicus Marine Service

Allows to download and visualize available datasets from Copernicus Marine datastore  (https://data.marine.copernicus.eu/products). 

Example of the the Sea Level Anomaly (in meter) from an aggregate of all available satellites data into Global Ocean Gridded Level4 product ([link](https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_NRT_008_046/description)) :

### 🌐 Global Ocean Gridded Sea Level Anomaly (L4)

Product: [SEALEVEL_GLO_PHY_L4_NRT_008_046](https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_NRT_008_046/description)

<p align="center">
  <img src="exmaples/images/example_Copernicus_allsatellitesGlobalOceanGridded_ssh_%20sealevelanomaly.png" width="700">
</p>

### 🌀 Global Ocean Physics (Mercator Ocean)

Hourly Sea Water Potential Temperature —  
Product: [GLOBAL_ANALYSISFORECAST_PHY_001_024](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description)

<p align="center">
  <img src="exmaples/images/example_Copernicus_GOPhysicsOutputs_hourlymean_sst.png" width="700">
</p>

---

# 🚀 Installation :

Clone the repository an install dependencies in virtual environnement :

```bash
git clone https://github.com/nsasso56-cell/VisuSat
cd VisuSat
uv sync
```

Or install with pip :

```bash
pip install requirements.txt
```

Or installe the package in editable mode :

```bash
pip install -e .
```

---
# 💡 Quick Start Examples

Here is a minimal example showing how to download and plot a Copernicus Marine dataset:

```python
from visusat import copernicus

request = copernicus.CopernicusRequest(
    dataset_id="cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
    variables=["sla", "err_sla"],
    minimum_longitude=1,
    maximum_longitude=359,
    minimum_latitude=-70,
    maximum_latitude=80,
    start_datetime="2025-10-22T00:00:00",
    end_datetime="2025-10-22T00:00:00",
    output_filename="duacs_sla.nc",
)

ds = copernicus.get_copdataset(request)

# Plot all fields
copernicus.plot_copdataset(request, ds)

# Plot surface currents
copernicus.plot_currents(request, ds, vectors=False)
```

More examples are available in the examples/ folder.

---

# 🛠️ Features

- High-level wrappers for Copernicus Marine API
- Automation of EUMETSAT Data Tailor workflows
- Built-in plotting functions (AMVs, radiances, currents…)
- Dataset registry and metadata helpers
- Strong logging system
- Full Sphinx documentation (ReadTheDocs)

---

# 📁 Project Structure

```text
VisuSat/
├── pyproject.toml
├── README.md
├── src/
│   └── visusat/
│       ├── copernicus.py
│       ├── eumetsat.py
│       ├── utils.py
│       └── eumetsat_products_registry.py
├── docs/
│   └── source/
├── examples/
│   ├── demo_copernicus_globmodel.py
│   ├── demo_eumetsat_datatailor.py
│   └── images/
└── data/
    ├── copernicus/
    └── eumetsat/
```

---

# 📬 Contact

Author : Nicolas SASSO.
- e-mail : [n.sasso56@gmail.com](mailto:n.sasso56@gmail.com)
- LinkedIn : [linkedin.com/in/nicolas-sasso-6356ab172](http://www.linkedin.com/in/nicolas-sasso-6356ab172)

---

# 📄 License

Distributed under the MIT License.