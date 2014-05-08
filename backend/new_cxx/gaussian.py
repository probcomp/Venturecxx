from venture import shortcuts

'''
ripl = shortcuts.make_puma_church_prime_ripl()
# ripl = shortcuts.Lite().make_church_prime_ripl()
ripl.assume("x", "(scope_include 1 1 (normal 0 10))")
ripl.assume("y", "(scope_include 1 2 (normal 10 10))")
ripl.assume("z", "(scope_include 2 1 (flip 0.5))")
ripl.assume("u", "(scope_include 1 3 (if z (normal x 1) (normal y 1)))")
ripl.observe("u", 10)
z_list = []
for iter in range(100):
	ripl.infer('(mh 2 all 1)')
	ripl.infer('(map 1 all 0.2 3 10)')
	z_list.append(ripl.sample('z'))
print 'p_z = ', sum(z_list)/float(len(z_list))

'''

ripl = shortcuts.make_puma_church_prime_ripl()
#ripl = shortcuts.Lite().make_church_prime_ripl()
ripl.assume("x", "(normal 0 10)")
ripl.assume("y", "(normal x 1)")
ripl.observe("y", 10)
ripl.infer('(hmc default all 0.2 3 1000)')
print ripl.sample("x")
