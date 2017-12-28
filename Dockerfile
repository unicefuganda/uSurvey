FROM python:2.7-alpine

RUN export LC_ALL=en_US.UTF-8
RUN export LANG=en_US.UTF-8

# Copy in your requirements file
ADD pip-requires.txt /pip-requires.txt

# Install host server dependencies.
RUN set -ex \
    && apk add  --update alpine-sdk \
            gcc \
            g++ \
            make \
            libc-dev \
            musl-dev \
            linux-headers \
            pcre-dev \
            libpq \
            postgresql-dev \
            git \
            libxml2-dev \
            libxslt-dev \
            zlib-dev \
            libffi-dev \
            postgresql-client

# now install python specific dependencies
RUN  LIBRARY_PATH=/lib:/usr/lib /bin/sh -c "pip install -U pip" \
    && LIBRARY_PATH=/lib:/usr/lib /bin/sh -c "pip install -r /pip-requires.txt"


# Copy application code to the container
RUN mkdir /src/
WORKDIR /src/
ADD . /src/

# create directory for odk files
RUN mkdir -p /src/files/submissions/
RUN mkdir -p /src/files/answerFiles/

# create log dir
RUN mkdir -p /src/logs

# setup the project
RUN cp survey/interviewer_configs.py.example survey/interviewer_configs.py

# Add any custom, static environment variables needed by Django or your settings file here:
ENV DJANGO_SETTINGS_MODULE=mics.settings
RUN DATABASE_URL=none python manage.py collectstatic --noinput


# Make entry point executable
RUN chmod +x /src/docker_entrypoint.sh

#define entry point
ENTRYPOINT ["/src/docker_entrypoint.sh"]
