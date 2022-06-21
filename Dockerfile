# If the GPU support is not necessary, then another image,
# for example "python:3.7" can be used.
FROM nvidia/cuda:10.2-devel-ubuntu18.04

# ENVs are visible both at image build time and container run time.
# We want the http proxys to be visible in both cases and therefore
# set them equal to the values of the ARGs.
ENV http_proxy=
ENV https_proxy=
ENV HTTP_PROXY=
ENV HTTPS_PROXY=

# Debian's default LANG=C breaks python3.
# See commends in the official python docker file:
# https://github.com/docker-library/python/blob/master/3.7/buster/Dockerfile
ENV LANG=C.UTF-8


RUN \
apt-get update &&\
apt-get upgrade -y --no-install-recommends &&\
DEBIAN_FRONTEND="noninteractive" \
apt-get install -y --no-install-recommends \
    libbluetooth3 libbz2-1.0 libc6 libexpat1 \
    libffi6 libgdbm5 liblzma5 libncursesw5 libreadline7 \
    libsqlite3-0 libssl1.1 tk xz-utils zlib1g \
    ffmpeg libsm6 libxext6 \
    gcc g++ build-essential make \
    curl git htop less man vim wget

# Install Python 3.7 & pip 3.7
# The base image ("nvidia/cuda") does not have Python pre-installed. The
# following command can be omitted on images that already have Python, for
# example "python:3.7".
RUN \
DEBIAN_FRONTEND="noninteractive" \
apt-get install -y --no-install-recommends \
python3.7-dev python3.7-venv python3-pip && \
python3.7 -m pip install --upgrade pip setuptools wheel && \
update-alternatives --install /usr/local/bin/python python /usr/bin/python3.7 0

# Install requirements
COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Entry point
EXPOSE 8888
RUN mkdir /workdir && chmod a+rwX /workdir
COPY . /workdir/
WORKDIR /workdir
ENTRYPOINT ["env"]
CMD ["bash", "-l"]