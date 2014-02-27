from IPython.parallel import Client
from IPython.parallel.util import interactive
from venture.shortcuts import make_church_prime_ripl
from venture.shortcuts import make_lite_church_prime_ripl
import numpy as np
import matplotlib.pylab as plt
from scipy.stats import kde
gaussian_kde = kde.gaussian_kde
import subprocess,time, pickle



### IPython Parallel Magics
## Use: See examples in /examples

# Tasks: 
# 1. get to work with import instead of execute
# 2. push and pull ripls: pass a ripl to the constructor. pull all ripls
#    from the mripl. use the functions included but retain labels and 
#    any other arguments of a directive. also consider via pickling (v_lite)
#    (make it easy to save at least one of current ripls to file)
# 3. improve type case-switch and plotting support for mixed types
# 4. add continuous inference and write some unit tests for it
# 5. have local ripl be optional (and update tests that depend on it)
# 6. remove plotting from probes and have plotting that can do timeseries
# 7. think about refactoring so the mripl object has fewer methods



# Utility functions for working with ipcluster

def clear_all_engines():
    'Clears the namespaces of all IPython remote processes'
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



### Functions needed for the MRipl Class (could be added to scope of the class definition)

# functions that copy ripls by batch loading directives that are constructed from directives_list

@interactive
def build_exp(exp):
    'Take expression from directive_list and build the Lisp string'
    if type(exp)==str:
        return exp
    elif type(exp)==dict:
        return str(exp['value'])
    else:
        return '('+str(exp[0])+' ' + ' '.join(map(build_exp,exp[1:])) + ')'


@interactive
def run_py_directive(ripl,d):
    '''FIXME: currently removes labels from instructions. Should be
    rewritten so that the label (and any other crucial information)
    is retained.'''
    if d['instruction']=='assume':
        ripl.assume( d['symbol'], build_exp(d['expression']) )
    elif d['instruction']=='observe':
        ripl.observe( build_exp(d['expression']), d['value'] )
    elif d['instruction']=='predict':
        ripl.predict( build_exp(d['expression']) )
    
@interactive
def copy_ripl(ripl,seed=None):
    '''copies ripl via directives_list to fresh ripl, preserve directive_id
    by preserving order, optionally set_seed'''
    di_list = ripl.list_directives()
    try: new_ripl = make_ripl()
    except: new_ripl = make_church_prime_ripl()
    if seed: new_ripl.set_seed(seed)
    [run_py_directive(new_ripl,di) for di in di_list]
    return new_ripl

copy_ripl_dict = {'build_exp':build_exp,
                  'run_py_directive':run_py_directive,'copy_ripl':copy_ripl}

# function for creating a list of ripls for each mripl
make_mripl_string='''
try:
    mripls.append([]); no_mripls += 1; seeds_lists.append([])
except:
    mripls=[ [], ]; no_mripls=1; seeds_lists = [ [], ]'''


def make_mripl_func():
    try:
        mripls.append([]); no_mripls += 1; seeds_lists.append([])
    except:
        mripls=[ [], ]; no_mripls=1; seeds_lists = [ [], ]


## MRIPL CLASS

# Create MRipls. Multiple MRipls can be created, sharing the same engines.
# Each engine has a list 'mripl', each element of which is a list 'ripl'
# containing ripls for that mripl. So the mripls are all being run in a
# single namespace on each remote engine.

# The user will mostly interact with an
# mripl via directives like 'mripl.assume(...)', which is applied to each
# ripl of that mripl (across all engines). However, the mripl.dview 
# attribute is a direct-view on the engines and allows the user to 
# execute arbitrary code across the engines, including altering the state
# of other mripls. (The user can also do this via %px). 

# (We can consider ways of making the data of an mripl accessible only
# via the mripl object in the user namespace). 


