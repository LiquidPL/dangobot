FROM python:3.11-alpine as build

RUN apk add --update build-base musl libc6-compat bash ca-certificates libffi libffi-dev libpq libpq-dev shadow git
RUN pip install pipenv

FROM build as build-venv

RUN mkdir /dangobot
WORKDIR /dangobot

COPY ./Pipfile ./Pipfile.lock /dangobot/

RUN PIPENV_VENV_IN_PROJECT=1 PIPENV_IGNORE_VIRTUALENVS=1 pipenv sync

FROM build-venv as build-main

COPY dangobot /dangobot/dangobot/
COPY manage.py /dangobot/
COPY docker/insert_version.sh /dangobot/docker/

RUN mkdir /dangobot/media && mkdir /dangobot/logs

RUN /dangobot/docker/insert_version.sh
RUN rm -rf /dangobot/docker

# remove .git directory as it was only needed to retrieve the commit hash
RUN rm -rf .git

FROM python:3.11-alpine as base

LABEL org.opencontainers.image.source=https://github.com/LiquidPL/dangobot

RUN apk add --update musl libc6-compat ca-certificates libffi libpq shadow \
    && useradd -m dangobot \
    && apk del shadow \
    && rm -rf /var/cache/apk/* \
    && mkdir -p /dangobot/media \
    && chown -R dangobot:dangobot /dangobot

USER dangobot
WORKDIR /dangobot

COPY --from=build-main --chown=dangobot:dangobot /dangobot /dangobot

CMD sh -c "source /dangobot/.venv/bin/activate && ./manage.py migrate && ./manage.py startbot"
