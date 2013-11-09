import venture.shortcuts as vs
ripl = vs.make_church_prime_ripl()
ripl.assume("x", "(square 2.0)", label="square")
ripl.assume("y", "(cube 2.0)", label="cube")
ripl.forget("cube")
ripl.forget("square")
print ripl.list_directives()
print "test"
z = ripl.assume("z", "(uniform_continuous 4.0)")
print z
assert ripl.get_logscore() == (-1 * math.log(4.0))
print "yo"

# z = ripl.assume("z", "(pyflip 0.8)")
# p = 0.8
# if not z:
#     p = 0.2
# assert ripl.get_logscore() == (-1 * math.log(p)) 
