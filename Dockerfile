# syntax=docker/dockerfile:1.10
# check=error=true

FROM python:3.13-slim-bookworm AS base

WORKDIR /app

# Install common distro packages
RUN --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    <<EOF
    apt-get --quiet --yes update
    apt-get --quiet --yes install --no-install-recommends \
        build-essential \
        curl \
        git \
        libpq-dev
    apt-get --quiet -y autoremove
EOF

# Add user, group and create venv in home directory
ARG USERNAME=brownsea
ARG UID=1001
ARG GID=1001
ARG VIRTUAL_ENV=/venv
RUN <<EOF
    groupadd --gid $GID $USERNAME
    useradd --gid $GID --uid $UID --create-home $USERNAME
    python -m venv --upgrade-deps $VIRTUAL_ENV
    chown -R $UID:$GID /app $VIRTUAL_ENV
EOF

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set env for python
ENV \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=$VIRTUAL_ENV \
    PATH=$VIRTUAL_ENV/bin:$PATH

USER $USERNAME

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/home/$USERNAME/.cache/uv,uid=$UID,gid=$GID \
    <<EOF
    uv sync --frozen --no-dev --group prod
EOF

FROM node:22-slim AS node-deps

WORKDIR /build/
ENV CI=true

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm <<EOF
    npm ci --no-audit --progress=false
EOF

FROM node-deps AS vite-build

COPY vite.config.js ./
COPY ./brownsea/ ./brownsea/
RUN npm run build

FROM base AS app

ARG USERNAME=brownsea
ARG UID=1001
ARG GID=1001

ENV DJANGO_SETTINGS_MODULE=brownsea.core.settings.production \
    PORT=8000 \
    WORKER_COUNT=2 \
    PYTHONPATH=/app

COPY --chmod=755 --chown=$UID:$GID docker/entrypoint.sh docker/start.sh ./docker/
COPY --chown=$UID:$GID . .
COPY --chown=$UID:$GID --from=vite-build --link /build/brownsea/static/dist/ ./brownsea/static/dist/
RUN <<EOF
    django-admin collectstatic --noinput --clear
EOF

ENTRYPOINT ["./docker/entrypoint.sh"]