screen -S x11vnc -d -m x11vnc -forever -create

mkdir /root/bokeh_data
cd /root/bokeh_data
screen -S bokeh -d -m bokeh-server --ip=0.0.0.0 --ws-port=5007 -D=/root/bokeh_data/

cd /root/Venturecxx/examples
screen -S ipy_nb -d -m ipython notebook

cd /root/Venturecxx

/bin/bash
