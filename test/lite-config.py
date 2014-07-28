global config # because the tests break without this global, pylint: disable=global-at-module-level
config = {}

config["num_samples"] = 50
config["num_transitions_per_sample"] = 50
config["should_reset"] = True
config["get_ripl"] = "lite"
config["get_mripl_backend"] = "lite"
config["get_mripl_local_mode"] = True


config["global_reporting_threshold"] = 0.001
#config["infer"] = "(pgibbs default ordered 2 5)"
config["infer"] = "(mh default one 100)"
config["ignore_inference_quality"] = False
