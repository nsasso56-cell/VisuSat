import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# chemin vers le fichier de registre
REGISTRY_PATH = Path(
    os.path.join(
        Path(__file__).resolve().parent.parent.parent, "data", "eumetsat_products.json"
    )
)


@dataclass
class Product:
    collection_id: str
    name: str
    level: str
    n_categories: int
    description: str = ""


PRODUCTS: Dict[str, Product] = {}


def load_registry():
    """Charge les produits depuis le JSON (si présent)."""
    if not REGISTRY_PATH.exists():
        return
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for coll_id, attrs in data.items():
        PRODUCTS[coll_id] = Product(**attrs)
    logger.info("EUMETSAT registry loaded")


def save_registry():
    """Save actual registry in JSON."""
    REGISTRY_PATH.parent.mkdir(exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {cid: asdict(prod) for cid, prod in PRODUCTS.items()},
            f,
            indent=2,
            ensure_ascii=False,
        )


def register_product(product: Product):
    """Add or update a EUMETSAT product, then save."""
    load_registry()
    PRODUCTS[product.collection_id] = product
    save_registry()


register_product(
    Product(
        collection_id="EO:EUM:DAT:0665",
        name="MTG-FCI High Resolution image - 0degree",
        level="L1c",
        n_categories=4,
        description="FCI Level 1c High Resolution Image Data - MTG - 0 degree",
    )
)
