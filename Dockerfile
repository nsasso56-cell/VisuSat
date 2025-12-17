

FROM python:3.9-slim


# 4. Dossier de travail
WORKDIR /app

# 1. Dépendances système nécessaires à rasterio / GDAL
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    libgeos-dev \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Variables GDAL (important)
ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV GDAL_VERSION=3.6.2

# 2. Vérification explicite (debug-safe)
RUN which gdal-config && gdal-config --version

# Installer uv de manière fiable
RUN pip install --no-cache-dir uv

# 5. Copier les fichiers de dépendances en premier (cache Docker)
COPY pyproject.toml uv.lock ./

COPY . .

RUN uv sync --locked

CMD ["uv", "run", "python3", "examples/demo_eumetsat_animation.py"]