import numpy as np
from numpy.random import randn
import pandas as pd
from scipy import stats
import matplotlib as mpl
import matplotlib.pyplot as plt
#import seaborn as sns

def hexbin_plot(x,y):
    fig,ax = subplots()
    ax.hexbin(x, y, gridsize=40, cmap="BuGn", extent=(min(x),max(x), min(y),max(y)) )
    return fig,ax

def kde_plot(x,y):
    fig,ax = subplots()
    sns.kdeplot(x,y,shade=True,cmap=None,ax=ax)
    return fig,ax

from venture.venturemagics.ip_parallel import *; 
lite=False; 
mk_l = make_lite_church_prime_ripl; mk_c = make_church_prime_ripl


x_model_crp='''
[assume alpha (uniform_continuous .01 1)]
[assume crp (make_crp alpha) ]
[assume z (mem (lambda (i) (crp) ) ) ]
[assume mu (mem (lambda (z) (normal 0 5) ) ) ] 
[assume sig (mem (lambda (z) (uniform_continuous .1 8) ) ) ]
[assume x_d (lambda () ( (lambda (z) (normal (mu z) (sig z) )) (crp) ) ) ]
[assume x (mem (lambda (i) (normal (mu (z i)) (sig (z i))))  ) ]
'''
x_model_t='''
[assume nu (gamma 10 1)]
[assume x_d (lambda () (student_t nu) ) ]
[assume x (mem (lambda (i) (x_d) ) )]
'''
pivot_model='''
[assume w0 (mem (lambda (p)(normal 0 3))) ]
[assume w1 (mem (lambda (p)(normal 0 3))) ]
[assume w2 (mem (lambda (p)(normal 0 1))) ]
[assume noise (mem (lambda (p) (gamma 2 1) )) ]
[assume pivot (normal 0 5)]
[assume p (lambda (x) (if (< x pivot) 0 1) ) ]

[assume f (lambda (x)
             ( (lambda (p) (+ (w0 p) (* (w1 p) x) (* (w2 p) (* x x)))  ) 
               (p x)  ) ) ]

[assume noise_p (lambda (fx x) (normal fx (noise (p x))) )] 

[assume y_x (lambda (x) (noise_p (f x) x) ) ]
                     
[assume y (mem (lambda (i) (y_x (x i))  ))] 
                     
[assume n (gamma 1 1) ]
[assume model_name (quote pivot)]
'''

quad_fourier_model='''
[assume w0 (normal 0 3) ]
[assume w1 (normal 0 3) ]
[assume w2 (normal 0 1) ]
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
[assume model_name (quote quad_fourier)]'''

logistic_model='''
[assume w0 (normal 0 3)]
[assume w1 (normal 0 3) ]
[assume log_mu (normal 0 3)]
[assume log_sig (normal 0 3) ]
[assume noise (gamma 2 1) ]

[assume sigmoid (lambda (x) (/ (- 1 (exp (* (- x log_mu) (* -1 log_sig) )) )
                               (+ 1 (exp (* (- x log_mu) (* -1 log_sig) )) ) ) )]
[assume f (lambda (x) (+ w0 (* w1 (sigmoid x) ) ) ) ]

[assume y_x (lambda (x) (normal (f x) noise) ) ]
[assume y (mem (lambda (i) (normal (f (x i) ) noise) ) )]
[assume n (gamma 1 1)]
[assume model_name (quote logistic)]'''


def mk_piecewise(weight=.5,quad=True):
    s='''
    [assume myceil (lambda (x) (if (= x 0) 1
                                 (if (< 0 x)
                                   (if (< x 1) 1 (+ 1 (myceil (- x 1) ) ) )
                                   (* -1 (myceil (* -1 x) ) ) ) ) ) ]
    [assume w0 (mem (lambda (p)(normal 0 3))) ]
    [assume w1 (mem (lambda (p)(normal 0 3))) ]
    [assume w2 (mem (lambda (p)(normal 0 1))) ]
    [assume noise (mem (lambda (p) (gamma 2 1) )) ]
    [assume width <<width>>]
    [assume p (lambda (x) (myceil (/ x width)))]

    [assume f (lambda (x)
                 ( (lambda (p) (+ (w0 p) (* (w1 p) x) (* (w2 p) (* x x)))  ) 
                   (p x)  ) ) ]

    [assume noise_p (lambda (fx x) (normal fx (noise (p x))) )] 

    [assume y_x (lambda (x) (noise_p (f x) x) ) ]

    [assume y (mem (lambda (i) (y_x (x i))  ))] 

    [assume n (gamma 1 1) ]
    [assume model_name (quote piecewise)]
    '''
    if not(quad):
        s= s.replace('[assume w2 (mem (lambda (p)(normal 0 1))) ]',
                     '[assume w2 0]')
    return s.replace('<<width>>',str(weight))

