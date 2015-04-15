VentureJSRIPL
=============

A Javascript client for the Venture RIPL, and a collection of web demos for Venture.

Running
=======

First, start a venture server:

  $ venture server puma

Now start a demo:

  $ firefox graph_curve_fitting.html
  
You will be asked to pick a venture server. Select the second option.

The demos are

- graph_curve_fitting.html
- cluster_crp_mixture.html
  - currently broken for reasons unknown (crashes the Venture server
    or the client loop when trying to add a point)
- cmvn_crp_mixture.html
  - requires venture server lite
- gp_curve_fitting.html
  - requires starting the server with python gp_server.py in this directory
