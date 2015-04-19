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

def build_brownian_model(step_form, noise_form):
  return """
[assume brown_step
  (tag (quote param) 0 {})]

[assume obs_noise
  (tag (quote param) 1 {})]

[assume position (mem (lambda (t)
  (tag (quote exp) t
   (if (<= t 0)
       (normal 0 brown_step)
       (normal (position (- t 1)) brown_step)))))]

[assume obs_fun (lambda (t)
  (normal (position t) obs_noise))]

[predict (position 10)]""".format(step_form, noise_form)
