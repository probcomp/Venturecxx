
# #Python Freenode:#Python (channel), minrk or min_rk

from IPython.parallel import Client
from venture.shortcuts import make_church_prime_ripl
import numpy as np
import matplotlib.pylab as plt
from scipy.stats import kde
gaussian_kde = kde.gaussian_kde
import subprocess,time
### PLAN


# for being on master
# doc_strings
# todo list
# need to get the right file path for the fie. can we do this by importing the 
# module first and using the same function to ask where the file is
# need to load up engines before this will work. which mgiht be troublesome, but
# good to iron our problems early

# todo list:
# 1. get to work with import instead of execute
# 2. push and pull ripls: pass a ripl to the constructor. pull all ripls
#    from the mripl. use the functions included but retain labels and 
#    any other arguments of a directive. also consider via pickling (v_lite)
#    (make it easy to save at least one of current ripls to file)
# 3. improve type case-switch and support for mixed types
# 4. add continuous inference and write some unit tests for it
# 5. have local ripl be optional (and update tests that depend on it)
# 6. remove plotting from probes and have plotting that can do timeseries
# 7. think about refactoring so the mripl object has fewer methods



#TODO 1
#- connect to EC2 and create some convenience features for doing so
# - ask about the namespace issues for multiripls

# test waiting on infer, test interactive mode, where an engine or ripl dies and you recover

# - too many methods, find some way to structure better.

# TODO 2
# 1. make display work and plot with discrete and cts inputs. 
#   so the crp example (maybe with ellipsoids). 
#     -- should add snapshot (with total transitions), as display will depend on it.

# 2. probes and scatter?

# - better type mathod

# - work out  

# 3. have the local ripl be optional

#4. map function should intercept infers to update total-transitions?

# 5. add all directives

# 7. want the user to be able to specify a cluster (a Client() output
# object).
# 8. async should be an option for plotting as you might have lots
# of infers as part of your code, or you might easily (in interaction)
# write somethign that causes crashes. (blocking is enemy of 
# interactive development)

# 9. In Master: clear shouldn't destroy the seed (delegate new seed after clear)

# 10. continuous inference




# Notes on Parallel IPython

# Questions
# 1. How exactly to enable user to purge data from a process
# and to shutdown processes. Should we allow one engine
# to fail and still get results back from others (vs. just
# having to restart the whole thing again). 

# 2. Basic design idea: only wait on infer. Everything else
# is synchronous. Do we need to give user the option of 
# making everything asynchronous?

# If not: we could set blocking and then have everything 
# be blocking by default (map not map_sync). 

# For infer, we override by running apply_async. We get
# back an async object.  

# if infer is async, need to think about what if someone combines them
# someone does a %v cell magic and it has (infer 10) in it. 
# might need an infer to finish before the predict. so if 
# waiting for an infer to fnish, what will predict do?

# looks life v.predict(1000) waits for v.infer(1000) to finish. is this
# a general rule, that one command will wait for the other? presumably
# otherwise semantics wouldn't work out. 
#  a=v.infer(100000);b= v.predict('100000000000000')


# q: what to do when one or two engines segfault? engines die. how 
# can we recover. engines won't start again. how to properly kill the engines?

# cool stuff: interactive_wait. maybe what we want for stuff involving inference
# cool stuff:  %px from IPython.parallel import bind_kernel; bind_kernel()
#           %px %qtconsole



# seems we can use magic commands in a %px
# and so the engines are running ipython
# --though they don't get the ipy_ripl (why not?)

# question of what happens when you push a function to them
# functions can't be mutated, so a pointer to a function
# should be the same as copying the function, apart from 
# the issue of the enclosing env. so: the function you
# push is like a copy, it doesn't maintain the closure
# (makes sense, coz we can't send across functions with closures)

#e.g. s='local'; f=lambda:s; dv.push({'f':f}); %px f() = error (no s var)


def clear_all_engines():
    cli = Client()
    cli.clear(block=True)

def shutdown():
    cli = Client(); cli.shutdown()

def start_engines(no_engines,sleeptime=10):
    start = subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines,'&'])
    time.sleep(sleeptime)
   