class MRipl():
    
    def __init__(self,no_ripls,lite=False,verbose=True,client=None,name=None):
        self.lite = lite
        if not self.lite:
            self.local_ripl = make_church_prime_ripl()
        else:
            self.local_ripl = make_lite_church_prime_ripl()
        self.local_ripl.set_seed(0)   # same seed as first remote ripl
        self.no_ripls = no_ripls
        self.seeds = range(self.no_ripls)
        self.total_transitions = 0
        
        self.cli = Client() if not(client) else client
        self.dview = self.cli[:]
        self.dview.block = True
        def p_getpids(): import os; return os.getpid()
        self.pids = self.dview.apply(p_getpids)
      
        if not self.lite:
            self.dview.execute('from venture.shortcuts import make_church_prime_ripl as make_ripl')
        else:
            self.dview.execute('from venture.shortcuts import make_lite_church_prime_ripl as make_ripl')
        
        # import as plt for all plotting (note: user may need to have opened
        # IPNB in inline mode for everything to work -- include in examples)
        self.dview.execute('import matplotlib.pylab as plt')
        self.dview.execute('import pickle')
        self.dview.execute('%pylab inline --no-import-all')
        #self.dview.execute('%pylab inline
        self.dview.push(copy_ripl_dict)
        self.dview.execute(make_mripl_string)
       
       
        self.mrid = self.dview.pull('no_mripls')[0] - 1  # all engines should return same number
        name = 'mripl' if not(name) else name
        self.name_mrid = '%s_%i' % (name,self.mrid)


        @interactive
        def mk_seed_ripl(seed,mrid):
            ripls = mripls[mrid]
            ripls.append( make_ripl() )
            ripls[-1].set_seed(seed)
            
            seeds = seeds_lists[mrid]
            seeds.append(seed)
            
        self.dview.map( mk_seed_ripl, self.seeds, [self.mrid]*self.no_ripls )
        
        ## Extract info from engines and ripls
        self.update_ripls_info()
        
        self.verbose = verbose
        if self.verbose: print self.display_ripls()
        
    
    def lst_flatten(self,l): return [el for subl in l for el in subl]

    def clear(self):
        ## FIXME still has to reset seeds. note that resetting seeds means
        ## re-running code after a clear will give identical results (add a 
        # convenient way around this)
        self.total_transitions = 0
        self.local_ripl.clear()
        @interactive
        def f(mrid):
            ripls=mripls[mrid]; seeds=seeds_lists[mrid]
            [ripl.clear() for ripl in ripls]
            [ripls[i].set_seed(seeds[i]) for i in range(len(ripls))]
        return  self.dview.apply(f,self.mrid) 
    
    def assume(self,sym,exp,**kwargs):
        self.local_ripl.assume(sym,exp,**kwargs)
        
        @interactive
        def f(sym,exp,mrid,**kwargs):
            return [ripl.assume(sym,exp,**kwargs) for ripl in mripls[mrid]]

        if self.lite:
            @interactive
            def f(sym,exp,mrid,**kwargs):
                out = [ripl.assume(sym,exp,**kwargs) for ripl in mripls[mrid]]
                try:
                    pickle.dumps(out)
                    return out
                except:
                    return [None for ripl in mripls[mrid] ]

        return self.lst_flatten( self.dview.apply(f,sym,exp,self.mrid,**kwargs) )
        

    def observe(self,exp,val,label=None):
        self.local_ripl.observe(exp,val,label)
        @interactive
        def f(exp,val,label,mrid): return [ripl.observe(exp,val,label) for ripl in mripls[mrid]]

        if self.lite:
            @interactive
            def f(exp,val,label,mrid):
                out=[ripl.observe(exp,val,label) for ripl in mripls[mrid]]
                try:
                    pickle.dumps(out)
                    return out
                except:
                    return [None for ripl in mripls[mrid] ]
                
        return self.lst_flatten( self.dview.apply(f,exp,val,label,self.mrid) )
    
    def predict(self,exp,label=None,type=False):
        self.local_ripl.predict(exp,label,type)
        @interactive
        def f(exp,label,type,mrid): return [ripl.predict(exp,label,type) for ripl in mripls[mrid]]

        if self.lite:
            @interactive
            def f(exp,label,type,mrid):
                out = [ripl.predict(exp,label,type) for ripl in mripls[mrid]]
                try:
                    pickle.dumps(out)
                    return out
                except:
                    return [None for ripl in mripls[mrid] ]
        
        return self.lst_flatten( self.dview.apply(f,exp,label,type,self.mrid) )

    def infer(self,params,block=False):
        if isinstance(params,int):
            self.total_transitions += params
        else:
            self.total_transitions += params['transitions']
            ##FIXME: consider case of dict more carefully
        self.local_ripl.infer(params)

        @interactive
        def f(params,mrid): return [ripl.infer(params) for ripl in mripls[mrid]]

        if block:
            return self.lst_flatten( self.dview.apply_sync(f,params,self.mrid) )
        else:
            return self.lst_flatten( self.dview.apply_async(f,params,self.mrid) )

    def report(self,label_or_did,**kwargs):
        self.local_ripl.report(label_or_did,**kwargs)
        @interactive
        def f(label_or_did,mrid,**kwargs):
            return [ripl.report(label_or_did,**kwargs) for ripl in mripls[mrid]]
        if self.lite:
            @interactive
            def f(label_or_did,mrid,**kwargs):
                out = [ripl.report(label_or_did,**kwargs) for ripl in mripls[mrid]]
                try:
                    pickle.dumps(out)
                    return out
                except:
                    return [None for ripl in mripls[mrid] ]
        return self.lst_flatten( self.dview.apply(f,label_or_did,self.mrid, **kwargs) )

    def forget(self,label_or_did):
        self.local_ripl.forget(label_or_did)
        @interactive
        def f(label_or_did,mrid):
            return [ripl.forget(label_or_did) for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f,label_or_did,self.mrid) )

    def execute_program(self,  program_string, params=None):
        self.local_ripl.execute_program( program_string, params )
        @interactive
        def f( program_string, params, mrid):
            return  [ripl.execute_program( program_string,params) for ripl in mripls[mrid]]
            
        if self.lite:    
            @interactive
            def f( program_string, params, mrid):
                out = [ripl.execute_program( program_string,params) for ripl in mripls[mrid]]
                try:
                    pickle.dumps(out)
                    return out
                except:
                    return [None for ripl in mripls[mrid] ]
        return self.lst_flatten( self.dview.apply(f, program_string, params,self.mrid) )

    def get_global_logscore(self):
        self.local_ripl.get_global_logscore()
        @interactive
        def f(mrid):
            return [ripl.get_global_logscore() for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f,self.mrid) )

    def sample(self,exp,type=False):
        
        self.local_ripl.sample(exp,type)
        @interactive
        def f(exp,type,mrid):
               return [ripl.sample(exp,type) for ripl in mripls[mrid] ]
               
        if self.lite:
            @interactive
            def f(exp,type,mrid):
                out = [ripl.sample(exp,type) for ripl in mripls[mrid] ]
                try:
                    pickle.dumps(out)
                    return out
                except:
                    return [None for ripl in mripls[mrid] ]
        return self.lst_flatten( self.dview.apply(f,exp,type,self.mrid) )

    def list_directives(self,type=False):

        self.local_ripl.list_directives(type)
        @interactive
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
            @interactive
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
        @interactive
        def get_info(mrid):
            import os; pid=os.getpid()
            
            return [ {'pid':pid, 'index':i, 'seed':seeds_lists[mrid][i],
                      'ripl':str(ripl)  }  for i,ripl in enumerate( mripls[mrid] ) ]
        self.ripls_location = self.lst_flatten( self.dview.apply(get_info,self.mrid) )
        self.no_ripls = len(self.ripls_location)
        self.seeds = [ripl['seed'] for ripl in self.ripls_location]

        
    def remove_ripls(self,no_rm_ripls):
        'map over the engines to remove a ripl if an engine has >1'
        no_removed = 0

        @interactive
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

    
    def snapshot(self,did_labels_list=[], plot=False, scatter=False, logscore=False):
        '''report the value of a list of variables (input using labels or dids)
        across the ripls and optionally plot as histograms or scatter plots'''
        
        if not(isinstance(did_labels_list,list)):
            did_labels_list = [did_labels_list] 
        values = { did_label:self.report(did_label) for did_label in did_labels_list}
        
        if logscore: values['global_logscore']= self.get_global_logscore()
        
        out = {'values':values,
               'total_transitions':self.total_transitions,
               'ripls_info': self.ripls_location }

        if plot: out['figs'] = self.plot(out,scatter=scatter)

        return out


    def type_list(self,lst):
        'find the type of a list of values, if there is a single type'
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

        
    def plot(self,snapshot,scatter=False):
        '''Takes input from snapshot, checks type of values and plots accordingly.
        Plots are inlined on IPNB and output as figure objects.'''
        
        figs = []
        values = snapshot['values']
        no_trans = snapshot['total_transitions']
        no_ripls = self.no_ripls
        
        for label,vals in values.items():

            var_type = self.type_list(vals)
            
            if var_type =='float':
                fig,ax = plt.subplots(nrows=1,ncols=2,sharex=True,figsize=(8,3.5))
                xr = np.linspace(min(vals),max(vals),400)
                ax[0].plot(xr,gaussian_kde(vals)(xr))
                ax[0].set_xlim([min(vals),max(vals)])
                ax[0].set_title('GKDE: %s (transitions: %i, ripls: %i)' % (str(label), no_trans, no_ripls) )

                ax[1].hist(vals)
                ax[1].set_title('Hist: %s (transitions: %i, ripls: %i)' % (str(label), no_trans, no_ripls) )
                [a.set_xlabel('Var %s' % str(label)) for a in ax]
            
            elif var_type =='int':
                fig,ax = plt.subplots()
                ax.hist(vals)
                ax.set_xlabel = 'Variable %s' % str(label)
                ax.set_title('Hist: %s (transitions: %i, ripls: %i)' % (str(label), no_trans, no_ripls) )
                
            elif var_type =='bool':
                ax.hist(vals)
            elif var_type =='string':
                pass
                
            
            else:
                print 'cant plot this type of data' ##FIXME, shouldnt add fig to figs
            fig.tight_layout()
            figs.append(fig)

            
        if scatter:
            label0,vals0 = values.items()[0]
            label1,vals1 = values.items()[1]
            fig, ax  = plt.subplots(figsize=(5,3.5))
            ax.scatter(vals0,vals1)
            ax.set_xlabel(label0); ax.set_ylabel(label1)
            ax.set_title('%s vs. %s (transitions: %i, ripls: %i)' % (str(label0),str(label1),
                                                                    no_trans, no_ripls) )
            figs.append(fig)
        
        return figs


    def probes(self,did_label='',logscore=False,no_transitions=10,no_probes=2,plot_hist=None,plot_kde=None,plot_series=None):
        ## FIXME, should take a list of labels (like snapshot) and plot accordingly.
        '''Run infer directive on ripls and record snapshots at a series of
        probe points. Optionally produce plots of probe points and a time-series
        plot.'''
        
        label = '' if logscore else did_label
        start = self.total_transitions
        probes = map(int,np.round( np.linspace(0,no_transitions,no_probes) ) )

        out = {'label':label, 'transition_limits':(start,start+no_transitions),
                  'probes':probes, 'series':[], 'snapshots':[], }
        

        # initialize list of snapshots and series FIXME (once logscore interface fixed, share code)
        if not(logscore):
            snapshots = [  self.snapshot( did_labels_list = [label], plot=False, scatter=False, logscore=False ), ]
            series = [snapshots[-1]['values'][label], ]

            for i in range(len(probes[:-1])):
                self.infer(probes[i+1]-probes[i])
                snapshots.append( self.snapshot( did_labels_list = [label], plot=False, scatter=False, logscore=False ) )
                series.append( snapshots[-1]['values'][label] )

        else:
            snapshots = [  self.snapshot( did_labels_list = [], plot=False, scatter=False, logscore=True ), ]
            series = [snapshots[-1]['values']['global_logscore'], ] 

            for i in range(len(probes[:-1])):
                self.infer(probes[i+1]-probes[i])
                snapshots.append( self.snapshot( did_labels_list = [], plot=False, scatter=False, logscore=True ) )
                series.append( snapshots[-1]['values']['global_logscore'] )


        out['series'] = series; out['snapshots'] = snapshots


        # plotting
        
        if plot_hist or plot_kde:  ##FIXME: have better interface
            xmin = min([min(shot) for shot in series])
            xmax = max([max(shot) for shot in series])
            xr = np.linspace(xmin,xmax,400)
            fig,ax = plt.subplots(ncols=no_probes,sharex=True,figsize=(10,5))
            
            for i in range(no_probes):
                ax[i].hist(series[i],bins=12)
                ax[i].set_xlim([xmin,xmax])
                t = 'Hist %s: start %i, probe %i/%i' % (str(label),
                                                               start,probes[i],
                                                               no_transitions)
                ax[i].set_title(t) 

            fig.tight_layout()
            out['hist_figs'] = fig


        if plot_kde:
            xmin = min([min(shot) for shot in series])
            xmax = max([max(shot) for shot in series])
            xr = np.linspace(xmin,xmax,400)
            kdfig,kdax = plt.subplots(ncols=no_probes,sharex=True,figsize=(10,5))

            for i in range(no_probes):
                kdax[i].plot(xr,gaussian_kde(series[i])(xr))
                ax[i].set_xlim([xmin,xmax])
                t = 'GKDE %s: start %i, probe %i/%i' % (str(label),
                                                                           start,probes[i],
                                                                           no_transitions)
                kdax[i].set_title(t)

            kdfig.tight_layout()
            out['kde_figs'] = kdfig


        if plot_series:
            fig,ax = plt.subplots(figsize=(5,3.5))
            for ripl in range(self.no_ripls):
                vals = [shot[ripl] for shot in series]
                ax.plot(probes,vals,label='R'+str(ripl))

            t = '%s: start %i, probes at %s' % (str(label),start,str(probes))
            ax.set_title(t)
            out['timeseries_fig'] = fig
           

        return out
    





