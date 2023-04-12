# If the GPU support is not necessary, then another image,
# for example "python:3.7" can be used.
FROM nvidia/cuda:10.2-devel-ubuntu18.04

# By default, only the user guest/1000 with group 1000 will be created.
# Set the lines below with your users info
# e.g.: ARG DEAL_USER_IDS="<username1>/<userid1>,<username2>/<userid2>"
ARG DEAL_USER_IDS
# e.g.: ARG DEAL_GROUP_ID=<groupid>
ARG DEAL_GROUP_ID=${DEAL_GROUP_ID:-999}

RUN if [ ! -z $DEAL_USER_IDS ]; then \
echo "The following user(s) will be added to the container: \
$DEAL_USER_IDS, with group: docker/$DEAL_GROUP_ID"; fi

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

RUN groupadd -g $DEAL_GROUP_ID docker
ENV USER_IDS=$DEAL_USER_IDS",guest/1000"
COPY docker/utils.sh /tmp
RUN bash -c '. /tmp/utils.sh; create_users "${USER_IDS}" "docker"'

# Entry point
EXPOSE 8888
RUN mkdir /workdir && chmod a+rwX /workdir
COPY . /workdir/
WORKDIR /workdir
USER guest
ENTRYPOINT ["env"]
CMD ["bash", "-l"]
