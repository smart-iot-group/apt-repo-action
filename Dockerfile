FROM ubuntu:bionic

LABEL maintainer="tristan jakobi <t.jakobi@smart-iot.solutions>"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y reprepro gpg python3 openssh-client python3-gnupg python3-debian python3-pip && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip && \
    pip3 install paramiko scp

COPY entrypoint.py /entrypoint.py
COPY key.py /key.py

ENTRYPOINT ["python3","/entrypoint.py"]
