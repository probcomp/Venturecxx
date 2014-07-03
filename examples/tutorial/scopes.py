
# - Have one "hierarchical Bayes" example, ala the Charles/Amy/Josh bags-of-coins stuff --- that is, a hierarchical model out of dirichlet/discrete componenets, with parameters, hyperparameters, and latents, for a few different groups. At least one group of data should have the die rolls be latent (but observe some counts), so there is "state estimation", as well as parameter estimation and hyperparameter estimation.

# - We can have two fixed sets of scopes --- "parameters", "hypers", "latent states" --- with blocks uniquely picking out random choices. We can contrast it with a new version that has one scope for hypers, another for parameters for group 1, another for parameters for group 2, etc.

# - We can contrast a few different inference methods, and also reinforce standard Bayesian vocabulary.

# - We can also have a Bayesian network, where the nodes are ordered in terms of topological sort, and the parameters are random. If the parameters are generated to be nearly deterministic, then we'll need to use blocked proposals; otherwise single-site proposals should work well.


# (define colors '(black blue green orange red))

# (define bag->prototype
#   (mem (lambda (bag) (dirichlet '(1 1 1 1 1)))))

# (define (draw-marbles bag num-draws)
#   (repeat num-draws
#           (lambda () (multinomial colors (bag->prototype bag)))))

# (hist (draw-marbles 'bag 50) "first sample")
# (hist (draw-marbles 'bag 50) "second sample")
# (hist (draw-marbles 'bag 50) "third sample")
# (hist (draw-marbles 'bag 50) "fourth sample")

from venture.venturemagics.ip_parallel import *

# notes:
# here the random choice of hyper_mean won't be in hyper_mean
# scope. (need to put scope include inside the lambda).

# dynamic scope works exactly as in scheme. in model2
# hyper_mean evals to a constant. there's no procedure
# application involving a random choice. so hyper_mean
# doesn't appear in *mean_scope*

# mem: every scope that calls a memoized proc will
# have the memoized random choice in it. e.g. if we 
# had multiple *mean* variables below, each using 
# the same memoized *hyper_mean* value, then *hyper_mean*
# would appear in each scope. if the different *mean*
# variables were in different blocks, then we'd get
# an exception.

model1='''
[assume hyper_mean (scope_include (quote hyper_mean_scope) 
                         (lambda () (uniform_continuous -100 100) ))  ]
[assume mean (scope_include (quote mean_scope) 0 (normal (hyper_mean) 5) ) ]
[observe (normal mean 0.5) 10]
[observe (normal mean 0.5) 11]
'''

model2='''
[assume hyper_mean  (uniform_continuous -100 100)  ]
[assume mean (scope_include (quote mean_scope) 0 (normal hyper_mean 5) ) ]
[observe (normal mean 0.5) 10]
[observe (normal mean 0.5) 11]'''
v = mk_p_ripl()
# v.execute_program(model2)
# for i in range(10):
#     print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
#     v.infer('(mh mean_scope one 10)')
    

# print 'one --- \n\n all'
# v = mk_p_ripl()
# v.execute_program(model)

# for i in range(10):
#     v.infer('(mh means all 10)')
#     print 'i: %i'%i, np.round( map(v.sample, ('hyper_mean', 'mean1') ), 2)


## PROBLEM WITH ARRAY BLOCK NAMES
# v.assume('x','(scope_include (quote sc) (array 0 0) (normal 0 1) )')
# print v.sample('x')
# #v.infer('(mh my_scope (array 0 0) 50)')
# block = {'type': 'array',
#          'value': [{'type': 'number', 'value': 0.0}, {'type': 'number', 'value': 0.0}]}

# v.infer( dict(kernel='mh',scope='sc', block=block, transitions=50) )
# v.infer( dict(kernel='mh',scope='sc', block=[0,0], transitions=50) )



# illustrate: mean appears in two scopes
model2='''
[assume hyper_mean  (uniform_continuous -100 100)  ]
[assume mean (scope_include (quote mean_scope) 0 (normal hyper_mean 5) ) ]
[observe (normal mean 0.5) 10]
[observe (normal mean 0.5) 11]'''
v = mk_p_ripl()
v.execute_program(model2)
for i in range(10):
    print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
    v.infer('(mh mean_scope one 10)')

print '\n\n'
for i in range(10):
    print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
    v.infer('(mh default one 10)')

print '\n\n'
for i in range(10):
    print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
    v.infer('(mh default all 10)')


# illustrate different blocks but same scope
model3='''
[assume hyper_mean (scope_include (quote hyper_scope) 0 (uniform_continuous -100 100) )  ]
[assume mean0 (scope_include (quote mean_scope) 0 (normal hyper_mean 5) ) ]
[assume mean1 (scope_include (quote mean_scope) 1 (normal hyper_mean 5) ) ]
[observe (normal mean0 10) 10]
[observe (normal mean1 10) 11]'''
v = mk_p_ripl()
v.execute_program(model3)
print '\n\n'
for i in range(10):
    print np.round( map( v.sample, ('hyper_mean','mean0','mean1') ) )
    v.infer('(cycle ( (mh mean_scope one 10) (mh hyper_scope one 10)) 1 )')

print '\n\n'
for i in range(10):
    print np.round( map( v.sample, ('hyper_mean','mean0','mean1') ) )
    v.infer('(mh mean_scope 0 10)')


# illustrate dynamic scope
## COREDUMPS IF FLIP PROB TOO SMALL
model4='''
[assume hyper_mean (scope_include (quote hyper_scope) 0 (uniform_continuous -100 100) )  ]
[assume my_flip (lambda () (if (flip .5) true (my_flip) ) ) ]
[assume mean (scope_include (quote mean_scope) 0
               (if (my_flip)
                 (normal hyper_mean 1)
                 (normal hyper_mean 10) ) ) ]

[observe (normal mean 10) 10]
[observe (normal mean 10) 11]'''
v = mk_p_ripl()
v.execute_program(model4)

print '\n\n----\n SCOPE EXCLUDE \n'
for i in range(20):
    print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
    v.infer('(mh mean_scope one 1)')

    
model5='''
[assume hyper_mean (scope_include (quote hyper_scope) 0 (uniform_continuous -100 100) )  ]
[assume my_flip (lambda () (if (flip .5) true (my_flip) ) ) ]
[assume mean (scope_include (quote mean_scope) 0
               (if (scope_exclude (quote mean_scope) (my_flip) )
                 (normal hyper_mean 1)
                 (normal hyper_mean 10) ) ) ]

[observe (normal mean 10) 10]
[observe (normal mean 10) 11]'''
v = mk_p_ripl()
v.execute_program(model5)

print '\n\n with exclude \n'
for i in range(20):
    print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
    v.infer('(mh mean_scope one 1)')




