# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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
from venture import shortcuts
from venture.unit import VentureUnit


class CrossCat(VentureUnit):
  def makeAssumes(self):
    self.assume("get_component_hyperparameter",
                "(mem (lambda (col) (gamma 1.0 1.0)))")
    self.assume("get_component_model", """
(mem (lambda (col category)
       (make_sym_dir_mult (get_component_hyperparameter col) %d)))
""" % self.parameters['n_values'])
    self.assume("view_crp_hyperparameter", "(gamma 1.0 1.0)")
    self.assume("view_crp", "(make_crp view_crp_hyperparameter)")
    self.assume("get_view", "(mem (lambda (col) (view_crp)))")
    self.assume("get_categorization_crp_hyperparameter",
                "(mem (lambda (view) (gamma 1.0 1.0)))")
    self.assume("get_categorization_crp", """
(mem (lambda (view)
       (make_crp (get_categorization_crp_hyperparameter view))))""")
    self.assume("get_category", """
(mem (lambda (view row)
       ((get_categorization_crp view))))""")
    self.assume("get_cell", """
(mem (lambda (row col)
       ((get_component_model col (get_category (get_view col) row)))))""")
    return

  def makeObserves(self):
    for r in range(self.parameters['n_rows']):
      for c in xrange(self.parameters['n_columns']):
        cell_value = r >= (self.parameters['n_rows'] / 2)
        self.observe("(get_cell %d %d)" % (r, c), "atom<%d>" % cell_value)
    return

if __name__ == '__main__':
  ripl = shortcuts.make_church_prime_ripl()
  parameters = {'n_values': 2, 'n_rows': 64, 'n_columns': 64}
  model = CrossCat(ripl, parameters)
  history = model.runConditionedFromPrior(50, verbose=True)
  history.plot(fmt='png')

