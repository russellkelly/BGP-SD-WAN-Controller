FROM ubuntu:14.04

MAINTAINER Russell Kelly (russellkelly@mac.com)

RUN apt-get update && UBUNTU_FRONTEND=noninteractive
RUN apt-get install -qy --no-install-recommends wget python git
RUN apt-get install -qy openssh-server
RUN apt-get install -qy openssh-client
RUN apt-get install -qy python-pip
RUN apt-get install -qy python-dev
RUN apt-get install -qy libxml2-dev
RUN apt-get install -qy libxslt-dev
RUN apt-get install -qy libssl-dev
RUN apt-get install -qy libffi-dev
RUN apt-get clean
RUN pip install git+https://github.com/Juniper/py-junos-eznc.git

RUN mkdir /root/demo
ENV HOME /root/demo
WORKDIR /root/demo


RUN git clone https://github.com/Exa-Networks/exabgp.git
WORKDIR /root/demo/exabgp
RUN git checkout master
RUN chmod +x setup.py
RUN ./setup.py install
WORKDIR /root/demo


COPY exabgp.env /root/exabgp/etc/exabgp/exabgp.env
COPY exabgp.env /usr/local/etc/exabgp/exabgp.env
