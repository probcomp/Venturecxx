import math
import venture.shortcuts as vs
ripl = vs.make_church_prime_ripl()
x = ripl.assume("x", "(square 2.0)", label="square")

y = ripl.assume("y", "(cube 2.0)", label="cube")
ripl.clear()
z = ripl.assume("z", "(py_uniform_continuous 0.0 4.0)")
assert ripl.get_global_logscore() == (-1 * math.log(4.0))

ripl.clear()

p = 0.8
z = ripl.assume("z", "(py_flip " + str(p) + ")")
if not z:
    p = 1.0 - p
assert ripl.get_global_logscore() == math.log(p) 
