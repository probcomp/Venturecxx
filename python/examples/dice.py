from venture import shortcuts


def makeAssumes(my_ripl, parameters):
    my_ripl.assume("get_die", "(mem (lambda (die_id) (make_sym_dir_mult 1.0 %d)))" % parameters["n_sides"])
    my_ripl.assume("get_die_roll", "(mem (lambda (die_id roll_id) ((get_die die_id))))")


def makeObserves(my_ripl, parameters):
    for die_id in xrange(parameters['n_die']):
        for roll_id in xrange(parameters['n_rolls']):
            my_ripl.observe("(get_die_roll %d %d)" % (die_id, roll_id), "atom<%d>" % 0)
    return


def main():
    my_ripl = shortcuts.make_church_prime_ripl() 
    parameters = {'n_die': 5, 'n_sides': 10, 'n_rolls': 10}
    makeAssumes(my_ripl, parameters)
    makeObserves(my_ripl, parameters)
    return my_ripl, parameters


if __name__ == '__main__':
    my_ripl, parameters = main()