def stop_engines(): 
    stop=subprocess.Popen(['ipcluster', 'stop'])
    stop.wait()


copy_ripl_string="""
def build_exp(exp):
    'Take expression from directive_list and build the Lisp string'
    if type(exp)==str:
        return exp
    elif type(exp)==dict:
        return str(exp['value'])
    else:
        return '('+str(exp[0])+' ' + ' '.join(map(build_exp,exp[1:])) + ')'

def run_py_directive(ripl,d):
    'Removes labels'
    if d['instruction']=='assume':
        ripl.assume( d['symbol'], build_exp(d['expression']) )
    elif d['instruction']=='observe':
        ripl.observe( build_exp(d['expression']), d['value'] )
    elif d['instruction']=='predict':
        ripl.predict( build_exp(d['expression']) )
    
def copy_ripl(ripl,seed=None):
    '''copies ripl via di_list to fresh ripl, preserve directive_id
    by preserving order, optionally set_seed'''
    di_list = ripl.list_directives()
    new_ripl = make_church_prime_ripl()
    if seed: new_ripl.set_seed(seed)
    [run_py_directive(new_ripl,di) for di in di_list]
    return new_ripl
"""

def build_exp(exp):
    'Take expression from directive_list and build the Lisp string'
    if type(exp)==str:
        return exp
    elif type(exp)==dict:
        return str(exp['value'])
    else:
        return '('+str(exp[0])+' ' + ' '.join(map(build_exp,exp[1:])) + ')'

def run_py_directive(ripl,d):
    'Removes labels'
    if d['instruction']=='assume':
        ripl.assume( d['symbol'], build_exp(d['expression']) )
    elif d['instruction']=='observe':
        ripl.observe( build_exp(d['expression']), d['value'] )
    elif d['instruction']=='predict':
        ripl.predict( build_exp(d['expression']) )
    
def copy_ripl(ripl,seed=None):
    '''copies ripl via di_list to fresh ripl, preserve directive_id
    by preserving order, optionally set_seed'''
    di_list = ripl.list_directives()
    new_ripl = make_church_prime_ripl()
    if seed: new_ripl.set_seed(seed)
    [run_py_directive(new_ripl,di) for di in di_list]
    return new_ripl

make_mripl_string='''
try:
    mripls.append([]); no_mripls += 1; seeds_lists.append([])
except:
    mripls=[ [], ]; no_mripls=1; seeds_lists = [ [], ]'''


def make_mripl_string_function():
    try:
        mripls.append([]); no_mripls += 1; seeds_lists.append([])
    except:
        mripls=[ [], ]; no_mripls=1; seeds_lists = [ [], ]


