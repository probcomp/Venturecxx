all: build

# Assets

gauss_plot.png:  # This takes about 3 minutes on my laptop
	venture puma -e '(run (resample 100)) (plot_to_file (quote gauss_plot) (quote h0) (run (accumulate_dataset 10000 (collect (labelled (normal 1 0.7071067811865475) x)))))'

reg-test.csv: mk_dataset.vnt
	venture puma -f $<

vis-frame.png: mk_frame.vnt curve-fitting.py
	venture lite -L curve-fitting.py -f $<

# Tutorial content files

%.lvnt: %.lvnt.erb
	erb $< > $@

%-smoke.lvnt: %.lvnt.erb
	SMOKETEST=1 erb $< > $@

tutorial/%/index.html: %.lvnt
	../../script/venture-transcript $< tutorial/$*

tutorial-smoke/%/index.html: %-smoke.lvnt
	../../script/venture-transcript $< tutorial-smoke/$*

# Full builds

build: tutorial/basics/index.html tutorial/linear-regression/index.html gauss_plot.png lin-reg-1.vnts reg-test.csv
	cp gauss_plot.png tutorial/basics/
	cp lin-reg-1.vnts tutorial/linear-regression
	cp reg-test.csv tutorial/linear-regression

build-smoke: tutorial-smoke/basics/index.html tutorial-smoke/linear-regression/index.html gauss_plot.png lin-reg-1.vnts reg-test.csv
	cp gauss_plot.png tutorial-smoke/basics/
	cp lin-reg-1.vnts tutorial-smoke/linear-regression
	cp reg-test.csv tutorial-smoke/linear-regression

upload: build
	scp -r tutorial/ login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/

upload-smoke: build-smoke
	scp -r tutorial-smoke/ login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/
