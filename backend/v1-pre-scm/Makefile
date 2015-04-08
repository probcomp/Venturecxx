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
test: test/c-stats.so
	$(MITSCHEME) --compiler --heap $(HEAP) --stack 2000 --batch-mode \
	  --no-init-file \
	  --eval '(set! load/suppress-loading-message? #t)' \
	  --eval '(begin (load "load") (load "test/load") (run-tests-and-exit))'

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
	-rm -f test/*.bci
	-rm -f test/*.bin
	-rm -f test/*.com
	-rm -f test/*.ext
	-rm -f test/c-stats.o
	-rm -f test/c-stats.so
