rejection-50.txt: coin-ex2.vnts
	metaprob -f prelude.vnts -f inference.vnts -f coin-ex2.vnts -e 'dump_rejection_samples(50)' > $@

particles-20-20.txt: coin-ex2.vnts
	metaprob -f prelude.vnts -f inference.vnts -f coin-ex2.vnts -e 'dump_particle_samples(20, 20)' > $@

mcmc-50-20.txt: coin-ex2.vnts
	metaprob -f prelude.vnts -f inference.vnts -f coin-ex2.vnts -e 'dump_mcmc_samples(50, 20)' > $@

particles-20-20.png: particles-20-20.txt rejection-50.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_particles("$<", "rejection-50.txt"); plt.savefig("$@")'

mcmc-50-20.png: mcmc-50-20.txt rejection-50.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_mcmc("$<", "rejection-50.txt"); plt.savefig("$@")'
