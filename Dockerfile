# Dockerfile for Venture project:
# http://probcomp.csail.mit.edu/venture/
#
# install Docker:
# https://docs.docker.com/installation/#installation
#
# to generate the docker image (from this directory, must run script/release-tarball first):
# sudo docker build -t probcomp/venture .
#
# to save/load the image to/from a tarball:
# sudo docker save probcomp/venture > venture-0.2-docker.tar
# cat venture-0.2-docker.tar | sudo docker load
#
# to start a container with an interactive shell (after generating or loading the image):
# sudo docker run -t -i probcomp/venture
#
# in order to use IPython notebook, expose port 8888:
# sudo docker run -t -i -p 8888:8888 probcomp/venture-summer-school
# (then run "ipcluster & ipython notebook" inside the container)
#
# in order to do graphical plotting, use VNC and expose port 5900:
# sudo docker run -t -i -p 5900:5900 probcomp/venture-summer-school
# (then run "x11vnc -forever -create" inside the container, and point a VNC client to localhost:5900)

FROM        ubuntu:14.04

MAINTAINER  MIT Probabilistic Computing Project

# Add source code repository (assumed to be in parent directory)
ADD         ../venture-0.2.tgz /root/
WORKDIR     /root/Venturecxx/

# Install dependencies
RUN         apt-get update
RUN         apt-get install -y libboost-all-dev libgsl0-dev python-pip ccache libfreetype6-dev
RUN         pip install -U distribute
RUN         apt-get install -y python-pyparsing python-flask python-requests python-numpy python-matplotlib python-scipy python-zmq ipython ipython-notebook
RUN         pip install -r requirements.txt
RUN         apt-get install -y python-pandas python-patsy
RUN         pip install ggplot

# Install Venture
RUN         python setup.py install

# IPython notebook configuration
RUN         ipython profile create --profile-dir=/.ipython/profile_default/
RUN         echo "c.NotebookApp.ip = '0.0.0.0'" >> /.ipython/profile_default/ipython_notebook_config.py
RUN         echo "c.NotebookApp.port = 8888" >> /.ipython/profile_default/ipython_notebook_config.py
RUN         echo "c.NotebookManager.notebook_dir = u'/root/Venturecxx/examples/tutorial/'" >> /.ipython/profile_default/ipython_notebook_config.py
EXPOSE      8888

# Install VNC (for graphical plotting)
RUN         apt-get install -y x11vnc xvfb

CMD         /bin/bash
