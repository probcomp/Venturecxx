all: build

# Assets

gauss_plot.png:  # This takes about 3 minutes on my laptop
	venture puma -e '(run (resample 100)) (plot_to_file (quote gauss_plot) (quote h0) (run (accumulate_dataset 10000 (collect (labelled (normal 1 0.7071067811865475) x)))))'

reg-test.csv: mk_dataset.vnt
	venture puma -f $<

vis-frame.png: mk_frame.vnts curve-fitting.py reg-test.csv
	venture lite -L curve-fitting.py -f $<

vis-outlier.png: mk_outlier_frame.vnts curve-fitting.py
	venture lite -L curve-fitting.py -f $<

BASIC_ASSETS = gauss_plot.png
REGRESSION_ASSETS = lin-reg-1.vnts lin-reg-2.vnts lin-reg-3.vnts reg-test.csv vis-frame.png vis-outlier.png curve-fitting.py
GP_ASSETS = gpexample_plugin.py gpmem.py BayesOpt_gpmem_sequence.png gp_mixreg_hardcoded.png gp_progressivemixreg_data.png gp_toy_posterior.png

# Tutorial content files

%.lvnt: %.lvnt.erb
	erb $< > $@

%-smoke.lvnt: %.lvnt.erb
	SMOKETEST=1 erb $< > $@

tutorial/%/index.html: %.lvnt reg-test.csv
	../../script/venture-transcript $< tutorial/$*

tutorial-smoke/%/index.html: %-smoke.lvnt reg-test.csv
	../../script/venture-transcript $< tutorial-smoke/$*

# Full builds

build: index.html tutorial/basics/index.html tutorial/linear-regression/index.html tutorial/gp/index.html $(BASIC_ASSETS) $(REGRESSION_ASSETS) $(GP_ASSETS)
	cp index.html tutorial/
	cp $(BASIC_ASSETS) tutorial/basics/
	cp $(REGRESSION_ASSETS) tutorial/linear-regression
	cp $(GP_ASSETS) tutorial/gp

build-smoke: index.html tutorial-smoke/basics/index.html tutorial-smoke/linear-regression/index.html tutorial-smoke/gp/index.html $(BASIC_ASSETS) $(REGRESSION_ASSETS)
	cp index.html tutorial-smoke/
	cp $(BASIC_ASSETS) tutorial-smoke/basics/
	cp $(REGRESSION_ASSETS) tutorial-smoke/linear-regression
	cp $(GP_ASSETS) tutorial-smoke/gp

upload: build
	scp -r tutorial/ login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/

upload-smoke: build-smoke
	scp -r tutorial-smoke/ login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/
