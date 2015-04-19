# Venture Plotter

This Hill curve demo shows off some of the capabilities of Venture in
an interactive manner. Users can plot points on a graph and watch as
the Venture-based model attempts to fit a Hill curve to the data.

## How to use

In addition to
[Flask](http://flask.pocoo.org/docs/0.10/installation/), this demo
requires
[Flask-SocketIO](https://flask-socketio.readthedocs.org/en/latest/),
which can be installed with `pip install flask-socketio`. Once this is
done, run `python server/server.py` from a command line to start the
server locally. The demo can be accessed by opening `web/Plotter.html`
in a browser. The demo should be fairly self-explanatory. Add and
remove points with *left click* and *alt + left click*,
respectively. Points can also be manually added and removed using the
input box at the right. Press *Start* to begin continuously asking the
server for samples.

## Design choices

Originally, the plotting interface was built using an HTML5
canvas. However, this was switched to SVG for several reasons that
make SVG easier to use. First, SVG automatically handles redraws and
updates, which can be expensive and hard to get right if done with
canvas. Additionally, testing SVG is much easier, as it can be done
with simple reflection instead of computer vision (i.e. you can
inspect all of the elements contained in the SVG object, but with the
canvas you can only look at individual pixels). Finally, SVG draws
cleaner curves, and overall appears sharper.

Server-side, I started with a RESTful HTTP-based implementation, but
quickly moved to using Websockets when it became apparent that HTTP
was slow and not fit for this cause. Websockets are better suited for
this kind of application where the client and server maintain a
constant connection and continuously send information back and
forth. Moreover, it offers better performance, and the Flask-SocketIO
implementation I used supports sessions, so multiple clients can
connect.

## Program layout

All code for rendering points and functions is in `web/LogPlotter.js`
("Log" referring to the fact that this displays the x-axis on a
logarithmic scale). It also handles conversion between graph and
displayed coordinates. `web/Plotter.html` displays the demo,
establishes a connection to the server, and handles data entered by
the client. `server/server.py` initializes the server and implements
all of the demo-specific methods needed to communicate with Venture
(connecting, adding/removing points, sampling, etc.).

The `Experimental` folders contain some alternative implementations of
the design choices listed above (e.g. a canvas-based plotter, an
HTTP-based server), but are largely incomplete.

## Possible improvements

I've experimented with two different sampling methods. In the method
currently implemented, the client sends a `sample` message every time
it wants a sample of inferred parameters, by default five times per
second. The server receives the message, pauses inference, takes the
samples, and returns them in a message. An alternative implementation
has the client send the server a single `startSample` message, which
tells the server to continuously send samples at a timed interval
until the server receives a `stopSample` message. I imagine this
second implementation could be much faster because the server does not
have to process so many client messages, but in practice it turned out
to be slower, so the current implementation is likely
inefficient. Another improvement to consider would be only returning a
sample if the data points have changed beyond some threshold since the
last sample was requested, which potentially lets the server send
fewer messages.

It is worthwhile checking that the server correctly garbage collects
session-specific data when a client disconnects, as I can't be certain
how Flask-SocketIO handles this, or whether Venture creates any
problems of its own in this area.

Finally, the `SECRET_KEY` in `server/server.py` should ideally be
moved to a configuration file instead of being inlined, as it should
be specific to the server instance running. Keeping it in the code is
fine for debugging, but potentially creates security issues.
