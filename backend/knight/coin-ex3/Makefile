# Shell wizardry to split the Make magic variable $*, within a given
# rule, on hyphens, and assign the pieces to the names given as
# arguments to SPLIT.
SPLIT = split () { \
    args='$*'; \
    while [ $$\# -gt 0 ]; do \
      arg=$${args%%-*}; \
      args=$${args\#*-}; \
      eval $$1=\$$arg; \
      shift; \
    done; \
  }; \
  split

# Shell wizardry to echo a command and run it, from inside a single
# Make line suppressed with the @ prefix.
RUN = run () { echo $$@; $$@; }; run

# Like RUN, but accepts a file name to direct output to.
RUN_AT = runat () { t=$$1; shift; echo $$@ '>' $$t; $$@ > $$t; }; runat

rejection-%.sav1: example.vnts
	@$(SPLIT) reps seed && \
	$(RUN_AT) $@ metaprob -s $$seed -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e "dump_rejection_samples($$reps)"

%.sav1: example.vnts
	@$(SPLIT) method reps steps seed && \
	echo "Building" $@ && \
	metaprob -s $$seed -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e "dump_$${method}_samples($$reps, $$steps)" > $@

REJ_FILES = $(foreach s,$(shell seq $$(($*/50))),rejection-50-$s.sav1)
rejection-%.sav2:
	rm -f $@.tmp
	$(MAKE) $(REJ_FILES)
	cat $(REJ_FILES) > $@.tmp
	mv -f $@.tmp $@

particle-%.sav2:
	@$(SPLIT) reps steps && \
	rm -f $@.tmp && \
	files=$$(for seed in `seq $$(($$reps/10))`; do echo particle-10-$$steps-$$seed.sav1; done) && \
	echo $$files && \
	$(MAKE) $$files && \
	cat $$files > $@.tmp && \
	mv -f $@.tmp $@

mcmc-%.sav2:
	@$(SPLIT) reps steps && \
	rm -f $@.tmp && \
	files=$$(for seed in `seq $$(($$reps/10))`; do echo mcmc-10-$$steps-$$seed.sav1; done) && \
	echo $$files && \
	$(MAKE) $$files && \
	cat $$files > $@.tmp && \
	mv -f $@.tmp $@

define PLOT_template
# Plotting data merged by merge
# Arguments:
# - Base name of plot/data file
# - Number of comparison rejection samples
# - Plot style
$1-$2.png: $1.sav2 rejection-$2.sav2 ../plotting.py
	python -c 'import matplotlib; matplotlib.use("Agg"); \
	  import matplotlib.pyplot as plt; \
	  import venture.knight.plotting as p; \
	  p.plot_$3("$$<", "rejection-$2.sav2"); \
	  plt.savefig("$$@")'
endef

# Small particles run (couple minutes on a probcomp machine)
$(eval $(call PLOT_template,particle-200-20,1000,particles))

# Larger particles runs
$(eval $(call PLOT_template,particle-1500-30,10000,particles))
$(eval $(call PLOT_template,particle-2000-50,20000,particles))
$(eval $(call PLOT_template,particle-5000-50,5000,particles))
$(eval $(call PLOT_template,particle-5000-50,20000,particles))

# Small mcmc run (couple minutes on a probcomp machine)
$(eval $(call PLOT_template,mcmc-200-20,1000,mcmc))

# Larger mcmc run
$(eval $(call PLOT_template,mcmc-1500-30,10000,mcmc))

# Still larger mcmc runs
$(eval $(call PLOT_template,mcmc-2000-50,20000,mcmc))
$(eval $(call PLOT_template,mcmc-5000-50,5000,mcmc))
$(eval $(call PLOT_template,mcmc-5000-50,20000,mcmc))

ks-evolution-sm.png: mcmc-10-20.sav2 particle-10-20.sav2 rejection-50.sav2 ../plotting.py
	python -c 'import matplotlib; matplotlib.use("Agg"); \
	  import matplotlib.pyplot as plt; \
	  import venture.knight.plotting as p; \
	  p.plot_ks_comparison("$<", "particle-10-20.sav2", "rejection-50.sav2"); \
	  plt.savefig("$@")'

ks-evolution-mid.png: mcmc-2000-50.sav2 particle-2000-50.sav2 rejection-20000.sav2 ../plotting.py
	python -c 'import matplotlib; matplotlib.use("Agg"); \
	  import matplotlib.pyplot as plt; \
	  import venture.knight.plotting as p; \
	  p.plot_ks_comparison("$<", "particle-2000-50.sav2", "rejection-20000.sav2"); \
	  plt.savefig("$@")'

ks-evolution-lg.png: mcmc-5000-50.sav2 particle-5000-50.sav2 rejection-5000.sav2 ../plotting.py
	python -c 'import matplotlib; matplotlib.use("Agg"); \
	  import matplotlib.pyplot as plt; \
	  import venture.knight.plotting as p; \
	  p.plot_ks_comparison("$<", "particle-5000-50.sav2", "rejection-5000.sav2"); \
	  plt.savefig("$@")'
