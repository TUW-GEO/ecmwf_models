FROM mambaorg/micromamba:1.3.1-alpine
MAINTAINER Wolfgang Preimesberger <wolfgang.preimesberger@geo.tuwien.ac.at>

USER root

RUN apk update && \
    apk upgrade && \
    apk add git && \
    apk add build-base && \
    apk add g++ && \
    apk add bsd-compat-headers && \
    apk add tiff

WORKDIR /app

COPY . /app

ARG MAMBA_DOCKERFILE_ACTIVATE=1

RUN micromamba install -y -n base -c conda-forge python=3.12 pygrib netcdf4 pyresample pykdtree
RUN pip install /app/.

RUN micromamba clean --all --yes

# Clean up the src code, as it is installed now
RUN rm -rf /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]