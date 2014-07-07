
# # - Have one "hierarchical Bayes" example, ala the Charles/Amy/Josh bags-of-coins stuff --- that is, a hierarchical model out of dirichlet/discrete componenets, with parameters, hyperparameters, and latents, for a few different groups. At least one group of data should have the die rolls be latent (but observe some counts), so there is "state estimation", as well as parameter estimation and hyperparameter estimation.

# # - We can have two fixed sets of scopes --- "parameters", "hypers", "latent states" --- with blocks uniquely picking out random choices. We can contrast it with a new version that has one scope for hypers, another for parameters for group 1, another for parameters for group 2, etc.

# # - We can contrast a few different inference methods, and also reinforce standard Bayesian vocabulary.

# # - We can also have a Bayesian network, where the nodes are ordered in terms of topological sort, and the parameters are random. If the parameters are generated to be nearly deterministic, then we'll need to use blocked proposals; otherwise single-site proposals should work well.


# # (define colors '(black blue green orange red))

# # (define bag->prototype
# #   (mem (lambda (bag) (dirichlet '(1 1 1 1 1)))))

# # (define (draw-marbles bag num-draws)
# #   (repeat num-draws
# #           (lambda () (multinomial colors (bag->prototype bag)))))

# # (hist (draw-marbles 'bag 50) "first sample")
# # (hist (draw-marbles 'bag 50) "second sample")
# # (hist (draw-marbles 'bag 50) "third sample")
# # (hist (draw-marbles 'bag 50) "fourth sample")

# from venture.venturemagics.ip_parallel import *

# # notes:
# # here the random choice of hyper_mean won't be in hyper_mean
# # scope. (need to put scope include inside the lambda).

# # dynamic scope works exactly as in scheme. in model2
# # hyper_mean evals to a constant. there's no procedure
# # application involving a random choice. so hyper_mean
# # doesn't appear in *mean_scope*

# # mem: every scope that calls a memoized proc will
# # have the memoized random choice in it. e.g. if we 
# # had multiple *mean* variables below, each using 
# # the same memoized *hyper_mean* value, then *hyper_mean*
# # would appear in each scope. if the different *mean*
# # variables were in different blocks, then we'd get
# # an exception.

# model1='''
# [assume hyper_mean (scope_include (quote hyper_mean_scope) 
#                          (lambda () (uniform_continuous -100 100) ))  ]
# [assume mean (scope_include (quote mean_scope) 0 (normal (hyper_mean) 5) ) ]
# [observe (normal mean 0.5) 10]
# [observe (normal mean 0.5) 11]
# '''

# model2='''
# [assume hyper_mean  (uniform_continuous -100 100)  ]
# [assume mean (scope_include (quote mean_scope) 0 (normal hyper_mean 5) ) ]
# [observe (normal mean 0.5) 10]
# [observe (normal mean 0.5) 11]'''
# v = mk_p_ripl()
# # v.execute_program(model2)
# # for i in range(10):
# #     print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
# #     v.infer('(mh mean_scope one 10)')
    

# # print 'one --- \n\n all'
# # v = mk_p_ripl()
# # v.execute_program(model)

# # for i in range(10):
# #     v.infer('(mh means all 10)')
# #     print 'i: %i'%i, np.round( map(v.sample, ('hyper_mean', 'mean1') ), 2)


# ## PROBLEM WITH ARRAY BLOCK NAMES
# # v.assume('x','(scope_include (quote sc) (array 0 0) (normal 0 1) )')
# # print v.sample('x')
# # #v.infer('(mh my_scope (array 0 0) 50)')
# # block = {'type': 'array',
# #          'value': [{'type': 'number', 'value': 0.0}, {'type': 'number', 'value': 0.0}]}

# # v.infer( dict(kernel='mh',scope='sc', block=block, transitions=50) )
# # v.infer( dict(kernel='mh',scope='sc', block=[0,0], transitions=50) )



# # illustrate: mean appears in two scopes
# model2='''
# [assume hyper_mean  (uniform_continuous -100 100)  ]
# [assume mean (scope_include (quote mean_scope) 0 (normal hyper_mean 5) ) ]
# [observe (normal mean 0.5) 10]
# [observe (normal mean 0.5) 11]'''
# v = mk_p_ripl()
# v.execute_program(model2)
# for i in range(10):
#     print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
#     v.infer('(mh mean_scope one 10)')

# print '\n\n'
# for i in range(10):
#     print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
#     v.infer('(mh default one 10)')

