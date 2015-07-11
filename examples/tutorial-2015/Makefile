all: build

gauss_plot.png:  # This takes about 3 minutes on my laptop
	venture puma -e '(run (resample 100)) (plot_to_file (quote gauss_plot) (quote h0) (run (accumulate_dataset 10000 (collect (labelled (normal 1 0.7071067811865475) x)))))'

%.lvnt: %.lvnt.erb
	erb $^ > $@

%-smoke.lvnt: %.lvnt.erb
	SMOKETEST=1 erb $^ > $@

build: tutorial.lvnt linear-regression.lvnt gauss_plot.png
	../../script/venture-transcript tutorial.lvnt ppaml
	../../script/venture-transcript linear-regression.lvnt linear-regression
	cp ppaml/index.html ppaml/tutorial.html
	cp gauss_plot.png ppaml/

build-smoke: tutorial-smoke.lvnt linear-regression-smoke.lvnt gauss_plot.png
	../../script/venture-transcript tutorial-smoke.lvnt ppaml-smoke
	../../script/venture-transcript linear-regression-smoke.lvnt linear-regression-smoke
	cp gauss_plot.png ppaml-smoke/

upload: build
	scp -r ppaml/ login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/

upload-smoke: build-smoke
	scp -r ppaml-smoke/ login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/