class MRipl():
    
    def __init__(self,no_ripls,client=None,name=None):
        self.local_ripl = make_church_prime_ripl()
        self.local_ripl.set_seed(0)   # same seed as first remote ripl
        self.no_ripls = no_ripls
        self.seeds = range(self.no_ripls)
        self.total_transitions = 0
        
        self.cli = Client() if not(client) else client
        self.dview = self.cli[:]
        self.dview.block = True
        def p_getpids(): import os; return os.getpid()
        self.pids = self.dview.apply(p_getpids)
      
        self.dview.execute('from venture.shortcuts import make_church_prime_ripl')
        self.dview.execute(copy_ripl_string) # defines copy_ripl for self.add_ripl method
        
        self.dview.execute(make_mripl_string)
        self.mrid = self.dview.pull('no_mripls')[0] - 1  # all engines should return same number
        name = 'mripl' if not(name) else name
        self.name_mrid = '%s_%i' % (name,self.mrid)


        def mk_ripl(seed,mrid):
            ripls = mripls[mrid]
            ripls.append( make_church_prime_ripl() )
            ripls[-1].set_seed(seed)
            
            seeds = seeds_lists[mrid]
            seeds.append(seed)
            
        self.dview.map( mk_ripl, self.seeds, [self.mrid]*self.no_ripls )
        self.update_ripls_info()
        print self.display_ripls()
        
    
    def lst_flatten(self,l): return [el for subl in l for el in subl]

    def clear(self):
        ## FIXME still has to reset seeds. note that resetting seeds means
        ## re-running code after a clear will give identical results (add a 
        # convenient way around this)
        self.total_transitions = 0
        self.local_ripl.clear()
        def f(mrid):
            ripls=mripls[mrid]; seeds=seeds_lists[mrid]
            [ripl.clear() for ripl in ripls]
            [ripls[i].set_seed(seeds[i]) for i in range(len(ripls))]
        return  self.dview.apply(f,self.mrid) 
    
    def assume(self,sym,exp,**kwargs):
        self.local_ripl.assume(sym,exp,**kwargs)
        def f(sym,exp,mrid,**kwargs):
            return [ripl.assume(sym,exp,**kwargs) for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f,sym,exp,self.mrid,**kwargs) )
        
    def observe(self,exp,val,label=None):
        self.local_ripl.observe(exp,val,label)
        def f(exp,val,label,mrid): return [ripl.observe(exp,val,label) for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f,exp,val,label,self.mrid) )
    
    def predict(self,exp,label=None,type=False):
        self.local_ripl.predict(exp,label,type)
        def f(exp,label,type,mrid): return [ripl.predict(exp,label,type) for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f,exp,label,type,self.mrid) )

    def infer(self,params,block=False):
        if isinstance(params,int):
            self.total_transitions += params
        else:
            self.total_transitions += params['transitions']
            ##FIXME: consider case of dict more carefully
        self.local_ripl.infer(params)
        
        def f(params,mrid): return [ripl.infer(params) for ripl in mripls[mrid]]

        if block:
            return self.lst_flatten( self.dview.apply_sync(f,params,self.mrid) )
        else:
            return self.lst_flatten( self.dview.apply_async(f,params,self.mrid) )

    def report(self,label_or_did,**kwargs):
        self.local_ripl.report(label_or_did,**kwargs)
        def f(label_or_did,mrid,**kwargs):
            return [ripl.report(label_or_did,**kwargs) for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f,label_or_did,self.mrid, **kwargs) )

    def forget(self,label_or_did):
        self.local_ripl.forget(label_or_did)
        def f(label_or_did,mrid):
            return [ripl.forget(label_or_did) for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f,label_or_did,self.mrid) )

    def execute_program(self,  program_string, params=None):
        self.local_ripl.execute_program( program_string, params )
        def f( program_string, params, mrid):
            return  [ripl.execute_program( program_string,params) for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f, program_string, params,self.mrid) )

    def get_global_logscore(self):
        self.local_ripl.get_global_logscore()
        def f(mrid):
            return [ripl.get_global_logscore() for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f,self.mrid) )

    def sample(self,exp,type=False):
        self.local_ripl.sample(exp,type)
        def f(exp,type,mrid):
               return [ripl.sample(exp,type) for ripl in mripls[mrid] ]
        return self.lst_flatten( self.dview.apply(f,exp,type,self.mrid) )

    def list_directives(self,type=False):
        self.local_ripl.list_directives(type)
        def f(type,mrid):
               return [ripl.list_directives(type) for ripl in mripls[mrid] ]
        return self.lst_flatten( self.dview.apply(f,type,self.mrid) )
               
    def add_ripls(self,no_new_ripls,new_seeds=None):
        'Add no_new_ripls ripls by mapping a copy_ripl function across engines'
        assert(type(no_new_ripls)==int and no_new_ripls>0)

        # could instead check this for each engine we map to
        pids_with_ripls = [ripl['pid'] for ripl in self.ripls_location]
        if any([pid not in pids_with_ripls for pid in self.pids]):
            print 'Error: some engines have no ripl, add_ripls failed'
            return None

        if not(new_seeds):
            # want to ensure that new seeds are different from all existing seeds
            next = max(self.seeds) + 1
            new_seeds = range( next, next+no_new_ripls )

        def add_ripl_engine(seed,mrid):
            # load the di_list from an existing ripl from ripls
            # we only set_seed after having loaded, so all ripls
            # created by a call to add ripls may have same starting values
            ripls=mripls[mrid]; seeds=seeds_lists[mrid]
            ripls.append( copy_ripl(ripls[0]) ) # ripls[0] must be present
            ripls[-1].set_seed(seed)
            seeds.append(seed)
            import os;   pid = os.getpid();
            print 'Engine %i created ripl %i' % (pid,seed)
            
        self.dview.map(add_ripl_engine,new_seeds,[self.mrid]*no_new_ripls)
        self.update_ripls_info()
        print self.display_ripls()
    
    def display_ripls(self):
        s= sorted(self.ripls_location,key=lambda x:x['pid'])
        ##FIXME improve output
        key = ['(pid, index, seed)'] 
        lst = key + [(d['pid'],d['index'],d['seed']) for d in s]
        #[ ('pid:',pid,' seeds:', d['seed']) for pid in self.pids for d
        return lst

    def update_ripls_info(self):
        'nb: reassigns attributes that store state of pool of ripls'
        def get_info(mrid):
            import os; pid=os.getpid()
            
            return [ {'pid':pid, 'index':i, 'seed':seeds_lists[mrid][i],
                      'ripl':str(ripl)  }  for i,ripl in enumerate( mripls[mrid] ) ]
        self.ripls_location = self.lst_flatten( self.dview.apply(get_info,self.mrid) )
        self.no_ripls = len(self.ripls_location)
        self.seeds = [ripl['seed'] for ripl in self.ripls_location]

        
    def remove_ripls(self,no_rm_ripls):
        'map over the engines to remove a ripl if they have >1'
        no_removed = 0
        def check_remove(x,mrid):
            ripls = mripls[mrid]
            if len(ripls) >= 2:
                ripls.pop()
                return 1
            else:
                return 0
       
        while no_removed < no_rm_ripls:
            result = self.dview.map(check_remove,[1]*no_rm_ripls, ([self.mrid]*no_rm_ripls))
            no_removed += len(result)

        ## FIXME should also remove seeds
        self.update_ripls_info()
        print self.display_ripls()

    
    def snapshot(self,labels_lst, plot=False, scatter=False, logscore=False):
        
        if not(isinstance(labels_lst,list)): labels_lst = [labels_lst] 
        values = { did_label: self.report(did_label) for did_label in labels_lst}
        
        if logscore: values['log']= self.get_global_logscore()
        
        out = {'values':values,
               'total_transitions':self.total_transitions,
               'ripls_info': self.ripls_location }

        if plot: out['figs'] = self.plot(out,scatter=scatter)

        return out


    def type_list(self,lst):
        if any([type(lst[0])!=type(i) for i in lst]):
            return 'mixed'
            ## give user a warning and tell them if you cast or leave out some data
        elif isinstance(lst[0],float):
            return 'float'
        elif isinstance(lst[0],int):
            return 'int'
        elif isinstance(lst[0],bool):
            return 'bool'
        elif isinstance(lst[0],str):
            return 'string'
        else:
            return 'other'

        
    def plot(self,snapshot,scatter=False): #values,total_transitions=None,ripls_info=None,scatter_heat=False):
        'values={ did_label: values_list } '
        figs = []
        values = snapshot['values']
        no_trans = snapshot['total_transitions']
        no_ripls = self.no_ripls
        
        for label,vals in values.items():

            var_type = self.type_list(vals)
            
            if var_type =='float':
                fig,ax = plt.subplots(nrows=1,ncols=2,sharex=True,figsize=(9,4))
                xr = np.linspace(min(vals),max(vals),400)
                ax[0].plot(xr,gaussian_kde(vals)(xr))
                ax[0].set_xlim([min(vals),max(vals)])
                ax[0].set_title('Gaussian KDE: %s (transitions: %i, ripls: %i)' % (str(label), no_trans, no_ripls) )

                ax[1].hist(vals)
                ax[1].set_title('Hist: %s (transitions: %i, ripls: %i)' % (str(label), no_trans, no_ripls) )
                [a.set_xlabel('Variable %s' % str(label)) for a in ax]
            
            elif var_type =='int':
                fig,ax = plt.subplots()
                ax.hist(vals)
                ax.set_xlabel = 'Variable %s' % str(label)
                ax.set_title('Hist: %s (transitions: %i, ripls: %i)' % (str(label), no_trans, no_ripls) )
                
            elif var_type =='bool':
                ax.hist(vals)
            else:
                print 'couldnt plot' ##FIXME, shouldnt add fig to figs
            fig.tight_layout()
            figs.append(fig)

            
        if scatter:
            label0,vals0 = values.items()[0]
            label1,vals1 = values.items()[1]
            fig, ax  = plt.subplots(figsize=(6,4))
            ax.scatter(vals0,vals1)
            ax.set_xlabel(label0); ax.set_ylabel(label1)
            ax.set_title('%s vs. %s (transitions: %i, ripls: %i)' % (str(label0),str(label1),
                                                                    no_trans, no_ripls) )
            figs.append(fig)
        
        return figs


    def probes(self,did_label,no_transitions,no_probes,plot_hist=None,plot_series=None):
        label = did_label
        start = self.total_transitions
        probes = map(int,np.round( np.linspace(0,no_transitions,no_probes) ) )
        
        series = [self.snapshot(label)['values'][label], ]
        for i in range(len(probes[:-1])):
            self.infer(probes[i+1]-probes[i])
            series.append( self.snapshot(label)['values'][label] )

        if plot_hist:
            xmin = min([min(shot) for shot in series])
            xmax = max([max(shot) for shot in series])
            xr = np.linspace(xmin,xmax,400)
            fig,ax = plt.subplots(ncols=no_probes,sharex=True,figsize=(10,5))
            kdfig,kdax = plt.subplots(ncols=no_probes,sharex=True,figsize=(10,5))
            for i in range(no_probes):
                ax[i].hist(series[i],bins=12)
                kdax[i].plot(xr,gaussian_kde(series[i])(xr))
                ax[i].set_xlim([xmin,xmax])
                t = '%s: start %i, probe at %i of %i' % (str(label),
                                                               start,probes[i],
                                                               no_transitions)
                ax[i].set_title(t); kdax[i].set_title(t)

            fig.tight_layout(); kdfig.tight_layout()

        if plot_series:
            fig,ax = plt.subplots()
            for ripl in range(self.no_ripls):
                vals = [shot[ripl] for shot in series]
                ax.plot(probes,vals,label='R'+str(ripl))

            t = '%s: start %i, probes at %s' % (str(label),start,str(probes))
            ax.set_title(t)
            #ax.legend()

        return probes,series
    


