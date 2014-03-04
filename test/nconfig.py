global config # because the tests break without this global, pylint: disable=global-at-module-level
config = {}

config["num_samples"] = 100
config["num_transitions_per_sample"] = 100
config["should_reset"] = False
config["get_ripl"] = "cxx"
config["global_reporting_threshold"] = 0.001
#config["infer"] = "(pgibbs default ordered 2 5)"
config["infer"] = "(mh default one 100)"
config["ignore_inference_quality"] = False
