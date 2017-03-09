rejection-50.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f example.vnts -e 'dump_rejection_samples(50)' > $@

rejection-500.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f example.vnts -e 'dump_rejection_samples(500)' > $@

rejection-2000.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f example.vnts -e 'dump_rejection_samples(2000)' > $@

rejection-10000.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f example.vnts -e 'dump_rejection_samples(10000)' > $@

particles-20-20.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f example.vnts -e 'dump_particle_samples(20, 20)' > $@

particles-500-20.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f example.vnts -e 'dump_particle_samples(500, 20)' > $@

particles-1500-30.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f example.vnts -e 'dump_particle_samples(1500, 30)' > $@

mcmc-50-20.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f example.vnts -e 'dump_mcmc_samples(50, 20)' > $@

mcmc-500-20.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f example.vnts -e 'dump_mcmc_samples(500, 20)' > $@

mcmc-1500-30.txt: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f example.vnts -e 'dump_mcmc_samples(1500, 30)' > $@

particles-20-20-50.png: particles-20-20.txt rejection-50.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_particles("$<", "rejection-50.txt"); plt.savefig("$@")'

particles-20-20-500.png: particles-20-20.txt rejection-500.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_particles("$<", "rejection-500.txt"); plt.savefig("$@")'

particles-500-20-2000.png: particles-500-20.txt rejection-2000.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_particles("$<", "rejection-2000.txt"); plt.savefig("$@")'

particles-1500-30-10000.png: particles-1500-30.txt rejection-10000.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_particles("$<", "rejection-10000.txt"); plt.savefig("$@")'

mcmc-50-20-50.png: mcmc-50-20.txt rejection-50.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_mcmc("$<", "rejection-50.txt"); plt.savefig("$@")'

mcmc-500-20-500.png: mcmc-500-20.txt rejection-500.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_mcmc("$<", "rejection-500.txt"); plt.savefig("$@")'

mcmc-500-20-2000.png: mcmc-500-20.txt rejection-2000.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_mcmc("$<", "rejection-2000.txt"); plt.savefig("$@")'

mcmc-1500-30-10000.png: mcmc-1500-30.txt rejection-10000.txt plotting.py
	python -c 'import venture.knight.plotting as p; import matplotlib.pyplot as plt; p.plot_mcmc("$<", "rejection-10000.txt"); plt.savefig("$@")'