## mr_map magic utility functions

def lst_flatten(l): return [el for subl in l for el in subl]

def mk_map_proc_string(mripl_name,mrid,proc_name):
    return 'results[-1] = [%s(ripl) for ripl in mripls[%i]] ' % ( proc_name, mrid)
    
add_results_list_string = '''
try: results.append([])
except: results=[ [], ]'''

set_plotting_string = '''
import matplotlib.pylab as plt
%matplotlib inline'''

def mr_map(line, cell):
    'syntax: %%mr_map mripl_name proc_name [optional: store_variable_name, local_ripl] '
    ip = get_ipython()

    assert len(str(line).split()) >= 2, 'Error. Syntax: %%mr_map proc_name mripl_name [optional: store_variable_name] ' 

    # get inputs
    proc_name = str(line).split()[1]
    mripl_name =  str(line).split()[0]
    mripl = eval(mripl_name,globals(),ip.user_ns) ## FIXME: what should globals,locals be?
    mrid = mripl.mrid

    ## FIXME: local_ripl will diverge from remotes if we don't have a third argument
    if len(str(line).split()) > 3:
        ip.run_cell(cell)  # run cell locally, for local ripl (FIXME is the namespace stuff s.t. this works?)
        eval( '%s( %s.local_ripl )' % (proc_name,mripl_name), globals(), ip.user_ns) # eval on local ripl 

    ip.run_cell_magic("px", '', cell)  #FIXME, dview.execute is more general?
    
    ## FIXME: order of these commands (run_cell_mag, execute(plotting)) seems to matter. why?
    mripl.dview.execute(set_plotting_string) # matplotlib, inlining
    mripl.dview.execute(add_results_list_string)    

    map_proc_string = mk_map_proc_string(mripl_name,mrid,proc_name)
    mripl.dview.execute(map_proc_string)  # execute the proc across all ripls

    outputs_by_ripl = lst_flatten( mripl.dview.apply( lambda: results[-1]) ) # pull the result of map_proc

    out_dict = {'info':{'mripl':mripl_name,'proc':proc_name}, 'out':outputs_by_ripl }
    
    # store in user_ns under input var_name
    if len(str(line).split()) > 2: 
        var_name = str(line).split()[2]
        ip.push({ var_name: out_dict } )
        print '%s = ' % var_name

    return out_dict


