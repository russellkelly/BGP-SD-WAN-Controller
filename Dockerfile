FROM ubuntu:14.04

MAINTAINER Russell Kelly (russellkelly@mac.com)

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get install -qy --no-install-recommends wget python git
RUN apt-get install -qy openssh-server
RUN apt-get install -qy openssh-client
RUN apt-get install -qy python-pip
RUN apt-get install -qy python-dev
RUN apt-get install -qy libxml2-dev
RUN apt-get install -qy libxslt-dev
RUN apt-get install -qy libssl-dev
RUN apt-get install -qy libffi-dev
RUN apt-get install -qy sudo
RUN apt-get install -qy vim
RUN apt-get install -qy telnet
RUN apt-get clean
RUN pip install flask
RUN pip install git+https://github.com/Juniper/py-junos-eznc.git

RUN useradd -m demo && echo "demo:demo" | chpasswd && adduser demo sudo

USER root

RUN mkdir /home/demo/epe-demo
ENV HOME /home/demo/epe-demo
WORKDIR /home/demo/epe-demo


RUN git clone https://github.com/Exa-Networks/exabgp.git
WORKDIR /home/demo/epe-demo/exabgp
RUN git checkout master
RUN chmod +x setup.py
RUN sudo ./setup.py install
WORKDIR /home/demo/epe-demo
RUN chmod -R 777 .

EXPOSE 179
EXPOSE 5000

COPY exabgp.env /root/exabgp/etc/exabgp/exabgp.env
COPY exabgp.env /usr/local/etc/exabgp/exabgp.env
COPY app.py /home/demo/epe-demo/
COPY app.py /home/demo/epe-demo/
COPY app.py /home/demo/epe-demo/
COPY app.py /home/demo/epe-demo/

USER demo
