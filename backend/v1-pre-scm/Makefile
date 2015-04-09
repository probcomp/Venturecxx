# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

.PHONY: default-target
default-target: test

CFLAGS = -Wall -Wextra -Werror -O2

MITSCHEME = mit-scheme

MITSCHEME_MODULE_SDK = /usr/src/mit-scheme/src/microcode
MITSCHEME_MODULE_CFLAGS = -I$(MITSCHEME_MODULE_SDK) -fPIC -DCOMPILE_AS_MODULE
MITSCHEME_MODULE_LDFLAGS = -shared -fPIC
MITSCHEME_MODULE_LIBS =

GSL_CFLAGS = `gsl-config --cflags`
GSL_LDFLAGS =
GSL_LIBS = `gsl-config --libs`

HEAP = $$(case `uname -m` in x86_64) echo 100000;; *) echo 6000;; esac)

.PHONY: test
test: test-remote
test: test-statistical

.PHONY: check
check: test

.PHONY: test-remote
test-remote:
	@echo '; run remote tests' && \
	echo '(load "test-remote")' \
	| $(MITSCHEME) --batch-mode --no-init-file \
	  --eval '(define (top-eval e) (eval e (->environment (quote ()))))' \
	  --load match \
	  --load condvar \
	  --load thread-barrier \
	  --load remote-balancer \
	  --load remote-client \
	  --load remote-io \
	  --load remote-server \
	  --load remote-worker \
	  # end of MIT Scheme options

.PHONY: test-statistical
test-statistical: test/c-stats.so
	@echo '; run statistical tests' && \
	echo '(run-tests-and-exit)' \
	| $(MITSCHEME) --compiler --heap $(HEAP) --stack 2000 --batch-mode \
	  --no-init-file \
	  --load load \
	  --load test/load \
	  # end of MIT Scheme options

c_stats_CFLAGS = $(CFLAGS) $(MITSCHEME_MODULE_CFLAGS) $(GSL_CFLAGS)
c_stats_LDFLAGS = $(LDFLAGS) $(MITSCHEME_MODULE_LDFLAGS) $(GSL_LDFLAGS)
c_stats_LIBS = $(LIBS) $(MITSCHEME_MODULE_LIBS) $(GSL_LIBS)
c_stats_SRCS = test/c-stats.c
c_stats_OBJS = $(c_stats_SRCS:.c=.o)
test/c-stats.o: test/c-stats.c Makefile
	$(CC) $(c_stats_CFLAGS) -o $@.tmp -c test/c-stats.c && mv -f $@.tmp $@
test/c-stats.so: $(c_stats_OBJS) Makefile
	$(CC) $(c_stats_LDFLAGS) -o $@.tmp $(c_stats_OBJS) $(c_stats_LIBS) \
	&& mv -f $@.tmp $@

clean:
	-rm -f *.bci
	-rm -f *.bin
	-rm -f *.com
	-rm -f *.ext
	-rm -f *.tmp
	-rm -f test/*.bci
	-rm -f test/*.bin
	-rm -f test/*.com
	-rm -f test/*.ext
	-rm -f test/*.tmp
	-rm -f test/c-stats.o
	-rm -f test/c-stats.so
