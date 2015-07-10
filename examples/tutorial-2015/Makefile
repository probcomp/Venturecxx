all: build

gauss_plot.png:
	venture puma -e '(plot_to_file (quote gauss_plot) (quote h0) (run (accumulate_dataset 100000 (collect (labelled (normal 1 0.7071067811865475) x)))))'

tutorial.lvnt: tutorial.lvnt.erb
	erb tutorial.lvnt.erb > tutorial.lvnt

tutorial-smoke.lvnt: tutorial.lvnt.erb
	SMOKETEST=1 erb tutorial.lvnt.erb > tutorial-smoke.lvnt

build: tutorial.lvnt gauss_plot.png
	../../script/venture-transcript tutorial.lvnt ppaml
	cp ppaml/index.html ppaml/tutorial.html
	cp gauss_plot.png ppaml/

build-smoke: tutorial-smoke.lvnt gauss_plot.png
	../../script/venture-transcript tutorial-smoke.lvnt ppaml-smoke
	cp gauss_plot.png ppaml-smoke/

upload: build
	scp -r ppaml/ login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/

upload-smoke: build-smoke
	scp -r ppaml-smoke/ login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/
