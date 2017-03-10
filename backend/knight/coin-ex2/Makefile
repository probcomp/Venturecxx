analytic-100.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< -e 'dump_analytic_samples(100)' > $@

particles-10-5.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< -e 'dump_particle_samples(10, 5)' > $@

rejection-p-p-50.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< -e 'rejection_p_p_plot(50, "$@")'

particles-p-p-10-2.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< -e 'particles_p_p_plot(10, 2, "$@")'

particles-p-p-50-20.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< -e 'particles_p_p_plot(50, 20, "$@")'

ssrmh-p-p-50-20.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< -e 'ssrmh_p_p_plot(50, 20, "$@")'

custom-rmh-p-p-50-20.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< -e 'custom_rmh_p_p_plot(50, 20, "$@")'

ss-vs-custom-rmh-p-p-50-3.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< -e 'ss_vs_custom_rmh_p_p_plot(50, 3, "$@")'

particles-10-5.png: particles-10-5.txt ../plotting.py
	python -c 'import matplotlib.pyplot as plt; import scipy.stats as stats; \
	  import venture.knight.plotting as p; \
	  p.plot_particles("$<", analytic=stats.beta(6,3)); plt.savefig("$@")'