# print '\n\n'
# for i in range(10):
#     print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
#     v.infer('(mh default all 10)')


# # illustrate different blocks but same scope
# model3='''
# [assume hyper_mean (scope_include (quote hyper_scope) 0 (uniform_continuous -100 100) )  ]
# [assume mean0 (scope_include (quote mean_scope) 0 (normal hyper_mean 5) ) ]
# [assume mean1 (scope_include (quote mean_scope) 1 (normal hyper_mean 5) ) ]
# [observe (normal mean0 10) 10]
# [observe (normal mean1 10) 11]'''
# v = mk_l_ripl()
# v.execute_program(model3)
# print '\n\n'
# for i in range(10):
#     print np.round( map( v.sample, ('hyper_mean','mean0','mean1') ) )
#     v.infer('(cycle ( (mh mean_scope one 10) (mh hyper_scope one 10)) 1 )')

# print '\n\n'
# for i in range(10):
#     print np.round( map( v.sample, ('hyper_mean','mean0','mean1') ) )
#     v.infer('(mh mean_scope 1 10)')


# # illustrate dynamic scope
# ## COREDUMPS IF FLIP PROB TOO SMALL
# model4='''
# [assume hyper_mean (scope_include (quote hyper_scope) 0 (uniform_continuous -100 100) )  ]
# [assume my_flip (lambda () (if (flip .5) true (my_flip) ) ) ]
# [assume mean (scope_include (quote mean_scope) 0
#                (if (my_flip)
#                  (normal hyper_mean 1)
#                  (normal hyper_mean 10) ) ) ]

# [observe (normal mean 10) 10]
# [observe (normal mean 10) 11]'''
# v = mk_p_ripl()
# v.execute_program(model4)

# print '\n\n----\n SCOPE EXCLUDE \n'
# for i in range(20):
#     print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
#     v.infer('(mh mean_scope one 1)')

    
# model5='''
# [assume hyper_mean (scope_include (quote hyper_scope) 0 (uniform_continuous -100 100) )  ]
# [assume my_flip (lambda () (if (flip .5) true (my_flip) ) ) ]
# [assume mean (scope_include (quote mean_scope) 0
#                (if (scope_exclude (quote mean_scope) (my_flip) )
#                  (normal hyper_mean 1)
#                  (normal hyper_mean 10) ) ) ]

# [observe (normal mean 10) 10]
# [observe (normal mean 10) 11]'''
# v = mk_p_ripl()
# v.execute_program(model5)

# print '\n\n with exclude \n'
# for i in range(20):
#     print np.round( (v.sample('hyper_mean'), v.sample('mean')), 2)
#     v.infer('(mh mean_scope one 1)')


from venture.venturemagics.ip_parallel import *
dim = 3
bags = 2
alpha = ' '.join(['1']*dim)

a= 'alpha', '(scope_include (quote alpha) 0 (array %s) )'%alpha
b = 'bag_prototype', '''(mem (lambda (bag)
                              (scope_include (quote latents) bag
                               (dirichlet alpha) ) ) )'''


ones = ' '.join(['1']*dim)

# doesn't work coz of simplex - how to make it work?
a= 'hyper_alpha', '''(scope_include (quote hyper_alpha) 0
                        (map (lambda (x) (* 5 x)) (dirichlet (array %s )) ) )'''%ones
a= 'hyper_alpha', '''(scope_include (quote hyper_alpha) 0
                        (dirichlet  (array %s) ))'''%ones
b = 'bag_prototype', '''(mem (lambda (bag)
                              (scope_include (quote latents) bag
                              (dirichlet hyper_alpha) ) ) )'''

m2='''
[assume hyper_alpha (scope_include (quote hyper_alpha) 0
                        (array (+ 1 (poisson 2)) (+ 1 (poisson 2) )) )]
[assume bag_prototype (mem (lambda (bag)
                              (scope_include (quote latents) bag
                               (beta (lookup hyper_alpha 0) (lookup hyper_alpha 1)) ) ) )]'''

obs_beta = lambda bag,color: ('(flip (bag_prototype %i) )'%bag,'%s'%color)
data_beta = [(0,'false')]*5 + [(1,'true')]*5



