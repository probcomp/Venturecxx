# Copyright (c) 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

global config # because the tests break without this global, pylint: disable=global-at-module-level
config = {}

config["num_samples"] = 50
config["num_transitions_per_sample"] = 50
config["should_reset"] = True
config["get_ripl"] = "puma"
config["get_mripl_backend"] = "puma"
config["get_mripl_local_mode"] = True


config["global_reporting_threshold"] = 0.00001
#config["infer"] = "(pgibbs default ordered 2 5)"
config["infer"] = "(mh default one 100)"
config["ignore_inference_quality"] = False
