# This particular process for profiling Puma (which registers as a C++
# extension to Python) depends upon apt-get install google-perftools
# and yep.py (included).  The latter was downloaded from
# https://github.com/fabianp/yep and slightly modified.

all: puma-profs lite-profs

puma-profs: puma-normal-normal-mh.prof
puma-normal-normal-mh.prof: Makefile
	time -o $@.time ../pythenv.sh python -m yep -o $@ -- ../script/venture puma -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer resimulation_mh(default, one, 300000);"
	@cat $@.time
	@echo "View with, e.g."
	@echo "google-pprof --cum --evince /usr/bin/python $@"

puma-profs: puma-normal-normal-slice.prof
puma-normal-normal-slice.prof: Makefile
	time -o $@.time ../pythenv.sh python -m yep -o $@ -- ../script/venture puma -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer slice(default, one, 0.25, 10, 30000);"
	@cat $@.time
	@echo "View with, e.g."
	@echo "google-pprof --cum --evince /usr/bin/python $@"

puma-profs: puma-normal-normal-pgibbs.prof
puma-normal-normal-pgibbs.prof: Makefile
	time -o $@.time ../pythenv.sh python -m yep -o $@ -- ../script/venture puma -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer pgibbs(default, ordered, 500, 500, false);"
	@cat $@.time
	@echo "View with, e.g."
	@echo "google-pprof --cum --evince /usr/bin/python $@"

lite-profs: lite-normal-normal-mh.prof
lite-normal-normal-mh.prof: Makefile
	time -o $@.time ../pythenv.sh python -m cProfile -o $@ -- ../script/venture lite -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer resimulation_mh(default, one, 10000);"
	@cat $@.time
	python -c 'import pstats; s = pstats.Stats("$@"); s.sort_stats("cumtime"); s.print_stats(0.1)'

lite-profs: lite-normal-normal-slice.prof
lite-normal-normal-slice.prof: Makefile
	time -o $@.time ../pythenv.sh python -m cProfile -o $@ -- ../script/venture lite -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer slice(default, one, 0.25, 10, 1000);"
	@cat $@.time
	python -c 'import pstats; s = pstats.Stats("$@"); s.sort_stats("cumtime"); s.print_stats(0.1)'

lite-profs: lite-normal-normal-pgibbs.prof
lite-normal-normal-pgibbs.prof: Makefile
	time -o $@.time ../pythenv.sh python -m cProfile -o $@ -- ../script/venture lite -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer pgibbs(default, ordered, 100, 100);"
	@cat $@.time
	python -c 'import pstats; s = pstats.Stats("$@"); s.sort_stats("cumtime"); s.print_stats(0.1)'

lite-profs: lite-normal-normal-hmc.prof
lite-normal-normal-hmc.prof: Makefile
	time -o $@.time ../pythenv.sh python -m cProfile -o $@ -- ../script/venture lite -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer hmc(default, all, 0.1, 30, 300);"
	@cat $@.time
	python -c 'import pstats; s = pstats.Stats("$@"); s.sort_stats("cumtime"); s.print_stats(0.1)'

lite-profs: lite-normal-normal-rejection.prof
lite-normal-normal-rejection.prof: Makefile
	time -o $@.time ../pythenv.sh python -m cProfile -o $@ -- ../script/venture lite -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer rejection(default, all, 3000);"
	@cat $@.time
	python -c 'import pstats; s = pstats.Stats("$@"); s.sort_stats("cumtime"); s.print_stats(0.1)'

normal-normal-chain: normal-normal-chain.cxx
	g++ -O2 $^ -lgsl -lgslcblas -o $@
