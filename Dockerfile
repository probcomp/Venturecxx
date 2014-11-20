# Dockerfile for Venture project:
# http://probcomp.csail.mit.edu/venture/
#
# install Docker:
# https://docs.docker.com/installation/#installation
#
# to generate the docker image (from this directory)
#   script/build_docker_image
# (which runs sudo docker build -t venture .)
#
# to start a container with an interactive shell (after generating or loading the image):
#   script/run_docker_container
# - IPython notebook server is exposed on port 8888
# - VNC server is exposed on port 5900
# See script/run_docker_container to configure
#
# to save/load the image to/from a tarball:
#   sudo docker save venture > venture-0.2-docker.tar
#   cat venture-0.2-docker.tar | sudo docker load

FROM        ubuntu:14.04

MAINTAINER  MIT Probabilistic Computing Project

# Install dependencies
RUN         apt-get update
RUN         apt-get install -y libboost-all-dev libgsl0-dev python-pip ccache libfreetype6-dev
RUN         pip install -U distribute
RUN         apt-get install -y python-pyparsing python-flask python-requests python-numpy python-matplotlib python-scipy python-zmq ipython ipython-notebook

# Install VNC (for graphical plotting) and other useful utilities
RUN         apt-get install -y x11vnc xvfb
RUN         apt-get install -y vim screen git supervisor
RUN 		mkdir -p /var/log/supervisor
#supervisord configuration file added in container_init.sh

# Add source code repository
# Moved this after dependency install to leverage build process caching
ADD         . /root/Venturecxx
WORKDIR     /root/Venturecxx/

RUN         sudo pip install -r requirements.txt
RUN         apt-get install -y python-pandas python-patsy
RUN         sudo pip install ipython --upgrade

# Install Venture
RUN         python setup.py install

# IPython notebook configuration
RUN         ipython profile create --profile-dir=/root/.ipython/profile_default/
RUN         echo "c.NotebookApp.ip = '0.0.0.0'" >> /root/.ipython/profile_default/ipython_notebook_config.py
RUN         echo "c.NotebookApp.port = 8888" >> /root/.ipython/profile_default/ipython_notebook_config.py
EXPOSE      8888

# Further configuration of container enviroment
RUN     echo "defshell -bash      # Set screen login shell to bash" >> ~/.screenrc
RUN     cp -f ./profile/matplotlibrc /etc/matplotlibrc # Changing backend to Agg
RUN     chmod 777 /var/run/screen

# Start processes as per /script/supervisord.conf and an interactive shell
CMD         ./script/container_init.sh
