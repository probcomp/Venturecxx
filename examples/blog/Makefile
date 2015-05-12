# This directory contains code to profile and compare BLOG and Venture code. Use
# this makefile to run these profiling tests and comparisons. Because some of
# the profiling runs contained here are a bit lengthy, the results of running
# this makefile are checked into Git. Re-running this file will override those
# results.

# For speed, profile_blog.py will start multiple processes on the host machine
# For sequential behavior, call profile_blog.py False
blog-results: profile_blog.py
	mkdir blog-results
	python profile_blog.py


