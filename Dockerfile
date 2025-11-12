FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
LABEL org.opencontainers.image.authors="Michael Gebetsroither <m.gebetsr@gmail.com>"

RUN mkdir -p /app

COPY README.md \
    ta-helper.py \
    ta-helper-trigger.py \
    pyproject.toml \
    uv.lock /app

WORKDIR /app

RUN set -ex \
    && uv sync --frozen --compile-bytecode \
    && uv sync --locked # check if uv.lock file is up-to-date