#########################3
utils_string='''
[assume append
     (lambda (v x)
       (if (is_pair v)
         (_append_list v x)
         (to_array (_append_list(to_list v) x))))]

[assume _append_list
     (lambda (v x)
       (if (is_empty v)
         (list x)
         (pair
           (first v)
           (_append_list (rest v) x))))]

[assume simplex_list (lambda (s)
                       (_simplex_list s (size s)) ) ]
[assume _simplex_list (lambda (s d)
                         (if (= d 0) (list)
                           (_append_list 
                             (_simplex_list s (- d 1) )
                               (lookup s (- d 1)) ) ) ) ]

[assume atom_number (lambda (atom) (+ 0 atom) ) ]

[assume range (lambda (n) (if (= n 1) (list 0)
                            (append (range (- n 1)) (- n 1) ) )) ]
[assume ones (mem (lambda (n) (map (lambda (x) 1) (range n) ) ) )]

'''


def test_funcs(model,backend='puma'):
    v=load_ripl(model,backend=backend)
    # test count functions
    assert v.sample('(append (list) 1)') == v.sample('(list 1)')
    assert map(int, v.sample('(range 5)')) == range(5)
    colors5 = [v.predict('(bag_t_color 0 %i)'%i) for i in range(5)]
    assert colors5 == v.predict('(bag_t_list 0 5)')
    counts5 = lambda color: sum( map(lambda x: x==color, colors5) )
    for color in range(colors):
        assert counts5(color) == v.predict('(bag_t_color_counts 0 5 %i)'%color)

    #test scopes
    v.predict('(t_color 0)')
    [v.infer('(mh %s one 1)'%scope) for scope in ('hyper_alpha','prototypes','latents') ]

    #test latents
    assert set( map(int,[v.sample('(draw_bag %i)'%i) for i in range(50)]) ) == set( range(bags) )
    assert set( map(int,[v.sample('(t_color %i)'%t) for t in range(100)]) ) == set( range(colors) )

    # test types
    assert v.sample('(not (is_atom (draw_bag 0) ) )')
    assert v.sample('(is_atom (t_color 0) )')
    assert v.sample('(is_atom (categorical (bag_prototype 0)))')

    
def load_ripl(model,observes=None,backend='puma'):
    v = mk_p_ripl() if backend=='puma' else mk_l_ripl()
    v.load_prelude()
    v.execute_program(model)
    if observes:
        [v.observe(*el) for el in observes]
    return v


def model_string(bags,colors):
    prior = ' '.join( ['(+ .1 (poisson 2))']*colors )
    prior = ' '.join( ['(uniform_continuous 0.05 3)']*colors )

    s = utils_string + '''
    [assume bag_t_color (mem (lambda (bag t)
                              (categorical (bag_prototype bag) ) ) ) ]

    [assume bag_t_list (lambda (bag t)
                        (map (lambda (x) (atom_number x))
                          (map (lambda (x)(bag_t_color bag x) ) (range t) ) ) )]

    [assume bag_t_color_counts (lambda (bag t color)
                                 (sum (map (lambda (x)(if (= x color) 1 0))
                                             (bag_t_list bag t) ) ) ) ]
    [assume scale (lambda (lst)
                   (map (lambda (x) (* 5 x)) lst) ) ] 
    [assume colors %i]
    [assume bags %i]
    [assume hyper_alpha_d (lambda ()
                            (scope_include (quote hyper_alpha_d) 0
                                (scale
                                  (simplex_list 
                                    (dirichlet (ones colors) )))))]

    [assume hyper_alpha (scope_include (quote hyper_alpha) 0
                            (array %s) )]
    [assume bag_prototype (mem (lambda (bag)
                               (scope_include (quote prototypes) bag
                                   (dirichlet hyper_alpha) ) ) )]

    [assume draw_bag (mem (lambda (t)
                           (scope_include (quote latents) t
                            (atom_number
                                (uniform_discrete 0 bags) ) ) ))]

    [assume t_color (mem (lambda (t) 
                           (categorical 
                             (bag_prototype (draw_bag t) ) ) )) ]

    '''%(colors,bags,prior)
    return s

def no_count_string(bags,colors):
    prior = ' '.join( ['(uniform_continuous 0.05 3)']*colors )
    s='''
    [assume atom_number (lambda (atom) (+ 0 atom) ) ]

    [assume bags %i]

    [assume hyper_alpha (scope_include (quote hyper_alpha) 0
                            (array %s) )]

    [assume bag_prototype (mem (lambda (bag)
                               (scope_include (quote prototypes) bag
                                   (dirichlet hyper_alpha) ) ) )]

    [assume draw_bag (mem (lambda (t)
                           (scope_include (quote latents) t
                             (atom_number
                               (uniform_discrete 0 bags) ) )) )]

    [assume t_color (mem (lambda (t) 
                           (categorical 
                             (bag_prototype (draw_bag t) ) ) )) ]

    '''%(bags,prior)
    return s

