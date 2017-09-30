FROM python:2.7-alpine

# Copy in your requirements file
ADD pip-requires.txt /pip-requires.txt

# Install build deps, then run `pip install`, then remove unneeded build deps all in a single step. Correct the path to your production requirements file, if needed.
RUN set -ex \
    && apk add  --update alpine-sdk --no-cache \
            gcc \
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
            postgresql-client \
    && LIBRARY_PATH=/lib:/usr/lib /bin/sh -c "pip install -U pip" \
    && LIBRARY_PATH=/lib:/usr/lib /bin/sh -c "pip install -r /pip-requires.txt"


# Copy application code to the container
RUN mkdir /src/
WORKDIR /src/
ADD . /src/

# setup the project
RUN cp survey/interviewer_configs.py.example survey/interviewer_configs.py

# Gunicorn will listen on this port
EXPOSE 8080 8082 9001

RUN export LD_LIBRARY_PATH=/usr/local/pgsql/lib:$LD_LIBRARY_PATH

# Add any custom, static environment variables needed by Django or your settings file here:
ENV DJANGO_SETTINGS_MODULE=mics.settings

# Make entry point executable
RUN chmod +x /src/docker_entrypoint.sh

#define entry point
ENTRYPOINT ["/src/docker_entrypoint.sh"]