## Magic functions defined on MRipl objects 


# Utility functions for the %mr_map cell magic

def lst_flatten(l): return [el for subl in l for el in subl]

def mk_map_proc_string(mripl_name,mrid,proc_name):
    return 'results[-1] = [%s(ripl) for ripl in mripls[%i]] ' % ( proc_name, mrid)
    
add_results_list_string = '''
try: results.append([])
except: results=[ [], ]'''


def mr_map(line, cell):
    '''cell magic allows mapping of functions across all ripls in an MRipl.
    syntax: %%mr_map mripl_name proc_name [store_variable_name, local_ripl] '''
    ## FIXME:think about the use of %px, which will map code
    # across whichever is the active dview on engines. If someone is running
    # multiple sets of engines (e.g. separated into multiple clients or one client
    # separated into multiple views) we'll need to be wary of px mapping to 
    # wrong set of engines. (Could let the dview come from the mripl - so 
    # no extra input argument needed).
    ip = get_ipython()
    #ip.run_cell_magic("px","","%pylab inline") #--no-import-all;%pylab inline") # not sure if this is needed or works
    
    assert len(str(line).split()) >= 2, 'Error. Syntax: %%mr_map mripl_name proc_name [optional: store_variable_name] '
    # get inputs
    proc_name = str(line).split()[1]
    mripl_name =  str(line).split()[0]
    mripl = eval(mripl_name,globals(),ip.user_ns) ## FIXME ensure this works
    mrid = mripl.mrid

    # optionally update the local_ripl (for debugging), must include var_name
    if len(str(line).split()) > 3:
        ip.run_cell(cell) 
        eval( '%s( %s.local_ripl )' % (proc_name,mripl_name),globals(),ip.user_ns)

    # execute cell input across engines to define function
    ip.run_cell_magic("px", '', cell)  
    mripl.dview.execute(add_results_list_string)    

    map_proc_string = mk_map_proc_string(mripl_name,mrid,proc_name)
    mripl.dview.execute(map_proc_string)  # execute the proc across all ripls
    
    outputs_by_ripl = lst_flatten( mripl.dview.apply( interactive(lambda: results[-1])) ) # pull the result of map_proc
    
    ip.run_cell_magic("px",'','pass;') #'plt.show()') # display any figs inline

    out_dict = {'info':{'mripl':mripl_name,'proc':proc_name}, 'out':outputs_by_ripl }
    
    # optionally store in user_ns under input var_name
    if len(str(line).split()) > 2: 
        var_name = str(line).split()[2]
        ip.push({ var_name: out_dict } )
        print '%s = ' % var_name

    return out_dict



