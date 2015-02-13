
Venture Terminal Documentation
-------------------------------

Code associated with the terminal:

All code needed for the Terminal is located in the VentureJSRIPL repository, in the Terminal subdirectory.

Spinning up  an EC2 instance and opening ports on the machines:

First, obtain EC2 credentials and generate a keypair. See Amazon Web Services for details on how to do this.

To spin up (and genearlly manage) EC2 machines, use StarCluster, which you can use to open ports on your instance.

First, install StarCluster:

With Ubuntu, run:
sudo apt-get install -y python-dev pip
sudo pip install starcluster

Second, create a ~/.starcluster/config file.  You can get a 'fresh' one by running
starcluster help
and choosing option 2: 'Write config template ...'. An example config file is in this directory, called ec2config_ex. 
Details on starcluster (starting your EC2 instance) can be found here:

http://star.mit.edu/cluster/

To open ports on your instance, you have to add the following to the permissions section (included in ec2config_ex):

[permission web]
from_port = 8080
to_port = 8080

[permission venture]
from_port = 1234
to_port = 1237

This opens port 8080 for web traffic and 1234-1237 for Venture.

Creating a terminal:

Setting up the EC2 environment to run Venture:

1. Log into an Amazon EC2 instance (use starcluster sshmaster <INSTANCE_NAME> if using starcluster).

2. Pull the Venture repository, python_refactor_2 branch, and the VentureJSRIPL repository, master branch.
You may have to install git onto your instance.

3. Install Venture on the EC2 instance using the following reference:

http://venture.csail.mit.edu/wiki/index.php5?title=Installation

How to run the Terminal from an EC2 instance

1. Once Venture is installed, begin the Venture Engine by running the following command:

python ~/Venture/python/scripts/run_server.py

This begins Venture through port 8082 by default. To change ports, simply amend run_server.py.
With the provided config file, you should set this to a value at or between 1234 and 1237.

2. An example Terminal is currently located at:

http://ec2-54-237-81-11.compute-1.amazonaws.com/

Upon loading, the Terminal will clear all directives. One can run Venture commands from the command line in the Terminal. The following Venture commands can be run in-line in the terminal:
     •	      assume
     •	      observe
     •	      predict
     •	      list_directives
     •	      start_continuous_inference
     •	      stop_continuous_inference
     •	      clear

Running examples in the Terminal

1. Select an example of Venture code form your computer (text only).

2. Click Load Example to send this example in the server. You should see the commands print inline in the Terminal. 

Creating a new example in the Terminal:

1. Simply create a text file with the appropriate code and load with the load function.

