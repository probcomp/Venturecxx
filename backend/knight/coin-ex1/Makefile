rejection-p-p-50.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f harness.vnts -e 'rejection_p_p_plot(50, "$@")'

particles-p-p-10-2.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f harness.vnts -e 'particles_p_p_plot(10, 2, "$@")'

particles-p-p-10-10.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f harness.vnts -e 'particles_p_p_plot(10, 10, "$@")'

particles-p-p-50-20.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f harness.vnts -e 'particles_p_p_plot(50, 20, "$@")'

ssrmh-p-p-10-10.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f harness.vnts -e 'ssrmh_p_p_plot(10, 10, "$@")'

ssrmh-p-p-50-20.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f harness.vnts -e 'ssrmh_p_p_plot(50, 20, "$@")'

custom-rmh-p-p-50-20.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f harness.vnts -e 'custom_rmh_p_p_plot(50, 20, "$@")'

ss-vs-custom-rmh-p-p-50-3.png: example.vnts
	metaprob -f ../prelude.vnts -f ../inference.vnts -f $< \
	  -f harness.vnts -e 'ss_vs_custom_rmh_p_p_plot(50, 3, "$@")'
