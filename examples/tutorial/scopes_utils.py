# Copyright (c) 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from venture.venturemagics.ip_parallel import MRipl, make_lite_church_prime_ripl, venture
from venture.venturemagics.ip_parallel import make_puma_church_prime_ripl as make_ripl
import time
import numpy as np
import matplotlib.pylab as plt


# model with no latents / state estimation

def make_simple_bag_string(colors):
    prior = ' '.join( ['(uniform_continuous 0.01 5)']*colors )
    string= '''    
    [assume hyper_alpha (array %s)]
    [assume bag_prototype (mem (lambda (bag)
                                (dirichlet hyper_alpha) ) ) ]
    ''' % prior
    return string

def data_observe(bag,color): 
    return ('(categorical (bag_prototype %i) )'%bag,'atom<%i>'%color)


def make_latent_bag_string(bags,colors, max_alpha_prior=5):
    prior = ' '.join( ['(uniform_continuous 0.01 %i)'%max_alpha_prior]*colors )
    string=''' 
    [assume atom_number (lambda (atom) (+ 0 atom) ) ]   
    [assume bags %i]
    [assume hyper_alpha (array %s)]
    [assume bag_prototype (mem (lambda (bag)
                                 (dirichlet hyper_alpha) ) ) ]

    [assume draw_bag (mem (lambda (t)
                            (atom_number
                                (uniform_discrete 0 bags) ) ) )]

    [assume t_color (mem (lambda (t) 
                           (categorical 
                             (bag_prototype (draw_bag t)) ) ) )]

    ''' % (bags,prior)
    return string

def make_latent_bag_string_scopes(bags,colors,max_alpha_prior=5):
    prior = ' '.join( ['(uniform_continuous 0.01 %i)'%max_alpha_prior]*colors )
    string='''
    [assume atom_number (lambda (atom) (+ 0 atom) ) ]
    [assume bags %i]
    [assume hyper_alpha (scope_include (quote hyper_alpha) 0
                            (array %s) )]

    [assume bag_prototype (mem (lambda (bag)
                               (scope_include (quote prototypes) bag
                                   (dirichlet hyper_alpha) ) ) )]

    [assume draw_bag (mem (lambda (t)
                           (scope_include (quote latent_bags) t
                             (atom_number
                               (uniform_discrete 0 bags) ) )) )]

    [assume t_color (mem (lambda (t) 
                           (categorical 
                             (bag_prototype (draw_bag t) ) ) )) ]

    '''%(bags,prior)
    return string


def data_observe(bag,color): 
    return ('(categorical (bag_prototype %i) )'%bag,'atom<%i>'%color)

def data_latent_observe(t,color):
    return ('(t_color %i)'%t, 'atom<%i>'%color)


### MAKE / DISPLAY NON-LATENTS DATA
def print_data(bags,data):
    for bag in range(bags):
        print '\nbag: ',bag,'colors: ', [el[1] for el in data if el[0]==bag]

def make_even_data(bags,colors, draws_per_bag, max_alpha_prior):
    data = [(bag,color) for bag in range(bags) for color in range(colors)] * draws_per_bag
    params = { '(bag_prototype %i)'%bag:np.array( [1./colors]*colors )  for bag in range(bags)}
    params['hyper_alpha'] = [max_alpha_prior]*colors
    return data, params

def make_conc_data(bags,colors, draws_per_bag, max_alpha_prior):
    data = [(bag, np.mod(bag,colors)) for bag in range(bags)] * draws_per_bag
    ptypes = [np.zeros(colors) for i in range(bags)]
    for bag, zero in enumerate(ptypes):
        zero[np.mod(bag,colors)] = 1
    params = { '(bag_prototype %i)'%bag:ptype for bag,ptype in zip(range(bags),ptypes)}
    params['hyper_alpha'] = [.01]*colors
    return data, params

def make_dataset(dataset,args):
    return make_conc_data(*args) if dataset=='conc' else make_even_data(*args)


def display_compare_queries(ripl,queries,gtruth_params,verbose=True):
    inf_params = {}
    
    for q in queries: # print queries
        if 'draw_bag' not in q and verbose:
            print '%s    :'%q, np.round(ripl.sample(q),2)
        inf_params[q] = ripl.sample(q)
        
    logscore = ripl.get_global_logscore()     
    
    # compare to gtruth
    mse_ptypes = 0
    mse_ar = lambda xs,ys:np.mean( (np.array(xs)-np.array(ys))**2 )
    
    for k in inf_params.keys():
        
        if k=='hyper_alpha':
            mse_alpha = mse_ar(inf_params[k], gtruth_params[k])
        elif 'proto' in k:
            mse_ptypes += mse_ar(inf_params[k], gtruth_params[k])
    if verbose:
        print 'mse ptypes:', mse_ptypes, 'mse hyper:', mse_alpha, 'Logscore: %.2f' % logscore
    
    return dict(logscore=logscore, mse_alpha=mse_alpha, mse_ptypes=mse_ptypes)


## MAKE/ LOAD LATENTS DATA
def make_latent_dataset(num_latents):
    data = []
    for t in range(num_latents):
        color = 0 if (t <=.5*num_latents) else 1
        data.append( (t,color) )
    return data

def load_model(bags,colors,make_string,max_alpha_prior):
    v = make_ripl()
    v.execute_program( make_string(bags,colors,max_alpha_prior) )
    return v

def load_observes(ripl, dataset, make_dataset_args, num_latents, verbose=False):
    data1,gtruth_params = make_dataset(dataset, make_dataset_args )
    data2 = make_latent_dataset( num_latents )
    if verbose:
        #print '----\nObserved draws for each bag: '; print_data(bags,data1)
        print '\n(t,color) for latent observes: ', data2

    observes = [data_observe(*datum) for datum in data1] + [data_latent_observe(*datum) for datum in data2]
    [ripl.observe(*observe) for observe in observes]
    return gtruth_params

def make_queries(bags,num_latents):
    bag_queries = ['(bag_prototype %i)'%bag for bag in range(bags)]
    latents = ['(draw_bag %i)'%t for t in range(num_latents)]
    return ['hyper_alpha'] + bag_queries + latents