def v_mk_piecewise(weight,quad):
    v=mk_l()
    v.execute_program(x_model_t + mk_piecewise(weight=weight,quad=quad))
    return v

def test_piecewise():
    ##FIXME try with lite
    def v_mk_piecewise(weight,quad):
        v=mk_c()
        v.execute_program(x_model_t + mk_piecewise(weight=weight,quad=quad))
        return v
    v=v_mk_piecewise(.2,True)
    xys=[ (.1*i,.1*i) for i in range(-6,6) ] * 6
    no_trans=1000
    observe_infer([v],xys,no_trans,with_index=True,withn=True)
    a,b,c = v.sample('(list (f -.3) (f .05) (f .3))')
    assert a<b<c
    fig,xr,y_x = plot_cond(v)
    ax = fig.axes[0]
    ax.set_ylim(-1,1); ax.set_xlim(-1,1)

    v=v_mk_piecewise(.5,False)
    xys=[ (x,abs(x)) for x in np.linspace(-1,1,20)]
    xys.extend( [ (x,-0.5*x) for x in np.linspace(1.1,2,20) ] )
    no_trans=1000
    observe_infer([v],xys,no_trans,with_index=True,withn=True)
    a,b,c = v.sample('(list (f -.3) (f .05) (f .5))')
    print a,b,c
    fig,xr,y_x = plot_cond(v)
    ax = fig.axes[0]
    ax.set_ylim(-2.5,2,5); ax.set_xlim(-2,2.8)


def generate_data(n,xparams=None,yparams=None,sin=True):
    'loc,scale = xparams, w0,w1,w2,omega,theta = yparams'
    if xparams:
        loc,scale = xparams; xs = np.random.normal(loc,scale,n)
    else:
        xs = np.random.normal(loc=0,scale=2.5,size=n)
    if yparams:
        w0,w1,w2,omega,theta = yparams
        ys = w0*(np.sin(omega*xs + theta))+w1 if sin else w0+(w1*xs)+(w2*(xs**2))
    else:
        ys = 3*np.sin(xs)
        
    xys = zip(xs,ys)
    fig,ax = plt.subplots(figsize=(6,2))
    ax.scatter(xs,ys);
    ax.set_title('Data from f w/ %s )' % str(yparams) ) if yparams else ax.set_title('Data from 3sin(x)')
    return xys


def observe_infer(vs,xys,no_transitions,with_index=True,withn=True):
    '''Input is list of ripls or mripls, xy pairs and no_transitions. Optionally
    observe the n variable to be the len(xys). We can either index the observations
    or we can treat them as drawn from x_d and y_x, which do not memoize but depend
    on the same hidden params. (Alternatively we could work out the last index and
    start from there).'''
    if with_index:
        for i,(x,y) in enumerate(xys):
            [v.observe('(x %i)' % i , '%f' % x, label='x%i' % i) for v in vs]
            [v.observe('(y %i)' % i , '%f' % y, label='y%i' % i ) for v in vs]
    else:        
        ## FIXME find some good labeling scheme
        for i,(x,y) in enumerate(xys):
            [v.observe('(x_d)', '%f' % x ) for v in vs]
            [v.observe('(y_x %f)' % x , '%f' % y ) for v in vs]
    if withn: [v.observe('n','%i' % len(xys)) for v in vs]

    [v.infer(no_transitions) for v in vs];


