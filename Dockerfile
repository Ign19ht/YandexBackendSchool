###############################################
# Base Image
###############################################
FROM python:3.9-slim as python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$VENV_PATH/bin:$PATH"

###############################################
# Builder Image
###############################################
FROM python-base as builder-base

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    build-essential

WORKDIR $PYSETUP_PATH
RUN python -m venv $VENV_PATH
COPY ./requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

###############################################
# Production Image
###############################################
FROM python-base as production
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

COPY ./docker-entrypoint.sh /prod/docker-entrypoint.sh
#COPY ./alembic.ini /prod/alembic.ini
#COPY ./migrations /prod/migrations
COPY backend/db_manager.py /prod/db_manager.py
COPY backend/models.py /prod/models.py
COPY backend/schemas.py /prod/schemas.py
COPY backend/crud.py /prod/crud.py
COPY backend/main.py /prod/main.py
RUN chmod +x /prod/docker-entrypoint.sh

WORKDIR /prod

ENTRYPOINT ./docker-entrypoint.sh $0 $@