FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
LABEL org.opencontainers.image.authors="Michael Gebetsroither <m.gebetsr@gmail.com>"

RUN mkdir -p /app

COPY README.md \
    ta-helper.py \
    ta-helper-trigger.py \
    pyproject.toml \
    uv.lock /app

WORKDIR /app

RUN uv sync --frozen --compile-bytecode
