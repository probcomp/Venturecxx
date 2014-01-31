global config # because the tests break without this global, pylint: disable=global-at-module-level
config = {}

config["num_samples"] = 50
config["num_transitions_per_sample"] = 50
config["should_reset"] = False
config["get_ripl"] = "lite"
config["global_reporting_threshold"] = 0.001
config["kernel"] = "mh"
config["scope"] = "default"
config["block"] = "one"
config["with_mutation"] = True
config["particles"] = 2
