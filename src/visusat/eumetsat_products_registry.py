"""
EUMETSAT Product Registry
=========================

This module provides a lightweight registry for storing metadata about
EUMETSAT products used within VisuSat. It is primarily designed to:

- Record product information (collection ID, name, level, number of categories),
- Store this registry as a JSON file inside the ``data/`` directory,
- Reload the registry to reconstruct :class:`Product` objects,
- Provide helper functions to add, update, or retrieve registered products.

The registry is intentionally minimalistic and file-based to ensure transparency
and ease of manual editing.

Notes
-----
- No code is executed when the module is imported (important for ReadTheDocs).
- Users must explicitly call :func:`register_product` to add entries.
- The JSON file is stored at ``data/eumetsat_products.json``.
"""
# --- Standard library ---
import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

# --- Logger ---
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path to registry file
# ---------------------------------------------------------------------------
REGISTRY_PATH = Path(
    os.path.join(
        Path(__file__).resolve().parent.parent.parent, "data", "eumetsat_products.json"
    )
)

# ---------------------------------------------------------------------------
# Product dataclass
# ---------------------------------------------------------------------------
@dataclass
class Product:
    """
    Metadata for a single EUMETSAT product.

    Parameters
    ----------
    collection_id : str
        EUMETSAT collection identifier (e.g. ``"EO:EUM:DAT:0665"``).
    name : str
        Short descriptive name.
    level : str
        Product level (e.g. ``"L1c"`` or ``"L2"``).
    n_categories : int
        Number of categories in the dataset (if applicable).
    description : str, optional
        Longer textual description.
    """
    collection_id: str
    name: str
    level: str
    n_categories: int
    description: str = ""


PRODUCTS: Dict[str, Product] = {}


def load_registry() -> None:
    """
    Load registry contents from the JSON file (if it exists).

    This populates the global :data:`PRODUCTS` dictionary.
    """
    if not REGISTRY_PATH.exists():
        logger.info("No registry file found. Initial registry is empty.")
        return
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for coll_id, attrs in data.items():
        PRODUCTS[coll_id] = Product(**attrs)
    logger.info("EUMETSAT registry loaded successfully.")


def save_registry() -> None:
    """
    Save the in-memory registry to the JSON file.

    Creates directories as needed.
    """
    REGISTRY_PATH.parent.mkdir(exist_ok=True)

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {cid: asdict(prod) for cid, prod in PRODUCTS.items()},
            f,
            indent=2,
            ensure_ascii=False,
        )
    
    logger.info("EUMETSAT registry saved.")

# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------


def register_product(product: Product) -> None:
    """
    Add or update a product in the registry and save to disk.

    Parameters
    ----------
    product : Product
        The product metadata to register.

    Notes
    -----
    Unlike earlier versions, this function is **not called at import time**.
    Users must call it explicitly.
    """
    load_registry()
    PRODUCTS[product.collection_id] = product
    save_registry()


# ---------------------------------------------------------------------------
# Optional example functions
# ---------------------------------------------------------------------------

def example_registry_entry() -> Product:
    """
    Returns an example product entry (not automatically registered).

    Useful for demonstration or tests.
    """
    return Product(
        collection_id="EO:EUM:DAT:0665",
        name="MTG-FCI High Resolution Image - 0 degree",
        level="L1c",
        n_categories=4,
        description="FCI Level 1c High Resolution Image Data - MTG - 0 degree",
    )
