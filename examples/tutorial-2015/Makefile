all: build

tutorial.lvnt: tutorial.lvnt.erb
	erb tutorial.lvnt.erb > tutorial.lvnt

tutorial-smoke.lvnt: tutorial.lvnt.erb
	SMOKETEST=1 erb tutorial.lvnt.erb > tutorial-smoke.lvnt

build: tutorial.lvnt
	../../script/venture-transcript tutorial.lvnt ppaml
	cp ppaml/index.html ppaml/tutorial.html

build-smoke: tutorial-smoke.lvnt
	../../script/venture-transcript tutorial-smoke.lvnt ppaml-smoke

upload: build
	scp -r ppaml/ login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/

upload-smoke: build-smoke
	scp -r ppaml-smoke/ login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/
