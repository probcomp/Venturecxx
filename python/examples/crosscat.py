from venture import shortcuts


def makeAssumes(my_ripl, parameters):
    my_ripl.assume("get_component_hyperparameter", "(mem (lambda (col) (gamma 1.0 1.0) ))")
    my_ripl.assume("get_component_model", "(mem (lambda (col category) (make_sym_dir_mult (get_component_hyperparameter col) 2) ))")
    my_ripl.assume("view_crp_hyperparameter", "(gamma 1.0 1.0)")
    my_ripl.assume("view_crp", "(make_crp view_crp_hyperparameter)")
    my_ripl.assume("get_view", "(mem (lambda (col) (view_crp) ))")
    my_ripl.assume("get_categorization_crp_hyperparameter", "(mem (lambda (view) (gamma 1.0 1.0) ))")
    my_ripl.assume("get_categorization_crp", "(mem (lambda (view) (make_crp (get_categorization_crp_hyperparameter view)) ))")
    my_ripl.assume("get_category", "(mem (lambda (view row) ( (get_categorization_crp view) ) ))")
    my_ripl.assume("get_cell", "(mem (lambda (row col) ( (get_component_model col (get_category (get_view col) row)) ) ))")
    return


def makeObserves(my_ripl, parameters):
    my_ripl.observe("(get_cell 0 0)", "atom<1>")
    my_ripl.observe("(get_cell 0 1)", "atom<1>")
    my_ripl.observe("(get_cell 0 2)", "atom<1>")
    my_ripl.observe("(get_cell 0 3)", "atom<1>")
    my_ripl.observe("(get_cell 0 4)", "atom<1>")
    my_ripl.observe("(get_cell 0 5)", "atom<1>")
    my_ripl.observe("(get_cell 1 0)", "atom<1>")
    my_ripl.observe("(get_cell 1 1)", "atom<1>")
    my_ripl.observe("(get_cell 1 2)", "atom<1>")
    my_ripl.observe("(get_cell 1 3)", "atom<1>")
    my_ripl.observe("(get_cell 1 4)", "atom<1>")
    my_ripl.observe("(get_cell 1 5)", "atom<1>")
    my_ripl.observe("(get_cell 2 0)", "atom<1>")
    my_ripl.observe("(get_cell 2 1)", "atom<1>")
    my_ripl.observe("(get_cell 2 2)", "atom<1>")
    my_ripl.observe("(get_cell 2 3)", "atom<1>")
    my_ripl.observe("(get_cell 2 4)", "atom<1>")
    my_ripl.observe("(get_cell 2 5)", "atom<1>")
    my_ripl.observe("(get_cell 3 0)", "atom<0>")
    my_ripl.observe("(get_cell 3 1)", "atom<0>")
    my_ripl.observe("(get_cell 3 2)", "atom<0>")
    my_ripl.observe("(get_cell 3 3)", "atom<0>")
    my_ripl.observe("(get_cell 3 4)", "atom<0>")
    my_ripl.observe("(get_cell 3 5)", "atom<0>")
    my_ripl.observe("(get_cell 4 0)", "atom<0>")
    my_ripl.observe("(get_cell 4 1)", "atom<0>")
    my_ripl.observe("(get_cell 4 2)", "atom<0>")
    my_ripl.observe("(get_cell 4 3)", "atom<0>")
    my_ripl.observe("(get_cell 4 4)", "atom<0>")
    my_ripl.observe("(get_cell 4 5)", "atom<0>")
    my_ripl.observe("(get_cell 5 0)", "atom<0>")
    my_ripl.observe("(get_cell 5 1)", "atom<0>")
    my_ripl.observe("(get_cell 5 2)", "atom<0>")
    my_ripl.observe("(get_cell 5 3)", "atom<0>")
    my_ripl.observe("(get_cell 5 4)", "atom<0>")
    my_ripl.observe("(get_cell 5 5)", "atom<0>")
    return


def main():
    my_ripl = shortcuts.make_church_prime_ripl() 
    parameters = {}
    makeAssumes(my_ripl, parameters)
    makeObserves(my_ripl, parameters)
    my_ripl.infer({'transitions': 10})
    return my_ripl, parameters


if __name__ == '__main__':
    my_ripl, parameters = main()
    # my_ripl.predict("(= (get_category (get_view 0) 0) (get_category (get_view 0) 3))")
