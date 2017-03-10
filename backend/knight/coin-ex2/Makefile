analytic-100.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e 'dump_analytic_samples(100)' > $@

particles-10-5.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e 'dump_particle_samples(10, 5)' > $@

particles-100-10.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e 'dump_particle_samples(100, 10)' > $@

particles-200-20.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e 'dump_particle_samples(200, 20)' > $@

ssrmh-200-20.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e 'dump_mcmc_samples(200, 20)' > $@

rejection-p-p-50.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e 'rejection_p_p_plot(50, "$@")'

particles-p-p-10-2.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e 'particles_p_p_plot(10, 2, "$@")'

particles-p-p-50-20.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e 'particles_p_p_plot(50, 20, "$@")'

ssrmh-p-p-50-20.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e 'ssrmh_p_p_plot(50, 20, "$@")'

custom-rmh-p-p-50-20.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e 'custom_rmh_p_p_plot(50, 20, "$@")'

ss-vs-custom-rmh-p-p-50-3.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f ../coin-ex1/harness.vnts -e 'ss_vs_custom_rmh_p_p_plot(50, 3, "$@")'

particles-10-5.png: particles-10-5.txt ../plotting.py
	python -c 'import matplotlib.pyplot as plt; import scipy.stats as stats; \
	  import venture.knight.plotting as p; \
	  p.plot_particles("$<", analytic=stats.beta(7,2)); plt.savefig("$@")'

particles-100-10.png: particles-100-10.txt ../plotting.py
	python -c 'import matplotlib.pyplot as plt; import scipy.stats as stats; \
	  import venture.knight.plotting as p; \
	  p.plot_particles("$<", analytic=stats.beta(7,2)); plt.savefig("$@")'

particles-200-20.png: particles-200-20.txt ../plotting.py
	python -c 'import matplotlib.pyplot as plt; import scipy.stats as stats; \
	  import venture.knight.plotting as p; \
	  p.plot_particles("$<", analytic=stats.beta(7,2)); plt.savefig("$@")'

ssrmh-200-20.png: ssrmh-200-20.txt ../plotting.py
	python -c 'import matplotlib.pyplot as plt; import scipy.stats as stats; \
	  import venture.knight.plotting as p; \
	  p.plot_mcmc("$<", analytic=stats.beta(7,2)); plt.savefig("$@")'
