
<p align="center">
  <img src="https://raw.githubusercontent.com/nsasso56-cell/VisuSat/main/docs/source/_static/logo_visusat.png" width="300">
</p>

# 🛰️ VisuSat project : 

[![Documentation Status](https://readthedocs.org/projects/visusat/badge/?version=latest)](https://visusat.readthedocs.io/en/latest/)
![Python Versions](https://img.shields.io/badge/python-3.9+-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/visusat.svg)](https://pypi.org/project/visusat/)

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
  <img src="https://raw.githubusercontent.com/nsasso56-cell/VisuSat/main/examples/images/example_AMVs_FCI2.png" width="420">
  <img src="https://raw.githubusercontent.com/nsasso56-cell/VisuSat/main/examples/images/zoom_exampleAMVs_FCI2.png" width="420">
</p>

## 🌊 Copernicus Marine Service

Allows to download and visualize available datasets from Copernicus Marine datastore  (https://data.marine.copernicus.eu/products). 

Example of the the Sea Level Anomaly (in meter) from an aggregate of all available satellites data into Global Ocean Gridded Level4 product ([link](https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_NRT_008_046/description)) :

### 🌐 Global Ocean Gridded Sea Level Anomaly (L4)

Product: [SEALEVEL_GLO_PHY_L4_NRT_008_046](https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_NRT_008_046/description)

<p align="center">
  <img src="https://raw.githubusercontent.com/nsasso56-cell/VisuSat/main/examples/images/example_Copernicus_allsatellitesGlobalOceanGridded_ssh_%20sealevelanomaly.png" width="700">
</p>

### 🌀 Global Ocean Physics (Mercator Ocean)

Hourly Sea Water Potential Temperature —  
Product: [GLOBAL_ANALYSISFORECAST_PHY_001_024](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description)

<p align="center">
  <img src="https://raw.githubusercontent.com/nsasso56-cell/VisuSat/main/examples/images/example_Copernicus_GOPhysicsOutputs_hourlymean_sst.png" width="700">
</p>

## 📽️ Animation from MTG-FCI L1c products

Effective radiance from Visible 0.6µm channel, over Western Europe, between 12UTC and 18UTC the 22/10/2025.
Product : [FCI L1c High Resolution Image Data - MTG](https://data.eumetsat.int/product/EO:EUM:DAT:0665)

The 0.6 µm visible channel of MTG FCI is a solar-reflectance channel that is sensitive to surface albedo, clouds (primarily their upper layers), and aerosols. Oceanic and continental surfaces tend to absorb most of the incoming solar radiation, leading to low radiances (dark tones), whereas clouds and aerosols reflect sunlight efficiently, resulting in high radiances (bright tones). In this image, the Benjamin depression is visible over the Atlantic Ocean and is characterized by a vortex-shaped pattern of enhanced radiances associated with thick cloud structures.

<p align="center">
  <img src="https://raw.githubusercontent.com/nsasso56-cell/VisuSat/dev/examples/images/animation.gif" width="420">
</p>

---

# 🚀 Installation :

VisuSat is available on PyPI:

```bash
pip install visusat
```

For devellopment :

```bash
git clone https://github.com/nsasso56-cell/VisuSat
cd VisuSat
pip install -e .
```

## 🔧 Upgrade VisuSat

```bash
pip install --upgrade visusat
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

ds = copernicus.load_dataset(request, force=False)

# Plot all fields
copernicus.plot_fields(request, ds)

# Plot surface currents
copernicus.plot_currents(request, ds, vectors = False)
```

More examples are available in the examples/ folder.

---

# 🛠️ Features

- High-level wrappers for Copernicus Marine API
- Automation of EUMETSAT Data Tailor workflows
- Built-in plotting functions (AMVs, radiances, currents…)
- Utilities for generating animated visualizations of satellite data.
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
│       ├── plotting.py
│       └── eumetsat_products_registry.py
├── docs/
│   └── source/
├── examples/
│   ├── demo_copernicus_globmodel.py
│   ├── demo_eumetsat_datatailor.py
│   ├── demo_eumetsat_animation.py
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