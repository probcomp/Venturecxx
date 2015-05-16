# This directory contains code to profile and compare BLOG and Venture code. Use
# this makefile to run these profiling tests and comparisons. Because some of
# the profiling runs contained here are a bit lengthy, the results of running
# this makefile are checked into Git. Re-running this file will override those
# results.

# The python script parallelizes across 10 processes to speed things up.
# If you want to use fewer cores, change the argument to Pool in profile_model.py
blog-profile-time: profile_model.py
	mkdir blog-profile-time
	python profile_model.py time_blog

venture-profile-time: poisson_ball.py poisson_ball.vnt profile_model.vnt
	mkdir venture-profile-time
	python profile_model.py time_venture

blog-profile-quality: profile_model.py
	mkdir profile-quality
	python profile_model.py quality_blog

venture-profile-quality: poisson_ball.py poisson_ball.vnt profile_model.vnt
	python profile_model.py quality_venture

compare-inference-quality: profile_model.py
	python profile_model.py compare
