# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] - 2025-11-14
### Added
- First PyPI release 🎉
- Full documentation hosted on ReadTheDocs.
- EUMETSAT Data Tailor tools (`customisation`, `plot_amvs`, `plot_radiance`).
- Copernicus Marine request and dataset visualisation.
- Product registry system for EUMETSAT.
- Example scripts for Copernicus & EUMETSAT workflows.

### Changed
- Refactored project structure (`visusat` namespace).
- Improved module docstrings and Sphinx integration.

### Fixed
- Import issues in ReadTheDocs.


## [0.3.0] - 2025-11-16

 feature/api-standardization

### [Added]
New visusat.plotting module
- Centralizes all geospatial plotting utilities previously scattered across copernicus.py and eumetsat.py.
- Provides a robust, reusable plot_field() function with:
- Automatic cartopy/matplotlib lazy-loading
- Full control: subdomain, labels, shading, colorbar label, DPI, projection, etc.
- Built-in validation and safe file saving
- Professional defaults (Spectral_r, 110m coastlines)
- Includes internal helper functions: _require_matplotlib(), _require_cartopy()
Added public API export
- __all__ = ["plot_field"] inside plotting.py
- Added from .plotting import plot_field in visusat/__init__.py
Added sphinx documentation scaffold
- Created new file docs/source/src/plotting.rst with:

### [Unreleased]

## [0.3.1] - 2025-11-25

### [Fixed]
- Standardized function names across modules. 
- Fixed inconsistencies in plotting routines after 
- Adapt new modules to lazy-importing heavy dependencies for ReadTheDocs. 

### [Changed]
- Reorganised imports to follow VisuSat coding standards.
- Linting and formatting of package modules and examples scripts. 

### [Documentation]
- Updated examples scripts to fit nex API names.
- New README.md installation instructions (`pip install visusat`)
- Added missing modules references.
- New installation instructions in ReadTheDocs documentation (installation.rst).
- Fix minor ReadTheDocs inconsistencies. 


