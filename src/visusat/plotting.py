"""
Plotting utilities for VisuSat.

This module centralizes all visualization functions, ensuring that
Cartopy/Matplotlib dependencies do not pollute data-access modules
(Copernicus, EUMETSAT, …).
"""

from __future__ import annotations

# --- Standard library ---
import logging
from pathlib import Path
from typing import Optional, Sequence, Tuple


import numpy as np

# --- Logger ---
logger = logging.getLogger(__name__)

def _require_matplotlib():
    try:
        import matplotlib.pyplot as plt
        from mpl_toolkits.axes_grid1 import make_axes_locatable
    except ImportError:
        raise ImportError("Matplotlib is required for plotting.")
    return plt, make_axes_locatable


def _require_cartopy():
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
    except ImportError:
        raise ImportError("Cartopy is required for plotting maps.")
    return ccrs, cfeature


# -----------------------------------------------------------------------------
# Generic geophysical field plotting
# -----------------------------------------------------------------------------
def plot_field(
    lon: np.ndarray,
    lat: np.ndarray,
    val: np.ndarray,
    *,
    title: str = "",
    subdomain: Optional[Sequence[float]] = None,
    cmap : str = "Spectral_r",
    cbar_label:str = "unknown",
    figsize: tuple = (12, 6),
    dpi : int = 200, 
    proj=None,
    show_coastlines: bool = True,
    show_borders: bool = True,
    coast_resolution: str = "110m",
    shading: str = "auto",
    savepath: Optional[str] = None,
    saveformat: str = "png",
) -> Tuple["Figure", "Axes"]:
    """
    Plot a geophysical field on a map using Cartopy.

    This function generates a 2D colormesh plot of a field defined on a regular
    longitude–latitude grid. It supports global plots as well as regional zooms,
    and includes coastlines, borders, and custom colorbar formatting. The output
    figure can optionally be saved to disk.

    Parameters
    ----------
    lon, lat : 2D np.ndarray
        Geographic grids.
    val : 2D np.ndarray
        Field to plot.
        2D data field to plot (e.g. radiance, SST, wind speed).
    title : str, optional
        Figure title. Defaults to an empty string.
    subdomain : list of float, optional
        Geographic extent specified as ``[lon_min, lon_max, lat_min, lat_max]``.
        If provided, the plot is zoomed to this region. Defaults to None.
    cmap : str, optional
        Matplotlib colormap name. Defaults to ``"Spectral_r"``.
    cbar_label : str, optional
        Label for the colorbar. Defaults to ``"unknown"``.
    figsize : tuple, optional
        Figure size in inches. Default ``(12, 6)``.
    dpi : int, optional
        Resolution of output figure. Default ``200``.
    proj : cartopy.crs.Projection, optional
        Map projection for the plot. Defaults to ``ccrs.PlateCarree()``.
    show_coastlines : bool, optional
        Whether to draw coastlines. Default True.
    show_borders : bool, optional
        Whether to draw national borders. Default True.
    coast_resolution : str, optional
        Resolution for coastlines. Default ```"110m"```.
    shading : str, optional
        pcolormesh shading. Default ```"auto"```
    savepath : str or path-like, optional
        Path where the figure will be saved. If None, the figure is only returned.
        Defaults to None.
    saveformat : str, optional
        Output format for saving (e.g. ``"png"``, ``"pdf"``). Defaults to ``"png"``.

    Returns
    -------
    tuple
        A tuple ``(fig, ax)`` where:
            - ``fig`` is the created Matplotlib figure.
            - ``ax`` is the Cartopy GeoAxes object.

    Notes
    -----
    - ``lon`` and ``lat`` must match the shape of ``val``.
    - ``subdomain`` must follow Plate Carrée coordinates.
    - If ``savepath`` is provided, the figure is saved with the specified format.
    """
    plt, make_axes_locatable = _require_matplotlib()
    ccrs, cfeature = _require_cartopy()

    if val.shape != (lat.shape[0], lon.shape[0]):
        raise ValueError(
            f"Value field shape {val.shape} does not match "
            f"latitude ({lat.shape}) and longitude ({lon.shape})"
        )

    if proj is None :
        proj = ccrs.PlateCarree()

    logger.info(f"Plot figure with field {title}.")

    # --- Initiate figure ---
    fig = plt.figure(figsize=figsize)
    ax = plt.axes(projection=proj)
    ax.set_global() if subdomain is None else ax.set_extent(subdomain)
    im = ax.pcolormesh(
        lon, lat, val, transform=ccrs.PlateCarree(), cmap=cmap, shading="auto"
    )

    # --- Grid ---
    gl = ax.gridlines(draw_labels=True, linewidth=1, color="lightgray", linestyle="--")
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 8}
    gl.ylabel_style = {"size": 8}

    # --- Colorbar ---
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="2.5%", pad=0.3, axes_class=plt.Axes)
    cbar = plt.colorbar(im, cax=cax, orientation="horizontal", fraction=0.046)
    cbar.set_label(cbar_label)

    # Coastlines, borders
    if show_coastlines:
        ax.coastlines(resolution="110m", linewidth=0.6)
    if show_borders:
        ax.add_feature(cfeature.BORDERS, linewidth=0.4)

    # --- Subdomain if specified ---
    if subdomain is not None:
        ax.add_feature(
            cfeature.LAKES.with_scale("10m"), linewidth=0.3, edgecolor="gray"
        )
        ax.add_feature(
            cfeature.RIVERS.with_scale("10m"), linewidth=0.3, edgecolor="lightblue"
        )

    # --- Titles --- 
    if title:
        fig.suptitle(title)

    fig.tight_layout()

    # --- Save figure if savepath ---
    if savepath is not None:
        savepath = Path(savepath)
        savepath.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(savepath, format=saveformat, dpi=dpi, bbox_inches="tight")
        logger.info("-> Figure saved in {savepath}.")

    return fig, ax


__all__ = [
    "plot_field",
]