def logscores(mr,name='Model'):
    logscore = mr.get_global_logscore()
    try: name=mr.sample('model_name')
    except: pass
    print '%s logscore: (mean, max) ' % name, np.mean(logscore), np.max(logscore)
    return np.mean(logscore), np.max(logscore)


def get_name(r_mr):  # FIXME dealing with ripl vs. mripl
    mr=1 if isinstance(r_mr,MRipl) else 0
    di_l = r_mr.list_directives()[0] if mr else r_mr.list_directives()
    if 'model_name' in str(di_l):
        try:
            n = r_mr.sample('model_name')[0] if mr else r_mr.sample('model_name')
            return n
        except: pass
    else:
        return 'anon model'


def plot_cond(ripl,no_reps=50,set_xr=None,plot=True):
    '''Plot f(x) with 1sd noise curves. Plot y_x with #(no_reps)
    y values for each x. Use xrange with limits based on posterior on P(x).'''
    
    if set_xr!=None:
        xr=set_xr
    else: # find x-range from min/max of observed points
        n = int( np.round( ripl.sample('n') ) )  #FIXME
        xs = [ripl.sample('(x %i)' % i) for i in range(n)]
        ys = [ripl.sample('(y %i)' % i) for i in range(n)]
        xr = np.linspace(1.5*min(xs),1.5*max(xs),20)
    
    f_xr = [ripl.sample('(f %f)' % x) for x in xr]
    
    # gaussian noise 1sd
    h_noise = ['pivot','piecewise']
    model_name=get_name(ripl)
    noise=ripl.sample('(noise 0)') if model_name in h_noise else ripl.sample('noise')
    f_a = [fx+noise for fx in f_xr]
    f_b = [fx-noise for fx in f_xr]

    # scatter for y conditional on x
    if plot:
        y_x = [  [ripl.sample('(y_x %f)' % x) for r in range(no_reps)] for x in xr]
        fig,ax = plt.subplots(1,2,figsize=(12,4),sharex=True,sharey=True)
        if set_xr==None: ax[0].scatter(xs,ys)
        ax[0].set_color_cycle(['m', 'gray','gray'])
        ax[0].plot(xr,f_xr,xr,f_a,xr,f_b)
        ax[0].set_title('Data and inferred f with 1sd noise (name= %s )' % model_name)

        [ ax[1].scatter(xr,[y[i] for y in y_x],s=5,c='gray') for i in range(no_reps) ]
        ax[1].set_title('Single ripl: P(y/X=x,params fixed) for uniform x-range (name= %s)' % model_name)
        fig.tight_layout()

        return fig,xr,y_x
    return xr,y_x


def plot_joint(ripl,no_reps=500):
    '''Sample from joint P(x,y) and plot as histogram and kde.'''
    xs = [ ripl.sample('(x_d)') for i in range(no_reps) ]
    ys = [ ripl.sample('(y_x %f)' % x) for x in xs]
    
    fig,ax = plt.subplots(1,2,figsize=(12,4),sharex=True,sharey=True)
    ax[0].scatter(xs,ys,s=5,c='gray')
    ax[0].set_title('Single ripl: %i samples from P(x,y)' % no_reps)
    H, xedges, yedges = np.histogram2d(xs, ys, bins=(12, 12))
    extent = [yedges[0], yedges[-1], xedges[-1], xedges[0]]
    ax[1].imshow(H, extent=extent, interpolation='nearest')
    ax[1].set_title('Single ripl: hist of %i samples from P(x,y) (name= %s)' % (no_reps,get_name(ripl)) )
    return xs,ys


def plot_ygivenx(mr,x):
    return mr.snapshot(exp_list=['(y_x %f)' % x ],plot=True)

def plot_xgiveny(mr,y,no_transitions=100):
    '''P(x / Y=y), by combining ripls in mr. Works by finding next unused observation
    label, setting Y=y for that observation, running inference, sampling x and then
    forgetting the observation of y. NB: locally disruptive of inference.'''
    
    obs_label = [di for di in mr.list_directives()[0] if di['instruction']=='observe' and di.get('label')]
    # labels should have form 'y1','y2', etc.
    if obs_label:
        y_nums = [int(di['label'][1:]) for di in obs_label if di['label'].startswith('y')]
        next_label = max(y_nums)+1
    else:
        next_label = int(np.random.randint(1000,10**8))
    
    mr.observe('(y %i)' % next_label, str(y), label='y%i' % next_label )
    mr.infer(no_transitions)
    snapshot=mr.snapshot(exp_list=['(x %i)' % next_label],plot=True)
    mr.forget('y%i' % next_label)
    return snapshot


