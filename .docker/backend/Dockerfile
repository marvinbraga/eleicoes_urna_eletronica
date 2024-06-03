FROM python:3.10-slim-bookworm as python

FROM python as python-build-stage

RUN apt-get update && apt-get install --no-install-recommends -y \
   build-essential

COPY ./pyproject.toml ./

RUN apt-get update -y && apt-get upgrade -y

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry export --without-hashes -f requirements.txt -o requirements.txt && \
    pip uninstall -y poetry

RUN pip wheel --wheel-dir /usr/src/app/wheels \
   -r requirements.txt

FROM python as python-run-stage

ARG APP_HOME=/app
ENV PYTHONPATH /app

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install --no-install-recommends -y \
    libpq-dev \
    gettext \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-build-stage /usr/src/app/wheels /wheels/

RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
   && rm -rf /wheels/

# Copie o restante do código da aplicação para o diretório de trabalho
COPY . .

# Comando para iniciar o backend
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7000"]
