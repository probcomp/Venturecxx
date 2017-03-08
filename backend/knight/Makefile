rejection-50.txt: coin-ex2.vnts
	metaprob -f prelude.vnts -f inference.vnts -f coin-ex2.vnts -e 'dump_rejection_samples(50)' > $@

rejection-500.txt: coin-ex2.vnts
	metaprob -f prelude.vnts -f inference.vnts -f coin-ex2.vnts -e 'dump_rejection_samples(500)' > $@

particles-20-20.txt: coin-ex2.vnts
	metaprob -f prelude.vnts -f inference.vnts -f coin-ex2.vnts -e 'dump_particle_samples(20, 20)' > $@

particles-500-20.txt: coin-ex2.vnts
	metaprob -f prelude.vnts -f inference.vnts -f coin-ex2.vnts -e 'dump_particle_samples(500, 20)' > $@

mcmc-50-20.txt: coin-ex2.vnts
	metaprob -f prelude.vnts -f inference.vnts -f coin-ex2.vnts -e 'dump_mcmc_samples(50, 20)' > $@

mcmc-500-20.txt: coin-ex2.vnts
	metaprob -f prelude.vnts -f inference.vnts -f coin-ex2.vnts -e 'dump_mcmc_samples(500, 20)' > $@

particles-20-20-50.png: particles-20-20.txt rejection-50.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_particles("$<", "rejection-50.txt"); plt.savefig("$@")'

particles-500-20-500.png: particles-500-20.txt rejection-500.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_particles("$<", "rejection-500.txt"); plt.savefig("$@")'

mcmc-50-20-50.png: mcmc-50-20.txt rejection-50.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_mcmc("$<", "rejection-50.txt"); plt.savefig("$@")'

mcmc-500-20-500.png: mcmc-500-20.txt rejection-500.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_mcmc("$<", "rejection-500.txt"); plt.savefig("$@")'