def params_compare(mr,exp_pair,xys,no_transitions,plot=False):
    '''Look at dependency as data comes in'''
    
    # get prior values
    out_pr = mr.snapshot(exp_list=exp_pair,plot=plot,scatter=False)
    vals_pr = out_pr['values']
    out_list = [out_pr]; vals_list=[vals_pr] 
    
    # add observes
    for i,xy in enumerate(xys):
        observe_infer([mr],[xy],no_transitions,with_index=False,withn=False) # FIXME obs n somewhere?
        out_list.append( mr.snapshot(exp_list=exp_pair,plot=plot,scatter=False) )
        vals_list.append( out_list[-1]['values'] )
        
    xys=np.array(xys); xs=[None] + list( xys[:,0] ); ys=[None] + list( xys[:,1] )

    fig,ax = plt.subplots(len(vals_list), 2, figsize=(12,len(vals_list)*4))

    for i,vals in enumerate(vals_list):
        ax[i,0].scatter( vals[exp_pair[0]], vals[exp_pair[1]], s=6)
        ax[i,0].set_title('%s vs. %s' % (exp_pair[0],exp_pair[1]))
        ax[i,0].set_xlabel(exp_pair[0]); ax[i,0].set_ylabel(exp_pair[1])
        if i>0:
            ax[i,1].scatter(xs[1:i], ys[1:i], c='blue') ## FIXME start from 1 to ignore prior
            ax[i,1].scatter(xs[i], ys[i], c='red')
            ax[i,1].set_title('Observed data with new point')
        
    fig.tight_layout()
    return fig,vals_list


def plot_posterior_conditional(mr,no_reps=50,set_xr=None,plot=True):    
    if set_xr!=None:
        xr = set_xr
    else:
        # find x-range from min/max of observed points
        # only look at output of first ripl
        n = int( np.round( mr.sample('n')[0] ) )  #FIXME
        xs = [mr.sample('(x %i)' % i)[0] for i in range(n)]
        ys = [mr.sample('(y %i)' % i)[0] for i in range(n)]
        xr = np.linspace(1.5*min(xs),1.5*max(xs),20)

    if plot:
        # = [ [samples from (y_x x)] for x in xr]
        #where higher no_reps only gives better picture of individual noise
        y_x = [  if_lst_flatten( [mr.sample('(y_x %f)' % x) for r in range(no_reps)] ) for x in xr]
          
        fig,ax = plt.subplots(figsize=(10,5),sharex=True,sharey=True)
        if set_xr==None: ax.scatter(xs,ys,c='m')
    
        [ ax.scatter(xr,[y[i] for y in y_x],s=6,c='gray') for i in range(no_reps) ]
        ax.set_title('Mripl: P(y/X=x) for uniform x-range (name= %s)' % get_name(mr))
    return xr,y_x


def plot_posterior_joint(mr,no_reps=500,plot=True):
    xy_st ='( (lambda (xval) (list xval (y_x xval)) ) (x_d) )'
    xys = if_lst_flatten( [mr.sample(xy_st) for i in range(no_reps) ] )
    print xys[:5]
    xs= [xy[0] for xy in xys]; ys=[xy[1] for xy in xys]
    
    fig,ax = plt.subplots(1,2,figsize=(12,4),sharex=False,sharey=False)
    ax[0].scatter(xs,ys,s=5,c='m')
    ax[0].set_title('Samples from P(x,y). (%i ripls, %i reps)' % (mr.no_ripls,
                                                                 no_reps) )
    H, xedges, yedges = np.histogram2d(xs, ys, bins=(12, 12))
    extent = [yedges[0], yedges[-1], xedges[-1], xedges[0]]
    ax[1].imshow(H, extent=extent, interpolation='nearest')
    ax[1].set_title('MRipl: hist of %i samples from P(x,y) (name= %s)' % (no_reps,get_name(mr)) )
    return xys


