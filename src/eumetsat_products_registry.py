import json
import os
import logging
from dataclasses import dataclass, asdict
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)
# chemin vers le fichier de registre
REGISTRY_PATH = Path(os.path.join(Path(__file__).resolve().parent.parent, "data", "eumetsat_products.json"))

@dataclass
class Product:
    collection_id : str
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
            ensure_ascii=False
        )


def register_product(product: Product):
    """Add or update a EUMETSAT product, then save."""
    load_registry()
    PRODUCTS[product.collection_id] = product
    save_registry()



register_product(Product(
    collection_id="EO:EUM:DAT:MSG:AMV",
    name="Atmospheric Motion Vectors",
    level="L2",
    n_categories=3,
    description="AMV product derived from SEVIRI imagery"
))