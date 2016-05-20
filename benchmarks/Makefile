# This particular process for profiling Puma (which registers as a C++
# extension to Python) depends upon apt-get install google-perftools
# and yep.py (included).  The latter was downloaded from
# https://github.com/fabianp/yep and slightly modified.

puma-normal-normal-mh.prof: Makefile
	time ../pythenv.sh python -m yep -o $@ -- ../script/venture puma -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer mh(default, one, 300000);"
	@echo "View with, e.g."
	@echo "google-pprof --cum --evince /usr/bin/python $@"
