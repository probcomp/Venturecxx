# This directory contains code to examine the behavior of a few different set
# implementations, both for sets of pre-determined size and where the size is
# not chosen.  This file contains the code to run all the examples contained
# here.  Many of these make commands dispatch to a shell script, because
# makefiles don't seem to do loops and conditionals

profile-scaffold: compare_scaffolds.vnt plugins.py run-tests.sh analyze_results.py
	mkdir results
	./run-tests.sh "run_filter"
	./run-tests.sh "run_prefix_k"
	./run-tests.sh "run_map"
	python analyze_results.py
