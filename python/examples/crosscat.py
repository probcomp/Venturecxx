from venture import shortcuts


def makeAssumes(my_ripl, parameters):
    my_ripl.assume("get_component_hyperparameter", "(mem (lambda (col) (gamma 1.0 1.0) ))")
    my_ripl.assume("get_component_model", "(mem (lambda (col category) (make_sym_dir_mult (get_component_hyperparameter col) %d) ))" % parameters['n_values'])
    my_ripl.assume("view_crp_hyperparameter", "(gamma 1.0 1.0)")
    my_ripl.assume("view_crp", "(make_crp view_crp_hyperparameter)")
    my_ripl.assume("get_view", "(mem (lambda (col) (view_crp) ))")
    my_ripl.assume("get_categorization_crp_hyperparameter", "(mem (lambda (view) (gamma 1.0 1.0) ))")
    my_ripl.assume("get_categorization_crp", "(mem (lambda (view) (make_crp (get_categorization_crp_hyperparameter view)) ))")
    my_ripl.assume("get_category", "(mem (lambda (view row) ( (get_categorization_crp view) ) ))")
    my_ripl.assume("get_cell", "(mem (lambda (row col) ( (get_component_model col (get_category (get_view col) row)) ) ))")
    return


def makeObserves(my_ripl, parameters):
    for r in xrange(parameters['n_rows']):
        for c in xrange(parameters['n_columns']):
            cell_value = r >= (parameters['n_rows'] / 2)
            my_ripl.observe("(get_cell %d %d)" % (r, c), "atom<%d>" % cell_value)
    return


def main():
    my_ripl = shortcuts.make_church_prime_ripl() 
    parameters = {'n_values': 2, 'n_rows': 6, 'n_columns': 6}
    makeAssumes(my_ripl, parameters)
    makeObserves(my_ripl, parameters)
    my_ripl.infer({'transitions': 10})
    return my_ripl, parameters


if __name__ == '__main__':
    my_ripl, parameters = main()
    # my_ripl.predict("(= (get_category (get_view 0) 0) (get_category (get_view 0) 3))")