def test_plot_posterior_joint():
    xys = generate_data(14,xparams=[0,1],yparams=[0,0,1,0,0],sin=False) # y=x^2
    v_piv = MRipl(10,lite=lite,verbose=False);
    v_piv.execute_program(x_model_t+pivot_model)
    observe_infer([v_piv],xys,300)
    xys=np.array(plot_posterior_joint(v_piv,no_reps=40))
    xs=xys[:,0], ys=xys[:,1]
    assert .5 > abs( np.mean(xs) )
    assert abs( np.mean(ys) ) > abs( np.mean(xs) )

    return None

def test_params_compare():
    xys = [(2,20),(0,0),(0.5,2),(-0.4,2),(1,5),(-1,5),(2.5,31)] # y=5x^2
    v_pivt = MRipl(40,lite=lite,verbose=False); v_pivcrp = MRipl(2,lite=lite,verbose=False)
    vs = [v_pivt]#,v_pivcrp] FIXME
    v_pivt.execute_program(x_model_t+quad_fourier_model)
    v_pivcrp.execute_program(x_model_crp+quad_fourier_model)
    
    no_transitions=75
    outs=[params_compare(v,['w2','noise'],xys,no_transitions) for v in vs]
    return None
    

def test_plot_posterior_conditional():
    # check inference quality.piv and fo should learn y=x^2. hence posterior when 
    # xr~0 is mean~0 (both models should have relevant symmetry)
    xys = generate_data(14,xparams=[0,1],yparams=[0,0,1,0,0],sin=False) # y=x^2
    v_piv = MRipl(10,lite=lite,verbose=False);
    v_fo = MRipl(10,lite=lite,verbose=False)
    v_piv.execute_program(x_model_t+pivot_model)
    v_fo.execute_program(x_model_t+quad_fourier_model)
    vs = [v_piv,v_fo]

    observe_infer(vs,xys,200,withn=True)
    v_out= [plot_posterior_conditional(v, no_reps=20) for v in vs]
    
    for xr,y_x in v_out:
        fil=[]
        for i,x in enumerate(xr):
            if abs(x)<.1: fil.append(y_x[i])
        print fil
        assert .1 > np.mean(fil)    

def test_plot_posterior_conditional_noisy_y():
    '''When observations of y are noisy, P(y/X=x) will have entropy that 
    depends on the noise for nearby observations'''
    v_piv = MRipl(10,lite=lite,verbose=False);
    v_fo = MRipl(10,lite=lite,verbose=False)
    v_piv.execute_program(x_model_t+pivot_model)
    v_fo.execute_program(x_model_t+quad_fourier_model)
    vs = [v_piv,v_fo]
    def noise_obs(x,y,e):
        return '[observe (normal (y_x %f) %f) %f]' %(x,e,y)
    for v in vs:
        v.execute_program(noise_obs(0,0,.1) + noise_obs(2,2,.1) +
                          noise_obs(-2,-2,1) + noise_obs(-4,-4,1))
        v.infer(200)
    xr =np.linspace(-6,6,30)
    v_out=[plot_posterior_conditional(v,no_reps=40,set_xr=xr) for v in vs]


def test_plot_posterior_conditional_noisy_x():
    '''When observations of x are noisy, we use our prior on x and assume
    that y's came from something closer to prior. Far off xy observations
    will be informative for nearby predictions'''
    def mk_mrs():
        v_piv = MRipl(10,lite=lite,verbose=False);
        v_fo = MRipl(10,lite=lite,verbose=False)
        v_piv.execute_program(x_model_t+pivot_model)
        v_fo.execute_program(x_model_t+quad_fourier_model)
        return [v_piv,v_fo]
    vs = mk_mrs()
    def noise_obs(ind,x,y,e):
        s1= '[observe (normal (x %i) %f) %f]' %(ind,e,x)
        s2='[observe (y %i) %f]' %(ind,y)
        return s1+s2

    ## FIXME,add observed data to plot
    for v in vs:
        v.execute_program(noise_obs(0,0,0,.1) + noise_obs(1,2,2,.1) +
                          noise_obs(2,-2,-2,1) + noise_obs(3,-4,-4,1))
        v.infer(200)
    xr =np.linspace(-6,6,30)
    v_out=[plot_posterior_conditional(v,no_reps=30,set_xr=xr) for v in vs]


    vs=mk_mrs()
    for v in vs:
        v.execute_program(noise_obs(0,14,14,3) + noise_obs(1,2,2,3) +
                          noise_obs(2,-2,-2,3) + noise_obs(3,-14,-14,3))
        v.infer(200)
    xr =np.linspace(-20,20,30)
    v_out=[plot_posterior_conditional(v,no_reps=30,set_xr=xr) for v in vs]    
    
    
