from venture.venturemagics.ip_parallel import *
from venture.unit import Analytics

switch_prior = '(uniform_continuous 1 100)'
lam_hypers = '(gamma 1 .3)'

m1='''
[assume lam_start (scope_include (quote hypers) 0 %s )]
[assume lam_coefficient (scope_include (quote hypers) 1 %s )]

[assume switch_point (scope_include (quote switch) 0 %s)]
[assume lam_post_switch (scope_include (quote hypers) 2 (gamma 1 .3))]

[assume lam (lambda (t) (if (< t switch_point) 
                          (+ lam_start (* t lam_coefficient))
                          lam_post_switch ))]
[assume g2b (lambda (t) (poisson (lam t))) ]
'''% (lam_hypers,lam_hypers,switch_prior)
m='''
[assume lam_start (scope_include (quote hypers) 0 (gamma 3 1) )]
[assume lam_coefficient (scope_include (quote hypers) 1 (gamma 3 1) )]


[assume lam (lambda (t) (+ lam_start (* t lam_coefficient)))]
[assume g2b (lambda (t) (poisson (lam t))) ]

'''
v=MRipl(2,local_mode=True)
v.execute_program(m1)
lam_start = 1; lam_coefficient = 1
num_timesteps = 100
switch_point = 50
lam_post_switch = 50

observes = []
for i in range(num_timesteps):
    if i < switch_point:
        [observes.append( ( '(g2b %i)'%i, lam_start + (i*lam_coefficient) ) ) for _ in range(1)]
    else:
        [observes.append( ( '(g2b %i)'%i, lam_post_switch ) ) for _ in range(1)]
    
[v.observe(*obs) for obs in observes];
ana = Analytics(v);

def plot_hypers(h):
    map( h.quickPlot, ('lam_start','lam_coefficient','switch_point','lam_post_switch') )


inf_kwargs = dict( infer='(mh default one 10)',simpleInfer=True )
h,mr = ana.runFromConditional(100,runs=1,**inf_kwargs)
#plot_hypers(h)
