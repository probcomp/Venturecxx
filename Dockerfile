# Dockerfile for Venture project:
# http://probcomp.csail.mit.edu/venture/
#
# install Docker:
# https://docs.docker.com/installation/#installation
#
# to generate the docker image (must run script/release-tarball first):
# sudo docker build -t probcomp/venture .
#
# to save/load the image to/from a tarball:
# sudo docker save -o venture.tar probcomp/venture
# sudo docker load -o venture.tar
#
# to start a container with an interactive shell:
# sudo docker run -t -i probcomp/venture
#

FROM        ubuntu:14.04

MAINTAINER  MIT Probabilistic Computing Project

# Add source code repository (assumed to be in parent directory)
ADD         ../venture-0.1.tgz /root/
WORKDIR     /root/Venturecxx/

# Install dependencies
RUN         apt-get update
RUN         apt-get install -y libboost-all-dev libgsl0-dev python-pip ccache libfreetype6-dev
RUN         pip install -U distribute
RUN         apt-get install -y python-pyparsing python-flask python-requests python-numpy python-matplotlib python-scipy python-zmq ipython
RUN         pip install -r requirements.txt
RUN         apt-get install -y python-pandas python-patsy
RUN         pip install ggplot

# Install Venture
RUN         python setup.py install

CMD         /bin/bash
