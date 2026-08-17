# ── Base image ───────────────────────────────────────────────
FROM python:3.12-slim

# ── System dependencies ───────────────────────────────────────
# Required for mysql-connector-python and psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ───────────────────────────────
# Copy requirements first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project files ────────────────────────────────────────
COPY . .

# ── Install CLI command ───────────────────────────────────────
RUN pip install --no-cache-dir -e .

# ── Expose API port ───────────────────────────────────────────
EXPOSE 8000

# ── Start the API server ──────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
