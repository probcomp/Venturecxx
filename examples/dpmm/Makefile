RESULTS := results-samples.png results-logscore.png results-num_clusters.png

$(RESULTS): dpmm_example.vnts extensions.py render_dpmm.py Makefile
	venture -s 1063234350 -f dpmm_example.vnts -L extensions.py -e 'doit(6, 3, 2, 8, 4)'
