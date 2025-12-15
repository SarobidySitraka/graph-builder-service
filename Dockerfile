FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Installer uniquement les outils nécessaires pour décompresser
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    make \
    libaio1 \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer Oracle Instant Client
COPY instantclient-basic-linux.x64-23.26.0.0.0.zip /tmp/instantclient.zip
RUN unzip /tmp/instantclient.zip -d /opt/oracle \
    && ln -s /opt/oracle/instantclient_19_10 /opt/oracle/instantclient \
    && rm -f /tmp/instantclient.zip

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .

# Copy project files
COPY . .

# Install dependencies with uv
RUN uv sync --frozen --no-cache

EXPOSE 8000

# Set the default command
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]