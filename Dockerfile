FROM alpine:latest

RUN apk add --update \
        build-base musl libc6-compat bash ca-certificates python3 python3-dev libffi libffi-dev postgresql-dev shadow git \
    && useradd -m dangobot \
    && apk del shadow \
    && easy_install-3.6 pip \
    && pip install --upgrade pip \
    && pip install pipenv \
    && rm -rf /var/cache/apk/*

RUN mkdir /dangobot \
    && chown dangobot:dangobot /dangobot

COPY . /dangobot

RUN mkdir /dangobot/media \
    && chown -R dangobot:dangobot /dangobot

USER dangobot

WORKDIR /dangobot

RUN cp settings.py.docker settings.py \
    && pipenv sync

CMD sh -c "pipenv run ./manage.py migrate && pipenv run ./manage.py startbot"
