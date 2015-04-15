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

GP Demo
=======

The Gaussian Process demo is a bit non-standard; instead of starting a server yourself, use the provided script:

  $ python gp_server.py

Then start the demo as usual:

  $ firefox gp_curve_fitting.html
