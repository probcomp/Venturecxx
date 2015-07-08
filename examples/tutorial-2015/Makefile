all: build

tutorial.lvnt: tutorial.lvnt.erb
	erb tutorial.lvnt.erb > tutorial.lvnt

build: tutorial.lvnt
	../../script/venture-transcript tutorial.lvnt ppaml

upload: build
	scp -r ppaml/ login.csail.mit.edu:/afs/csail.mit.edu/proj/probcomp/www/data/venture/