## NOTES on no_counts
# (categorical (bag_prototype bag) ) = atom
# (t_color t) = atom
# but *bag* and *t* are numbers


def dirmult_string(colors,bags):
    s='''
    [assume colors %i]
    [assume bags %i]
    [assume hyper_alpha (scope_include (quote hyper_alpha) 0
                            (array %s) )]
    [assume bag_dirmult (mem (lambda (bag)
                               (scope_include (quote dirmults) bag
                                   (make_dir_mult hyper_alpha))))]
    [assume bag_draw (lambda (bag) ( (bag_dirmult bag) ) ) ]'''


def uncollapsed_observes(bags,colors,latents,dataset,N,num_latents):
    obs = lambda bag,color: ('(categorical (bag_prototype %i) )'%bag,'atom<%i>'%color)
    even = [(b,c) for b in range(bags) for c in range(colors) ] * N
    conc = [(b, np.mod(b,colors)) for b in range(bags)]*N
    data = conc if dataset=='conc' else even_data
    observes= [obs(*bag_color) for bag_color in data]

    split = int(num_latents * .5)
    l_data = [(t,0) for t in range(split)]+[(t,1) for t in range(split,num_latents)]
    obs = lambda t,color: ('(t_color %i)'%t, 'atom<%i>'%color)
    latent_observes = [obs(*t_color) for t_color in l_data]
    if latents: observes.extend(latent_observes)
    return observes

    
def infer_loop(v,query_exps, infer_prog=10, limit=10):
  print '\n---\n query_exps: ',query_exps
  print 'infer_prog: ',infer_prog

  for i in range(limit):
    print np.round( map( v.sample, query_exps), 2 )
    v.infer( infer_prog )

    
def check(latents,num_latents):
    print 'dataset: ', dataset
    print 'hyper_alph: ', np.round(v.sample('hyper_alpha'),2)
    print 'ptypes: ', np.round( map(v.sample,['(bag_prototype %i)'%bag for bag in range(bags)]), 2)

    if latents:
        latents_vals = [v.sample('(draw_bag %i)'%i) for i in range(num_latents)] 
        print latents_vals
        
        
def cycle_infer(repeats=5):
    v.infer('''(cycle ( (mh hyper_alpha one 3)
                      (mh prototypes one 10) ) %i)'''%repeats)
    v.infer('''(cycle ( (mh hyper_alpha one 3)
                      (mh prototypes one 10)
                      (mh latents one 5) ) %i)'''%repeats)
    
def pgibbs_infer( particles_reps=(10,5)):
    v.infer('''(cycle ( (func_pgibbs hyper_alpha one 20 3)
                        (func_pgibbs prototypes one 20 3) )
                        5)''')
    v.infer('''(cycle ( (func_pgibbs hyper_alpha one 20 3)
                        (func_pgibbs prototypes one 20 3)
                        (func_pgibbs latents one 30 3) )
                        5)''')
                  
# tests
bags,colors = 3,3
backend = 'puma'
latents = True
dataset = 'conc'
N = 8  # num balls per bag
num_latents = 6
m = model_string(bags,colors)
test_funcs(m,backend); print m

# observes
observes = uncollapsed_observes(bags,colors,latents,dataset,N,
                                num_latents)

## run inference
v=load_ripl(m,observes,backend=backend)
print 'before inf: ', check(latents,num_latents)
cycle_infer()
check(latents,num_latents)



def query_exps(bags,colors,num_latents):
    hyp = ['(lookup hyper_alpha %i)'%c for c in range(colors)]
    protos = []
    for b in range(bags):
        for c in range(colors):
            protos.append('(lookup (bag_prototype %i) %i)'%(b,c))
    latents= ['(draw_bag %i)'%i for i in range(num_latents) ]
    return hyp+protos+latents




# no latents, t for each bag
def t_per_bag():
    obs1 = lambda bag,t,color: ('(bag_t_color %i %i)'%(bag,t),'atom<%s>'%color)
    even_data1 = []
    for bag in range(bags):
        color_seq = range(colors) * 2
        for t,color in enumerate(color_seq):
            even_data1.append( (bag,t,color) )

    data = even_data1
    observes  = [obs1(*bag_color) for bag_color in data]









