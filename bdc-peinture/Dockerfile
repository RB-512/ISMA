FROM python:3.12-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Dépendances système
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Installer uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copier les fichiers de dépendances
COPY pyproject.toml uv.lock* ./

# Installer les dépendances (sans dev deps)
RUN uv sync --frozen --no-dev

# Copier le code
COPY . .

# Collecter les fichiers statiques
RUN uv run manage.py collectstatic --noinput --settings=config.settings.prod || true

# Port exposé
EXPOSE 8000

CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