# Non-magic version of the magic above (callable from normal Python script)
# Takes an actual mripl and proc as inputs.
def mr_map_nomagic(mripl,proc):
    'Push procedure into engine namespaces. Use execute to map across ripls.'
    proc_name = 'user_proc_' + str( abs(hash(proc)) )
    mripl.dview.push( { proc_name: interactive(proc)} )
    #mripl.dview.execute(set_plotting_string) # matplotlib, inlining

    mripl.dview.execute('print %s' % proc_name)
    mripl.dview.execute( 'results_%s =  [ %s(ripl) for ripl in mripls[%i] ] ' % (proc_name, proc_name, mripl.mrid) )

    ## FIXME: should this be the same as the magic?
    try: # if running ipy, try to plot any figures from the ripls
        ip=get_ipython()
        ip.run_cell_magic("px",'','pass') # display any figs inline
    except:
        pass

    outputs_by_ripl = lst_flatten( mripl.dview['results_%s' % proc_name] )
    # could also pass the procedure out
    out_dict = {'info':{'mripl':mripl.name_mrid,'proc':proc_name}, 'out':outputs_by_ripl }
    
    return out_dict



## Register the cell magic for IPython use
try:
    ip = get_ipython()
    ip.register_magic_function(mr_map, "cell")    
except:
    print 'no ipython'





