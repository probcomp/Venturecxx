%.ps: %.hp
	hp2ps $^

%.pdf: %.ps
	ps2pdf $^

%.iface: dist/build/benchmark/benchmark-tmp/%.p_hi
	ghc --show-iface $^ > $@

normal-normal-chain: normal-normal-chain.cxx
	g++ -O2 $^ -lgsl -lgslcblas -o $@