## all version where user hands a function (which has to only include variables that 
# are in the %px namespace
def mr_map_nomagic(mripl,proc):
    'Push proc into engine namespaces. Use execute to map across ripls.'
    proc_name = 'user_proc_' + str( abs(hash(proc)) )
    mripl.dview.push( { proc_name: proc} )
    mripl.dview.execute(set_plotting_string) # matplotlib, inlining

    mripl.dview.execute('print %s' % proc_name)
    mripl.dview.execute( 'results_%s =  [ %s(ripl) for ripl in mripls[%i] ] ' % (proc_name, proc_name, mripl.mrid) )

    outputs_by_ripl = lst_flatten( mripl.dview['results_%s' % proc_name] )
    # could also pass the procedure out
    out_dict = {'info':{'mripl':mripl.name_mrid,'proc':proc_name}, 'out':outputs_by_ripl }
    
    return out_dict






## Consider Version where we use execute instead of %px
    # one way: define function locally and sent it to all ripls
    #f_name = f_name_parens[:f_name_parens.find('(')]
    #res1 = v.dview.apply_sync(lambda:[func(r) for r in ripls])
    
    # second way: run all the code, which could include various 
    # defines and imports needed for the function, across all engines
    # then execute code that maps the defined function across all ripls
    # in an engine and pull out the resulting object (should be something
    # one can pull).

