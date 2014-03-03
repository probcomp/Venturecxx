import numpy as np
from numpy.random import randn
import pandas as pd
from scipy import stats
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

def hexbin_plot(x,y):
    fig,ax = subplots()
    ax.hexbin(x, y, gridsize=40, cmap="BuGn", extent=(min(x),max(x), min(y),max(y)) )
    return fig,ax

def kde_plot(x,y):
    fig,ax = subplots()
    sns.kdeplot(x,y,shade=True,cmap=None,ax=ax)
    return fig,ax

from venture.venturemagics.ip_parallel import *; lite=False; clear_all_engines()
mk_l = make_lite_church_prime_ripl; mk_c = make_church_prime_ripl


x_model_crp='''
[assume alpha (uniform_continuous .01 1)]
[assume crp (make_crp alpha) ]
[assume z (mem (lambda (i) (crp) ) ) ]
[assume mu (mem (lambda (z) (normal 0 5) ) ) ] 
[assume sig (mem (lambda (z) (uniform_continuous .1 8) ) ) ]
[assume x (mem (lambda (i) (normal (mu (z i)) (sig (z i))))  ) ]
'''
x_model_t='''
[assume nu (gamma 10 1)]
[assume x (mem (lambda (i) (student_t nu) ) )]
'''
pivot_model='''
[assume w0 (mem (lambda (p)(normal 0 3))) ]
[assume w1 (mem (lambda (p)(normal 0 3))) ]
[assume w2 (mem (lambda (p)(normal 0 1))) ]
[assume noise (mem (lambda (p) (gamma 2 1) )) ]
[assume pivot (normal 0 5)]
[assume p (lambda (x) (if (< x pivot) 0 1) ) ]

[assume f (lambda (x w0 w1 w2) (+ w0 (* w1 x) (* w2 (* x x) ) ) ) ]

[assume f2 (lambda (x)
             ( (lambda (p) (+ (w0 p) (* (w1 p) x) (* (w2 p) (* x x)))  ) 
               (p x)  ) ) ]

[assume noise_p (lambda (fx p) (normal fx (noise p)) )] 

[assume y_x (lambda (x) 
                ( (lambda (p) (noise_p  (f x (w0 p) (w1 p) (w2 p)) p ) )
                     (p x) ) ) ]

[assume y (mem (lambda (i) (noise_p  (f (x i) (w0 (p (x i))) (w1 (p (x i))) (w2 (p (x i)) ))  (p (x i)) ) ) ) ]

[assume y2 (mem (lambda (i) 
                ( (lambda (x p)
                    (noise_p  (f x (w0 p) (w1 p) (w2 p)) p ) )
                     (x i) (p (x i)) 
                     ) ) ) ]
[assume n (gamma 1 1) ]
'''

pivot_check='''
[observe (x 0) 0.]
[observe pivot 20.]
[observe (w0 0) 0.]
[observe (w1 0) 1.]
[observe (w2 0) 0.]
[observe (noise 0) .01]'''

def test_pivot(v):
    v.execute_program(pivot_check)
    v.infer(1)
    assert v.predict('(= 0 (p (x 0)))')
    assert 0 == v.predict('(f (x 0) (w0 (p 0)) (w1 (p 0)) (w2 (p 0)))')
    assert .5 > (0 - v.assume('y0','(y 0)') ) # y0 close to 0
    assert .5 > (0 - v.assume('y20','(y2 0)') ) # y0 close to 0

    xys = [v.predict('(list (x %i) (y %i))' % (i,i)) for i in range(10) ];
    xy2s = [v.predict('(list (x %i) (y2 %i))' % (i,i)) for i in range(10) ];
    assert all( [ .5 > (xy[0] - xy[1]) for xy in xy2s ] )
    
    f2= np.array( [v.predict('(f2 %i)' % i) for i in range(5)] )
    f = np.array( [v.predict('(f %i 0 1 0)' % i) for i in range(5) ] )
    assert all( 0.01 > np.abs(f - f2) )
    [v.observe('(y %i)' % i, str(i+.01) ) for i in range(20,25)]
    y_x20 = np.array( [v.predict('(y_x %i)' % i) for i in range(20,25)] )
    y20 = np.array( [v.predict('(y %i)' % i) for i in range(20,25)] )
    #assert all( [ 2 > (y_x20[i] - y20[i]) for y_x20,y20 ] ) 

v_crp=mk_c(); v_crp.execute_program(x_model_crp+pivot_model)
v_t=mk_l(); v_t.execute_program(x_model_t+pivot_model)
vs=[v_t,v_crp]
[test_pivot(v) for v in vs]

quad_fourier_model='''
[assume w0 (normal 0 3) ]
[assume w1 (normal 0 3) ]
[assume w2 (normal 0 3) ]
[assume omega (normal 0 3) ]
[assume theta (normal 0 3) ]
[assume noise (gamma 2 1) ]

[assume model (if (flip) 1 0) ]
[assume quadratic (lambda (x) (+ w0 (* w1 x) (* w2 (* x x) ) ) ) ]
[assume fourier (lambda (x) (+ w0 (* w1 (sin (+ (* omega x) theta) ) ) ) ) ]
[assume f (if (= model 0) quadratic fourier) ]

[assume y_x (lambda (x) (normal (f x) noise) ) ]
[assume y (mem (lambda (i) (normal (f (x i) ) noise) ) )]
[assume n (gamma 1 1)]
'''
quad_fourier_checks='''
[observe (x 0) 0.]
[observe w0 0.]
[observe w1 1.]
[observe w2 0.]
[observe model 0]
[observe noise .01]
'''

def test_quad_fourier(v):
    v.execute_program(quad_fourier_checks)
    v.infer(1)
    assert .1 > abs( 0 - v.predict('(x 0)') )
    assert 0 == v.predict('model')
    assert 2 > abs( (0 - v.predict('(y 0)') ) )
    xfs = [v.predict('(list x (f (x %i) ))' % i) for i in range(10) ]
    xys = [v.predict('(list (x %i) (y %i))' % (i,i)) for i in range(10) ];
    assert all( [ .5 > (xy[0] - xy[1]) for xy in xys ] )
    assert all( [ xf[1] - xy[1] for (xf,xy) in zip(xfs,xys) ] )    
    assert .1 > ( v.predict('(y 0)') - v.predict('(y_x 0)') )
    print xfs,xys

[v.clear() for v in vs]
[v.execute_program(x_model_t + quad_fourier_model) for v in vs]
#[test_quad_fourier(v) for v in vs]



