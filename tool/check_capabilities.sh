#!/bin/sh

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

set -ex

# This script is for checking basic operation of a user installation
# of Venture.  This is not part of the regular test suite because it
# should be usable even in the absence of Venture's test dependencies.

# The completeness criterion for this script is that it should at
# least minimally exercise each of Venture's (Python) dependencies,
# for early detection of gross install problems.

# Basic simulation
venture lite --abstract-syntax -e '(normal 0 1)'

# Plotting (to file)
plot_file=`mktemp -t "check-capabilities-normal-plot.XXXXXXX"`
venture lite --abstract-syntax -e "
[infer (resample 10)]
[assume x (normal 0 1)]
[assume y (normal x 1)]
[infer
 (let ((d (empty)))
   (do (repeat 100
        (do (mh default all 1)
            (bind (collect x y (abs (- y x))) (curry into d))))
       (plotf_to_file \"$plot_file\" (quote p0s2) d)))]"
rm -rf $plot_file
rm -rf "$plot_file.png"

# Saving and restoring a ripl
save_file=`mktemp -t "check-capabilities-save.XXXXXXX"`
venture lite --abstract-syntax -e "
[assume x (normal 0 1)]
(pyexec \"ripl.save(\\\"$save_file\\\")\")"
venture lite --abstract-syntax -e "
(pyexec \"ripl.load(\\\"$save_file\\\")\")
(sample (normal x 1))"
rm -rf $save_file

# TODO Define and exercise a to-file version of draw_scaffold.

# TODO Exercise the rest server and client, as soon as I can figure
# out how to make sure the server process gets cleaned up properly
