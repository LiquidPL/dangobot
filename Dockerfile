FROM python:3.9-alpine as build

RUN pip install pipenv

RUN apk add --update build-base musl libc6-compat bash ca-certificates python3 python3-dev libffi libffi-dev postgresql-dev shadow git

RUN mkdir /dangobot
WORKDIR /dangobot

COPY . /dangobot

RUN PIPENV_VENV_IN_PROJECT=1 pipenv sync

RUN /dangobot/docker/insert_version.sh

FROM python:3.9-alpine as base

LABEL org.opencontainers.image.source=https://github.com/LiquidPL/dangobot

RUN pip install --no-cache-dir pipenv
RUN apk add --update musl libc6-compat ca-certificates libffi libpq shadow \
    && rm -rf /var/cache/apk/*

RUN useradd -m dangobot \
    && apk del shadow \
    && mkdir -p /dangobot/media \
    && chown -R dangobot:dangobot /dangobot

USER dangobot
WORKDIR /dangobot

COPY --from=build --chown=dangobot:dangobot /dangobot /dangobot

CMD sh -c "pipenv run ./manage.py migrate && pipenv run ./manage.py startbot"
