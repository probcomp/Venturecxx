
Venture Terminal Documentation
-------------------------------

Code associated with the terminal:

All code needed for the Terminal is located in the VentureJSRIPL repository, in the Terminal subdirectory.

Creating a terminal:

Setting up the EC2 environment:

1. Log into an Amazon EC2 instance.

2. Pull the Venture repository, python_refactor_2 branch, and the VentureJSRIPL repository, master branch.

3. Install Venture on the EC2 instance using the following reference:

http://venture.csail.mit.edu/wiki/index.php5?title=Installation

How to run the Terminal from an EC2 instance

1. Once Venture is installed, begin the Venture Engine by running the following command:

python ~/Venture/python/scripts/run_server.py

This begins Venture through port 8082 by default. To change ports, simply amend run_server.py.

2. An example Terminal is currently located at:

http://ec2-54-224-249-120.compute-1.amazonaws.com

Upon loading, the Terminal will clear all directives. One can run Venture commands from the command line in the Terminal. The following Venture commands can be run in-line in the terminal:
     •	      assume
     •	      observe
     •	      predict
     •	      list_directives
     •	      start_continuous_inference
     •	      stop_continuous_inference
     •	      clear

Running examples in the Terminal

1. Select an example from the radio buttons at the top of the page.

2. Click Load Example to send this example in the server. You should see the commands print inline in the Terminal. 

Creating a new example in the Terminal (This might change if the load function changes)

1. Create a text file with the example script in the directory index.html is located, i.e. put trickycoin.txt in /var/www in the EC2 instance.

2. Amend the radio buttons in index.html, where the value is the name of the text file, minus the ".txt" extension. The terminal will look for example_name.txt where example_name is the value field of the radio button.
