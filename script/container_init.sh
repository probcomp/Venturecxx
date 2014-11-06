#!/bin/bash
# To modify what runs in your container, see /script/supervisord.conf
cp ./script/supervisord.conf /etc/supervisor/conf.d/supervisord.conf  # Define processes to run
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf # Start supervisor daemon
/bin/bash 