try:
    ip = get_ipython()
    ip.register_magic_function(mr_map, "cell")    
except:
    print 'no ipython'

def sp(no_ripls=2):    
    v = MRipl(no_ripls)
    v.assume('r','(normal 0 30)',label='r')
    v.assume('s','(normal 0 30)',label='s')
    v.assume('w1','(normal (+ r s) 5.)',label='w1')
    v.observe('w1','50.')
    v.assume('w2','(normal (+ r s) 6.)',label='w2')
    v.observe('w2','50.')
    return v

def crp(no_ripls=2):
    prog='''
    [assume alpha (uniform_continuous .9 1)]
    [assume crp (make_crp alpha) ]
    [assume z (mem (lambda (i) (crp) ) ) ]
    [assume mu (mem (lambda (z dim) (normal 0 30) ) ) ] 
    [assume sig (mem (lambda (z dim) (uniform_continuous .1 1) ) ) ]
    [assume x (mem (lambda (i dim) (normal (mu (z i) dim) (sig (z i) dim)))  ) ]'''
    v=make_church_prime_ripl()
    v.execute_program(prog)
    n=100
    xs = [v.predict('(x ' + str(i) + ' ' +str(j) +')') for i in range(n) for j in range(2) ]
    obs = [v.observe('(x ' + str(i) + ' ' +str(j) +')', str(xs[i*(j+1)]) ) for i in range(n) for j in range(2) ]
    x=np.array(xs)[range(0,len(xs),2)]
    y=np.array(xs)[range(1,len(xs),2)]
    return prog,v,xs,x,y

# clear_all_engines()
# no_rips = 5
# v=MRipl(no_rips)

# # test what happens when ripl directives results in exception or segfault
# def m(x):
#     import os; pid=os.getpid()
#     if pid%4==0:
#         [r.predict('(categorical 2 2)') for r in mripls[0] ]
#         return [r.predict('x') for r in mripls[0]]
#     else:
#         return [r.predict('5') for r in mripls[0]]

# ans=v.dview.map_async(m,range(no_rips))










        

