global config # because the tests break without this global, pylint: disable=global-at-module-level
config = {}

config["num_samples"] = 200
config["num_transitions_per_sample"] = 200
config["should_reset"] = False
config["get_ripl"] = "cxx"
config["global_reporting_threshold"] = 0.001
config["kernel"] = "mh"
config["scope"] = "default"
config["block"] = "one"
config["with_mutation"] = True
config["particles"] = 2
config["ignore_inference_quality"] = False
