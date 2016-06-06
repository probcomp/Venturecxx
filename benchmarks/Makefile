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

puma-normal-normal-slice.prof: Makefile
	time ../pythenv.sh python -m yep -o $@ -- ../script/venture puma -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer slice(default, one, 0.25, 10, 30000);"
	@echo "View with, e.g."
	@echo "google-pprof --cum --evince /usr/bin/python $@"

puma-normal-normal-pgibbs.prof: Makefile
	time ../pythenv.sh python -m yep -o $@ -- ../script/venture puma -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer pgibbs(default, ordered, 500, 500, false);"
	@echo "View with, e.g."
	@echo "google-pprof --cum --evince /usr/bin/python $@"

lite-normal-normal-mh.prof: Makefile
	time ../pythenv.sh python -m cProfile -o $@ -- ../script/venture lite -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer mh(default, one, 10000);"
	python -c 'import pstats; s = pstats.Stats("$@"); s.sort_stats("cumtime"); s.print_stats(0.1)'

lite-normal-normal-slice.prof: Makefile
	time ../pythenv.sh python -m cProfile -o $@ -- ../script/venture lite -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer slice(default, one, 0.25, 10, 1000);"
	python -c 'import pstats; s = pstats.Stats("$@"); s.sort_stats("cumtime"); s.print_stats(0.1)'

lite-normal-normal-pgibbs.prof: Makefile
	time ../pythenv.sh python -m cProfile -o $@ -- ../script/venture lite -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer pgibbs(default, ordered, 100, 100);"
	python -c 'import pstats; s = pstats.Stats("$@"); s.sort_stats("cumtime"); s.print_stats(0.1)'

lite-normal-normal-hmc.prof: Makefile
	time ../pythenv.sh python -m cProfile -o $@ -- ../script/venture lite -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer hmc(default, all, 0.1, 30, 300);"
	python -c 'import pstats; s = pstats.Stats("$@"); s.sort_stats("cumtime"); s.print_stats(0.1)'

lite-normal-normal-rejection.prof: Makefile
	time ../pythenv.sh python -m cProfile -o $@ -- ../script/venture lite -e \
	    "assume x = normal(0, 1); \
	     observe normal(x, 1) = 2; \
	     infer rejection(default, all, 3000);"
	python -c 'import pstats; s = pstats.Stats("$@"); s.sort_stats("cumtime"); s.print_stats(0.1)'