## Use examples: to be moved to dedicated example scripts

def sp(no_ripls=2):    
    v = MRipl(no_ripls,lite
=True)
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




prog2='''

[assume nps (list (quote bob) (quote time) (quote space) (quote truth) (quote alice) (quote fate) (quote man) (quote beast) (quote nature) (quote he) (quote she) (quote cynthia) (quote zeus) ) ]
[assume np (lambda () (lookup nps (uniform_discrete 0 (len nps)) ) ) ]
[assume uni_simplex (lambda (n) (map_list (lambda (x) (div 1 n)) (zeros n) ) ) ]
[assume np2 (lambda () (lookup nps (categorical (simplex (uni_simplex (len nps) ) ) ) ) ) ]
[assume npz (repeat np 3) ]
[assume alpha (uniform_continuous .9 1)]
[assume crp (make_crp alpha) ]
[assume z (mem (lambda (i) (crp) ) ) ]
[assume s (pair (np) (vp) ) ]
[assume ptype (mem (lambda (z) (s))) ]
[assume noise (lambda (p) (if (flip .1) 
                                (pair (first p) (pair (rest p) (rest p) ) )
                                (if (flip .2) 
                                   (pair (first p) (pair (adv) (rest p) ) ) 
                                   p ) ) ) ]
[assume x (mem (lambda (i) (noise (ptype (z i) ) ) ) )]'''










        

