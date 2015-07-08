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

from numpy import array_equal
from venture.test.config import get_ripl, on_inf_prim, gen_on_inf_prim

class TestMatrixVector(object):
  _multiprocess_can_split_ = True
  def setup(self):
    self.ripl = get_ripl()
    self.ripl.assume("v1", "(vector 1 7)")
    self.ripl.assume("v2", "(vector 3 4)")
    self.ripl.assume("m1", "(matrix (array (array 0 1) (array -1 0)))")
    self.ripl.assume("m2", "(matrix (array v1 v2))")

  @on_inf_prim("none")
  def testVectorAdd(self):
    assert array_equal(self.ripl.sample("(vector_add v1 v2)"), [4, 11])
    assert array_equal(self.ripl.sample("(vector_add v2 v2)"), [6, 8])

  @on_inf_prim("none")
  def testMatrixAdd(self):
    assert array_equal(self.ripl.sample("(matrix_add m1 m2)"), [[1, 8], [2, 4]])
    assert array_equal(self.ripl.sample("(matrix_add m2 m2)"), [[2, 14], [6, 8]])

  @on_inf_prim("none")
  def testScaleVector(self):
    assert array_equal(self.ripl.sample("(scale_vector 11 v1)"), [11, 77])
    assert array_equal(self.ripl.sample("(scale_vector -0.5 v2)"), [-1.5, -2.0])

  @on_inf_prim("none")
  def testScaleMatrix(self):
    assert array_equal(self.ripl.sample("(scale_matrix -2 m1)"), [[0, -2], [2, 0]])
    assert array_equal(self.ripl.sample("(scale_matrix 0.1 m2)"), [[0.1, 0.7], [0.3, 0.4]])

  @on_inf_prim("none")
  def testVectorDot(self):
    assert self.ripl.sample("(vector_dot v1 v1)") == 50
    assert self.ripl.sample("(vector_dot v1 v2)") == 31

  @on_inf_prim("none")
  def testMatrixMul(self):
    assert array_equal(self.ripl.sample("(matrix_mul m1 m1)"), [[-1, 0], [0, -1]])
    assert array_equal(self.ripl.sample("(matrix_mul m1 m2)"), [[3, 4], [-1, -7]])
    assert array_equal(self.ripl.sample("(matrix_mul (matrix (array v1 v1 v1)) m1)"), [[-7, 1], [-7, 1], [-7, 1]])

  @on_inf_prim("none")
  def testTranspose(self):
    assert array_equal(self.ripl.sample("(transpose m1)"), [[0, -1], [1, 0]])
    assert array_equal(self.ripl.sample("(transpose m2)"), [[1, 3], [7, 4]])

  @on_inf_prim("none")
  def testMatrixTimesVector(self):
    assert array_equal(self.ripl.sample("(matrix_times_vector m1 v1)"), [7, -1])
    assert array_equal(self.ripl.sample("(matrix_times_vector m1 v2)"), [4, -3])

  @on_inf_prim("none")
  def testVectorTimesMatrix(self):
    assert array_equal(self.ripl.sample("(vector_times_matrix v1 m1)"), [-7, 1])
    assert array_equal(self.ripl.sample("(vector_times_matrix v2 m1)"), [-4, 3])