def if_lst_flatten(l):
    if type(l[0])==list: return [el for subl in l for el in subl]
    return l
    
    

def test_funcs(mripl=False,n=14,fast=False):
    if fast: n=8
    xys = generate_data(n,xparams=[0,3],yparams=[0,0,1,0,0],sin=False) # y=x^2
        
    if mripl:
        v_piv = MRipl(2,lite=lite,verbose=False); v_fo = MRipl(2,lite=lite,verbose=False)
        vs = [v_piv,v_fo]
    else:
        v_piv = mk_c(); v_fo=mk_c(); vs = [v_piv,v_fo]
    v_piv.execute_program(x_model_t+pivot_model); v_fo.execute_program(x_model_t+quad_fourier_model)

    observe_infer(vs,xys,50,withn=True) if fast else observe_infer(vs,xys,300,withn=True)

    [logscores(v) for v in vs]

    if mripl:
        [mr_map_nomagic(v,plot_cond,limit=1) for v in vs]
    else:
        [plot_cond(v) for v in vs]

    if mripl: ## FIXME look over this test again
        outs = [mr_map_nomagic(v,plot_joint,limit=1)['out'][0] for v in vs]
        for out in outs:
            xs,ys = out
            print np.mean(xs), np.mean(ys)
            if not(fast):
                assert( 2 > np.abs( np.mean(xs) ) )
            else:
                assert( 4 > np.abs( np.mean(xs) ) )
    else:
        outs=[plot_joint(v,no_reps=500) for v in vs]
        for out in outs:
            xs,ys = out
            if not(fast):
                assert( 2 > np.abs( np.mean(xs) ) )
            else:
                assert( 4 > np.abs( np.mean(xs) ) )
        

    # in-sample guess should be close to true vals after enough inference
    [v.infer(300) for v in vs] if not(fast) else [v.infer(100) for v in vs]
    f0 = if_lst_flatten( [v.predict('(f 0)') for v in vs] )
    f1 = if_lst_flatten( [v.predict('(f 1)') for v in vs] )
    f1 = if_lst_flatten( [v.predict('(f -1)') for v in vs] )
    assert all( 10 > np.abs((0 - np.array(f0) ) )) and any( 5 > np.abs((0 - np.array(f0) ) ) )
    assert all( 10 > np.abs((1 - np.array(f1) ) )) and any( 5 > np.abs((1 - np.array(f0) ) ) )
    assert all( 10 > np.abs((1 - np.array(f1) ) )) and any( 5 > np.abs((1 - np.array(f0) ) ) )

    if mripl:  ##FIXME, look over xgiveny for how much inference we need
        snap_outs= [plot_ygivenx(v,0) for v in vs]
        ygiven0 = np.array( snap_outs[0]['values'].values()[0] )
        assert all( 6 > np.abs((0 - ygiven0) ) )

        snap_outs= [plot_xgiveny(v,0) for v in vs]
        xgiven0 = np.array( snap_outs[0]['values'].values()[0] )
        assert all( 6 > np.abs((0 - xgiven0) ) )
    



   


### PLAN: different plots/scores
#1. av logscore and best logscore.
# 2. plot the curve, adding noise error (easiest way is with y_x)
# 3. plot the joint (sample both x's and y's)
# 4. plot posterior on sets of params
# 5. plot posterior conditional
# 6. plot posterior joint (the posterior join density over x,y: get from running chain long time or combining chains)
# 7. plot p(x / y) for some particular y's 

