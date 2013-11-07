import venture.shortcuts as vs
ripl = vs.make_church_prime_ripl()
ripl.assume("x", "(square 2.0)")
# ripl.assume("y", "(cube 2.0)")
ripl.assume("is_trick", "(bernoulli 0.1)")
