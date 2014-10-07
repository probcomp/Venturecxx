screen -S x11vnc -d -m x11vnc -forever -create

screen -S bokeh -d -m bokeh-server

cd /root/Venturecxx/examples

screen -S ipy_nb -d -m ipython notebook

/bin/bash
