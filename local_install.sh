#!/bin/sh
sudo pip install -r requirements.txt
sudo CC="ccache gcc-4.8" python setup.py install
