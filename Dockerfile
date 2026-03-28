ARG PYTHON_VERSION=3.13
ARG UV_VERSION=0.10.0

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_NO_DEV=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=/app/pyproject.toml,readonly \
    --mount=type=bind,source=uv.lock,target=/app/uv.lock,readonly \
    --mount=from=uv,source=/uv,target=/bin/uv,readonly \
    uv sync --locked --no-install-project --no-editable

COPY LICENSE /app/LICENSE
COPY README.md /app/README.md

COPY src /app/src
COPY pyproject.toml uv.lock /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=from=uv,source=/uv,target=/bin/uv,readonly \
    uv sync --locked --no-editable


FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv

USER appuser
WORKDIR /app

ENTRYPOINT ["python", "-m", "app"]
