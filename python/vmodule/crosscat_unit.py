from venture import shortcuts
from venture.vmodule.venture_unit import *


class CrossCat(VentureUnit):
    def makeAssumes(self):
        self.assume("get_component_hyperparameter", "(mem (lambda (col) (gamma 1.0 1.0) ))")
        self.assume("get_component_model", "(mem (lambda (col category) (make_sym_dir_mult (get_component_hyperparameter col) %d) ))" % self.parameters['n_values'])
        self.assume("view_crp_hyperparameter", "(gamma 1.0 1.0)")
        self.assume("view_crp", "(make_crp view_crp_hyperparameter)")
        self.assume("get_view", "(mem (lambda (col) (view_crp) ))")
        self.assume("get_categorization_crp_hyperparameter", "(mem (lambda (view) (gamma 1.0 1.0) ))")
        self.assume("get_categorization_crp", "(mem (lambda (view) (make_crp (get_categorization_crp_hyperparameter view)) ))")
        self.assume("get_category", "(mem (lambda (view row) ( (get_categorization_crp view) ) ))")
        self.assume("get_cell", "(mem (lambda (row col) ( (get_component_model col (get_category (get_view col) row)) ) ))")
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
    # 
    #history = model.runConditionedFromPrior(50, verbose=True)
    #history = model.runFromJoint(50, verbose=True)
    #history = model.sampleFromJoint(20, verbose=True)
    #history = model.runFromConditional(50)
    #
    #history.plot(fmt='png')

    # sampledHistory, inferredHistory, klHistory
    history_types = model.computeJointKL(200, 200, runs=4)
    for history_type in history_types:
        history_type.plot(fmt='png')
