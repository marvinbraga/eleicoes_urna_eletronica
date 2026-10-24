FROM python:3.15.1-slim-bookworm AS python

FROM python AS python-build-stage

COPY --from=ghcr.io/astral-sh/uv:0.11.27 /uv /uvx /bin/

RUN apt-get update && apt-get install --no-install-recommends -y \
   build-essential \
   && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV UV_PYTHON_DOWNLOADS=never

COPY ./pyproject.toml ./uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project --python /usr/local/bin/python

FROM python AS python-run-stage

ARG APP_HOME=/app
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV=/app/.venv

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install --no-install-recommends -y \
    libpq-dev \
    gettext \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-build-stage /app/.venv /app/.venv

# Copie o restante do código da aplicação para o diretório de trabalho
COPY . .

# Comando para iniciar o backend
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7000"]
