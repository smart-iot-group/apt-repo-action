FROM ubuntu:bionic

LABEL maintainer="tristan jakobi <t.jakobi@smart-iot.solutions>"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y reprepro gpg python3 python3-git python3-gnupg expect python3-debian python3-pip && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get install -y python-paramiko libffi-dev



COPY entrypoint.py /entrypoint.py
COPY key.py /key.py

ENTRYPOINT ["python3","/entrypoint.py"]
