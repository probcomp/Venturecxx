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
config["num_data"] = 20
config["should_reset"] = True
config["get_ripl"] = "mite"


config["global_reporting_threshold"] = 0.00001
config["infer"] = """
(repeat 5
(mh_correct
 (on_subproblem default all
   (lambda (subproblem)
     (do (rho_weight_and_rho_db <- (detach subproblem))
         (xi_weight <- (regen subproblem))
         (let ((rho_weight (first rho_weight_and_rho_db))
               (rho_db (rest rho_weight_and_rho_db)))
         (return
          (list (- xi_weight rho_weight)
                pass                    ; accept
                (do (detach subproblem) ; reject
                    (restore subproblem rho_db))))))))))
"""
config["ignore_inference_quality"] = False
