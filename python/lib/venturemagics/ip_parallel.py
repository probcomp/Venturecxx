from IPython.parallel import Client
from IPython.parallel.util import interactive
from venture.shortcuts import make_puma_church_prime_ripl
from venture.shortcuts import make_lite_church_prime_ripl
import numpy as np
import matplotlib.pylab as plt
from scipy.stats import kde
gaussian_kde = kde.gaussian_kde
import subprocess,time,pickle
make_church_prime_ripl = make_puma_church_prime_ripl
mk_l_ripl = make_lite_church_prime_ripl
mk_p_ripl = make_puma_church_prime_ripl

### IPython Parallel Magics


# Utility functions for working with ipcluster and mripl

def erase_initialize_mripls(client=None,no_erase=False):
    '''Clear engine namespaces and initialize with mripls list. Optionally specify
    a pre-existing client object. With "no_erase", only clear and initialize if
    mripls list and counter are not present in engines.'''
    
    if not client: client=Client(); print "Created new Client"
    if no_erase:
        try: # mripl vars already present: return client object
            client[:]['no_mripls']
        except:
            client[:].execute('mripls=[]; no_mripls=0')
        return client
    else:
        client.clear()
        print 'Cleared engine namespaces and created "mripls"'
        client[:].execute('mripls=[]; no_mripls=0')
        return client
    
def start_engines(no_engines,sleeptime=10):
    start = subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines,'&'])
    time.sleep(sleeptime)
   
def stop_engines(): 
    stop=subprocess.Popen(['ipcluster', 'stop'])
    stop.wait()


def create_new_global_client():
    '''Create new client and dview on it, possibly after closing old one.
    On creating new client, initialize mripls.'''
    try:
        global global_client_for_mripls
        if global_client_for_mripls: global_client_for_mripls.close()
        global_client_for_mripls=Client()
        erase_initialize_mripls()
    except:
        pass
        

### Functions needed for the MRipl Class (could be added to scope of the class definition)

# functions used by engines (and imported when constructing an mripl)
def backend_filter(backend,out):
    if backend=='puma':
        return out
    else:
        return mk_picklable(out)

def mk_picklable(out_lst):
    'if list is unpicklable, cast elements as strings' 
    try:
        pickle.dumps(out_lst)
        return out_lst
    except:
        return map(str,out_lst)

# functions that copy ripls by batch-loading directives that are constructed from directives_list
@interactive
def build_exp(exp):
    'Take expression from directive_list and build the Lisp string'
    if type(exp)==str:
        return exp
    elif type(exp)==dict:
        return str(exp['value'])
    else:
        return '('+ ' '.join(map(build_exp,exp)) + ')'

@interactive
def run_py_directive(ripl,d):
    # FIXME removes labels
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


## MRIPL CLASS


class MRipl2():
    
    def __init__(self,no_ripls,backend='puma',no_local_ripls=1,output='remote',local_mode=False,
                 seeds=None,verbose=False,client=None):
        'seeds={"local":lst_seeds,"remote":lst_seeds}'
        
        self.backend = backend
        assert output in ['remote','local','both']
        self.output = output   
        self.local_mode = local_mode 
        self.total_transitions = 0
        self.verbose = verbose

# initialize local ripls
        assert no_local_ripls > 0
        self.no_local_ripls=no_local_ripls
        self.local_seeds = range(self.no_local_ripls) if not seeds else seeds['local']  # seeds deterministic for reproducibility
        if self.backend=='puma':
            self.local_ripls = [make_puma_church_prime_ripl() for i in range(self.no_local_ripls)]
        else:
            self.local_ripls = [make_lite_church_prime_ripl() for i in range(self.no_local_ripls)]

        [v.set_seed(i) for (v,i) in zip(self.local_ripls,self.local_seeds) ]
        if self.local_mode: return

        ## initialize remote ripls
        self.cli = Client(); self.dview=self.cli[:]
        try:
            self.dview['no_mripls']
        except:
            self.dview.execute('mripls=[]; no_mripls=0')
            print 'Created new "mripls" list'

        self.no_engines = len(self.cli.ids)
        self.no_ripls_per_engine = int(np.ceil(no_ripls/float(self.no_engines)))
        self.no_ripls = self.no_engines * self.no_ripls_per_engine 
        if seeds: assert  len(seeds['local'])==no_local_ripls and len(seeds['remote'])==no_ripls
        self.seeds = range(self.no_ripls) if not seeds else seeds['remote']
        
        # seed are deterministic by default. we reinstate original seeds on CLEAR
        self.dview = self.cli[:]
        self.dview.block = True   # consider again async for infer
        
        # Imports for remote ripls
        self.dview.execute('from venture.venturemagics.ip_parallel import *') # FIXME namespace issues
        self.dview.execute('%pylab inline --no-import-all')
        
        def p_getpids(): import os; return os.getpid()
        self.pids = self.dview.apply(p_getpids)

        self.mrid = self.dview.pull('no_mripls')[0] # id is index into mripls list
        self.dview.push({'no_mripls':self.mrid+1})

        
        # function that creates ripls, using ripls_per_engine attribute we send to engines
        @interactive
        def make_mripl_proc(no_ripls_per_engine):
            k=no_ripls_per_engine
            mripls.append({'lite':[make_lite_church_prime_ripl() for i in range(k)],
                           'puma':[make_puma_church_prime_ripl() for i in range(k)],
                           'seeds':[]})
            
        self.dview.apply(make_mripl_proc,self.no_ripls_per_engine)
         
        @interactive
        def set_engine_seeds(mrid,seeds_for_engine):
            mripl=mripls[mrid]
            mripl['seeds'] = seeds_for_engine
            for backend in ['lite','puma']:
                ripls = mripl[backend]
                [ripl.set_seed(mripl['seeds'][i]) for i,ripl in enumerate(ripls)]

        # divide seeds between engines and then set them across ripls in order
        for i in range(self.no_engines):
            engine_view = self.cli[i]
            start = i*self.no_ripls_per_engine
            seeds_for_engine = self.seeds[start:start+self.no_ripls_per_engine]
            engine_view.apply(set_engine_seeds,self.mrid,seeds_for_engine)
        
        # invariant
        @interactive
        def get_seeds(mrid): return mripls[mrid]['seeds']
        assert self.seeds==self.lst_flatten(self.dview.apply(get_seeds,self.mrid))
    
        # these should overwrite the * import of ip_parallel (we could also alter names)
        #self.dview.push(copy_ripl_dict)
        
        if self.verbose: print self.ripls_info()

 
    def __del__(self):
        if not self.local_mode:
            print '__del__ is closing client'
            self.cli.close()
    
    def lst_flatten(self,l): return [el for subl in l for el in subl]

 

    def switch_backend(self,backend):
        'Clears ripls for new backend and resets transition count'
        if backend==self.backend: return None
        self.backend = backend
        self.total_transitions = 0
        
        ## FIXME: because we use local_ripl[0] to get directives, we are required
        # to always have a local_ripl with identical directives
        di_string_lst = [directive_to_string(di) for di in self.local_ripls[0].list_directives() ]
        if not(di_string_lst):
            return None
        else:
            di_string = '\n'.join(di_string_lst)
        if self.verbose: print di_string
        
        # CLEAR ripls: otherwise when we switch back to a backend
        # we would redefine some variables
        @interactive
        def send_ripls_di_string(mrid,backend,di_string):
            mripl=mripls[mrid]
            [r.clear() for r in mripl[backend]]
            [r.execute_program(di_string) for r in mripl[backend]]

        self.dview.apply(send_ripls_di_string,self.mrid,self.backend,di_string)


    def output_mode(self,local,remote):
        if self.output=='local':
            return local
        elif self.output=='remote':
            return remote
        else:
            return (local,remote)


    def mr_apply(self,local_out,f,*args,**kwargs):
        if self.local_mode: return local_out

        # all remote apply's have to pick a mrid and backend
        remote_out = self.lst_flatten( self.dview.apply(f,self.mrid,self.backend,*args,**kwargs) )        
        return self.output_mode(local_out,remote_out)
        

    def clear(self):
        self.total_transitions = 0
        if self.verbose: print 'CLEAR: mripl.total_transitions=0 and seeds reset'
        local_out = [r.clear() for r in self.local_ripls]
        if self.local_mode:
            self.reset_seeds()
            return local_out

        @interactive
        def f(mrid,backend):
            return [r.clear() for r in mripls[mrid][backend]]
        
        apply_out=self.mr_apply(local_out,f)
        self.reset_seeds() # otherwise all seeds the same
        return apply_out
        

    def reset_seeds(self):
        'Assumes that set_seed has no output'
        [r.set_seed(seed) for r,seed in zip(self.local_ripls,self.local_seeds)]
        if self.local_mode: return

        @interactive
        def f(mrid,backend):
            seeds=mripls[mrid]['seeds']
            [r.set_seed(seed) for r,seed in zip(mripls[mrid][backend],seeds)]
        return self.dview.apply(f,self.mrid,self.backend) 


## FIXME: careful about shadowing kword args correctly
            
    def assume(self,sym,exp,**kwargs):
        local_out = [r.assume(sym,exp,**kwargs) for r in self.local_ripls]
        
        @interactive
        def f(mrid,backend,sym,exp,**kwargs):
            mripl=mripls[mrid]
            out = [r.assume(sym,exp,**kwargs) for r in mripl[backend]]
            return backend_filter(backend,out)

        return self.mr_apply(local_out,f,sym,exp,**kwargs)
        


    def observe(self,exp,val,label=None):
        local_out = [r.observe(exp,val,label=label) for r in self.local_ripls]
        
        @interactive
        def f(mrid,backend,exp,val,label=None):
            mripl=mripls[mrid]
            out = [r.observe(exp,val,label) for r in mripl[backend]]
            return backend_filter(backend,out)

        return self.mr_apply(local_out,f,exp,val,label=label)


    def predict(self,exp,label=None,type=False):
        local_out = [r.predict(exp,label=label,type=type) for r in self.local_ripls]
        
        @interactive
        def f(mrid,backend,exp,label=None,type=False):
            mripl=mripls[mrid]
            out = [r.predict(exp,label=label,type=type) for r in mripl[backend]]
            return backend_filter(backend,out)

        return self.mr_apply(local_out,f,exp,label=label,type=type)


    def sample(self,exp,type=False):
        local_out = [r.sample(exp,type=type) for r in self.local_ripls]
        
        @interactive
        def f(mrid,backend,exp,type=False):
            mripl=mripls[mrid]
            out = [r.sample(exp,type=type) for r in mripl[backend]]
            return backend_filter(backend,out)

        return self.mr_apply(local_out,f,exp,type=type)


    def infer(self,params,block=True):
        if isinstance(params,int):
            self.total_transitions += params
            if self.verbose: print 'total transitions: ',self.no_transitions
        elif 'transitions' in params:
            self.total_transitions += params['transitions']
            if self.verbose: print 'total transitions: ',self.no_transitions
        ##FIXME: add cases for inference programming

        local_out = [r.infer(params) for r in self.local_ripls]
        if self.local_mode: return local_out

        @interactive
        def f(mrid,backend,params):
            return [r.infer(params) for r in mripls[mrid][backend] ]
        
        if block:
            remote_out= self.lst_flatten( self.dview.apply_sync(f,self.mrid,self.backend,params) )
        else:
            remote_out = self.lst_flatten( self.dview.apply_async(f,self.mrid,self.backend,params) )


        return self.output_mode(local_out,remote_out)
        
        

    def report(self,label_or_did,**kwargs):
        local_out = [r.report(label_or_did,**kwargs) for r in self.local_ripls]
        
        @interactive
        def f(mrid,backend,label_or_did,**kwargs):
            mripl=mripls[mrid]
            out = [r.report(label_or_did,**kwargs) for r in mripl[backend]]
            return backend_filter(backend,out)

        return self.mr_apply(local_out,f,label_or_did,**kwargs)


    def forget(self,label_or_did):
        local_out = [r.forget(label_or_did) for r in self.local_ripls]
        @interactive
        def f(mrid,backend,label_or_did):
            return [r.forget(label_or_did) for r in mripls[mrid][backend]]
            
        return self.mr_apply(local_out,f,label_or_did)


    def continuous_inference_status(self):
        self.local_ripl.continuous_inference_status()
        @interactive
        def f(mrid):
            return [ripl.continuous_inference_status() for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f, self.mrid) )

    def start_continuous_inference(self, params=None):
        self.local_ripl.start_continuous_inference(params)
        @interactive
        def f(params, mrid):
            return [ripl.start_continuous_inference(params) for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f, params, self.mrid) )

    def stop_continuous_inference(self):
        self.local_ripl.stop_continuous_inference()
        @interactive
        def f(mrid):
            return [ripl.stop_continuous_inference() for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f, self.mrid) )


    def execute_program(self,program_string,params=None):
        
        local_out=[r.execute_program(program_string, params) for r in self.local_ripls]

        @interactive
        def f(mrid,backend,program_string, params ):
            mripl=mripls[mrid]
            out = [r.execute_program(program_string, params) for r in mripl[backend]]
            return backend_filter(backend,out)
  
        out_execute= self.mr_apply(local_out,f,program_string,params)
        
        if '[clear]' in program_string.lower():
            self.total_transitions = 0
            print 'Total transitions set to 0'
            self.reset_seeds()
        
        return out_execute


    def get_global_logscore(self):
        local_out = [r.get_global_logscore() for r in self.local_ripls]

        @interactive
        def f(mrid,backend):
            return [r.get_global_logscore() for r in mripls[mrid][backend]]

        return self.mr_apply(local_out,f)


    def list_directives(self,type=False): return self.local_ripls[0].list_directives(type=type) 

               
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
    
    
    
    def ripls_info(self):
        local_out = [(seed,str(r)) for seed,r in zip(self.local_seeds,self.local_ripls) ]
        if self.local_mode: return local_out
        
        @interactive
        def get_info(mrid,backend):
            import os; pid=os.getpid()
            mripl=mripls[mrid]
            seeds = mripl['seeds'] # FIXME add get_seed
            ripl_prints = [str(r) for r in mripl[backend]]
            return [(pid,seed,ripl_print) for seed,ripl_print in zip(seeds,ripl_prints) ]
                   
        remote_out = self.lst_flatten( self.dview.apply(get_info,self.mrid,self.backend) )
        
        return self.output_mode(local_out,remote_out)


        
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

    

    def snapshot(self,exp_list=[],did_labels_list=[],
                 plot=False, scatter=False, plot_range=None,
                 plot_past_values=[],
                 sample_populations=None, repeat=None,
                 predict=True,logscore=False):
                 
        '''Input: lists of dids_labels and expressions (evaled in order)
           Output: values from each ripl, (optional) plots.''' 
        
        # sample_populations, repeat need non-det exps (not thunks)
        # sample pop needs a pair
        # plot past vals takes list of snapshot outputs and plots first var in values
        # (so exp_list and did list could be empty)
        
        if isinstance(did_labels_list,(int,str)): did_labels_list = [did_labels_list]
        if isinstance(exp_list,str): exp_list = [exp_list]

        if plot_range: # = (xrange[,yrange])
            pr=plot_range; l=len(pr)
            assert (l==2 and len(pr[0])==len(pr[1])==2) or (l==1 and len(pr[0])==2)
        
        out = {'values':{}, 'total_transitions':self.total_transitions,
                    'ripls_info': self.ripls_info() }


        # special options: (return before basic snapshot)
        if sample_populations:
            return self.sample_populations(exp_list,out,sample_populations,plot=plot,
                                           plot_range=plot_range)
        elif repeat: 
            no_groups = self.no_local_ripls if self.output=='local' else self.no_ripls
            return self.sample_populations(exp_list, out, (no_groups,repeat),
                                           flatten=True, plot=plot,plot_range=plot_range)

            
        # basic snapshot
        out['values'] = { did_label:self.report(did_label) for did_label in did_labels_list}

        if not(predict):
            v={ exp:self.sample(exp) for exp in exp_list }
        else:
            v={ exp: self.predict(exp,label='snapvals_%i' %i) for i,exp in enumerate(exp_list)}
            [self.forget('snapvals_%i'%i ) for i,exp in enumerate(exp_list)]

        out['values'].update(v)

        
        # special options that use basic snapshot
        if plot_past_values:
            return self.plot_past_values(exp_list, out, plot_past_values,
                                         plot_range=plot_range)

        # logscore current must go after plot_past_values to avoid errors
        if logscore: out['values']['global_logscore']= self.get_global_logscore()
        
        if plot or scatter:
            out['figs'] = self.plot(out,scatter=scatter,plot_range=plot_range)


        return out

    


    def sample_populations(self,exp_list,out,groups_popsize,flatten=False,plot=False,plot_range=None):
        # PLAN: think about non-cts case of sample populations. think about doing
        # sample populations for correlations

        assert len(exp_list)==1
        exp = exp_list[0]
        no_groups,pop_size = groups_popsize

        def pred_repeat_forget(r,exp,pop_size):
            vals=[r.predict(exp,label='snapsp_%i'%j) for j in range(pop_size)]
            [r.forget('snapsp_%i'%j) for j in range(pop_size)]
            return vals

        mrmap_values = mr_apply_proc(self, no_groups,
                                pred_repeat_forget, exp, pop_size)

        if flatten: mrmap_values = self.lst_flatten(mrmap_values)

        out['values'][exp]=mrmap_values

        if plot and flatten: # Predictive
            fig,ax=plt.subplots(figsize=(6,3))
            ax.hist(mrmap_values, bins=20,alpha=.8, normed=True, color='m')
            xr=np.linspace(min(mrmap_values),max(mrmap_values),50)
            ax.plot(xr,gaussian_kde(mrmap_values)(xr), c='black', lw=2,label='GKDE')
            ax.set_title('Predictive: %s (no_ripls= %i, repeats= %i)' % (exp,no_groups,pop_size))
            ax.legend()
            if plot_range:
                ax.set_xlim(plot_range[0])
                if len(plot_range)==2: ax.set_ylim(plot_range[1])
            out['figs']=fig
            return out

        if plot and not flatten: # Random populations
            mrmap_values = np.array(mrmap_values).T
            fig,ax=plt.subplots(1,2,figsize=(14,4),sharex=True,sharey=False)
            all_vals=self.lst_flatten(mrmap_values)
            xr=np.linspace(min(all_vals),max(all_vals),80)

            hist_counts = []
            for col in range(no_groups):
                hist_out = ax[0].hist(mrmap_values[:,col],
                                      bins=20, alpha=.4, normed=False, histtype='stepfilled')
                hist_counts.append( hist_out[0])
                ax[1].plot(xr,gaussian_kde(mrmap_values[:,col])(xr))

            max_hist_count = np.max(hist_counts)
            ax[0].set_ylim( (0, 1.1*max_hist_count) )
            
            ax[0].set_title('Sample populations: %s (population size= %i)' % (exp,pop_size))
            ax[1].set_title('GKDE: %s (population size= %i)' % (exp,pop_size))

            if plot_range:
                [ax[i].set_xlim(plot_range[0]) for i in range[0,1]]
                if len(plot_range)==2: ax[0].set_ylim(plot_range[1])
            out['figs']=fig

            return out


    def plot_past_values(self, exp_list, out, past_values_list,plot_range):
        if exp_list:
            current_vals = out['values'].values()[0] # note conflict with logscore
            exp_name  = exp_list[0]
        else:
            curent_vals = None
            exp_name = past_values_list[0]['values'].keys()[0]

        assert isinstance(past_values_list,(list,tuple))

        list_vals = [ past_out['values'].values()[0] for past_out in past_values_list]
        if current_vals: list_vals.append( current_vals ) 

        fig,ax=plt.subplots(1,2,figsize=(14,3.5),sharex=True)
        all_vals=self.lst_flatten(list_vals)
        xr=np.linspace(min(all_vals),max(all_vals),50)

        for count,past_vals in enumerate(list_vals):
            label='Pr [0]' if count==0 else 'Po [%i]'%count
            alpha = .9 - .2*(len(list_vals) - count )
            ax[0].hist( past_vals, bins=20,alpha=alpha,
                        normed=True,label=label)
            ax[1].plot(xr,gaussian_kde(past_vals)(xr),
                       alpha=alpha, label=label)

        [ ax[i].legend(loc='upper left',ncol=len(list_vals)) for i in range(2)]
        ax[0].set_title('Past values hist: %s (ripls= %i)' % (exp_name,self.no_ripls) )
        ax[1].set_title('GKDE: %s (ripls= %i)' % (exp_name,self.no_ripls) )

        if plot_range:
            [ax[i].set_xlim(plot_range[0]) for i in range(2)]
            if len(plot_range)==2: ax[0].set_ylim(plot_range[1])

        out['figs'] = fig
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

        
    def plot(self,snapshot,scatter=False,plot_range=None):
        '''Takes input from snapshot, checks type of values and plots accordingly.
        Plots are inlined on IPNB and output as figure objects.'''
        

        def draw_hist(vals,label,ax,plot_range=None):
            ax.hist(vals)
            ax.set_title('Hist: %s (transitions: %i, ripls: %i)' % (str(label), no_trans, no_ripls) )
            ax.set_xlabel('Exp: %s' % str(label))
            if plot_range:
                ax.set_xlim(plot_range[0])
                if len(plot_range)==2: ax.set_ylim(plot_range[1])

        def draw_kde(vals,label,ax,plot_range=None):
            xr = np.linspace(min(vals),max(vals),50) 
            ax.plot(xr,gaussian_kde(vals)(xr))
            ax.set_title('GKDE: %s (transitions: %i, ripls: %i)' % (str(label), no_trans, no_ripls) )
            ax.set_xlabel('Exp: %s' % str(label))
            if plot_range:
                ax.set_xlim(plot_range)                 
                if len(plot_range)==2: ax.set_ylim(plot_range[1])

        
        # setup variables for plot
        figs = []
        values = snapshot['values']
        no_trans = snapshot['total_transitions']
        no_ripls = self.no_ripls if self.output=='remote' else self.no_local_ripls
                
        # loop over label,val from snapshot and plot subplot of kde and hist
        for label,vals in values.items():
            var_type = self.type_list(vals)

            if var_type =='float':
                try:
                    kde=list(gaussian_kde(vals)(np.linspace(min(vals),max(vals),50)))[0]
                except:
                    kde=False
                if kde:
                    fig,ax = plt.subplots(nrows=1,ncols=2,sharex=True,figsize=(9,2))
                    draw_hist(vals,label,ax[0],plot_range=plot_range)
                    draw_kde(vals,label,ax[1],plot_range=plot_range)
                else:
                    fig,ax = plt.subplots(figsize=(4,2))
                    draw_hist(vals,label,ax,plot_range=plot_range)

            elif var_type in 'int':
                fig,ax = plt.subplots()
                draw_hist(vals,label,ax,plot_range=plot_range)

            fig.tight_layout()
            figs.append(fig)

            
        if scatter:
            label0,vals0 = values.items()[0]
            label1,vals1 = values.items()[1]
            fig, ax  = plt.subplots(figsize=(4,2))
            ax.scatter(vals0,vals1)
            ax.set_xlabel(label0); ax.set_ylabel(label1)
            ax.set_title('%s vs. %s (transitions: %i, ripls: %i)' % (str(label0),str(label1),
                                                                    no_trans, no_ripls) )
            figs.append(fig)
        
        return figs









# function for creating a list of ripls for each mripl
make_mripl_string='''
try:
    mripls.append([]); no_mripls += 1; seeds_lists.append([])
except:
    mripls=[ [], ]; no_mripls=1; seeds_lists = [ [], ]'''

@interactive
def make_mripl_func():
    try:
        mripls.append([]); no_mripls += 1; seeds_lists.append([])
    except:
        mripls=[ [], ]; no_mripls=1; seeds_lists = [ [], ]





class MRipl():
    
    def __init__(self,no_ripls,lite=False,verbose=False,client=None,name=None):
        self.lite = lite
        if not self.lite:
            self.local_ripl = make_church_prime_ripl()
        else:
            self.local_ripl = make_lite_church_prime_ripl()
        self.local_ripl.set_seed(0)   # same seed as first remote ripl
        self.no_ripls = no_ripls
        self.seeds = range(self.no_ripls)
        #self.seeds = map(int,(list(np.random.randint(1,10**3,self.no_ripls)))) ##FIXME set np seed in advance for reproduce
        self.total_transitions = 0
        
        self.cli = Client() if not(client) else client # REMOVE
        self.dview = self.cli[:]
        self.dview.block = True
        
        # FIXME if we push anything with same name, the pushed thing should take precedence
        self.dview.execute('from venture.venturemagics.ip_parallel import *')
        
        def p_getpids(): import os; return os.getpid()
        self.pids = self.dview.apply(p_getpids)
      
        if not self.lite:
            self.dview.execute('from venture.shortcuts import make_church_prime_ripl as make_ripl')
        else:
            self.dview.execute('from venture.shortcuts import make_lite_church_prime_ripl as make_ripl')
        
        # import plt for plotting 
        self.dview.execute('import matplotlib.pylab as plt')
        self.dview.execute('import numpy as np')
        self.dview.execute('import pickle')
        self.dview.execute('%pylab inline --no-import-all')
        
        # these should overwrite the * import of ip_parallel (we could also alter names)
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


    def test_assume(self,sym,exp,**kwargs):
        self.local_ripl.assume(sym,exp,**kwargs)
        
        @interactive
        def f(mrid,backend,sym,exp,**kwargs):
            outs =[ [ripl.assume(sym,exp,**kwargs) for ripl in mripls[mrid]] for mripls in backends]
            return outs[0] if backend=='puma' else pickle_safe(outs[1])

        return self.lst_flatten( self.dview.apply(f,self.backend,self_mrid,sym,exp,**kwargs) )
    

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
                    return ['sp' for ripl in mripls[mrid] ]

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
                    return ['sp' for ripl in mripls[mrid] ]
                
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
                    return ['sp' for ripl in mripls[mrid] ]
        
        return self.lst_flatten( self.dview.apply(f,exp,label,type,self.mrid) )

    def infer(self,params,block=True):
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
                    return ['sp' for ripl in mripls[mrid] ]
        return self.lst_flatten( self.dview.apply(f,label_or_did,self.mrid, **kwargs) )

    def forget(self,label_or_did):
        self.local_ripl.forget(label_or_did)
        @interactive
        def f(label_or_did,mrid):
            return [ripl.forget(label_or_did) for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f,label_or_did,self.mrid) )


    def continuous_inference_status(self):
        self.local_ripl.continuous_inference_status()
        @interactive
        def f(mrid):
            return [ripl.continuous_inference_status() for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f, self.mrid) )

    def start_continuous_inference(self, params=None):
        self.local_ripl.start_continuous_inference(params)
        @interactive
        def f(params, mrid):
            return [ripl.start_continuous_inference(params) for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f, params, self.mrid) )

    def stop_continuous_inference(self):
        self.local_ripl.stop_continuous_inference()
        @interactive
        def f(mrid):
            return [ripl.stop_continuous_inference() for ripl in mripls[mrid]]
        return self.lst_flatten( self.dview.apply(f, self.mrid) )


    def execute_program(self,  program_string, params=None):
        
        ## FIXME: [clear] could appear anywhere
        if program_string.split()[0].startswith('[clear]'):
            self.total_transitions = 0
            

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
                    return str(out)
                
        out_execute=if_lst_flatten( self.dview.apply(f, program_string, params,self.mrid) )

        @interactive ## FIXME:pasted from self.clear and should be properly abstracted
        def reset_seeds(mrid):
            ripls=mripls[mrid]; seeds=seeds_lists[mrid]
            [ripls[i].set_seed(seeds[i]) for i in range(len(ripls))]

        out_seeds=self.dview.apply(reset_seeds,self.mrid)
        
        return out_execute


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
                    return ['sp' for ripl in mripls[mrid] ]
        return self.lst_flatten( self.dview.apply(f,exp,type,self.mrid) )


    def list_directives(self,type=False):

        self.local_ripl.list_directives(type)
        @interactive
        def f(type,mrid):
               return [ripl.list_directives(type) for ripl in mripls[mrid] ]
               
        if self.lite:
            @interactive
            def f(type,mrid):
                out = [ripl.list_directives(type) for ripl in mripls[mrid] ]
                try:
                    pickle.dumps(out)
                    return out
                except:


                    return str(out)


        return if_lst_flatten( self.dview.apply(f,type,self.mrid) )
               
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

    
    def snapshot(self,exp_list=[],did_labels_list=[],
                 plot=False, scatter=False, plot_range=None,
                 plot_past_values=[],
                 sample_populations=None, repeat=None,
                 predict=False,logscore=False):
                 
                
        '''Input: lists of dids_labels and expressions.
           Output: values from each ripl, (optional) plots.''' 
        
        
        if not(isinstance(did_labels_list,list)): did_labels_list = [did_labels_list]
        if not(isinstance(exp_list,list)): exp_list = [exp_list]
        
        values = { did_label:self.report(did_label) for did_label in did_labels_list}
        
        if not(predict):
            values.update( { exp:self.sample(exp) for exp in exp_list } )
        else:
            values.update( { exp:self.predict(exp) for exp in exp_list } )
            
        if logscore: values['global_logscore']= self.get_global_logscore()
        
        out = {'values':values,
               'total_transitions':self.total_transitions,
               'ripls_info': self.ripls_location }


        if sample_populations:
            if isinstance(sample_populations,int):
                no_groups,pop_size = sample_populations,100
            else:
                no_groups,pop_size = sample_populations
            exp = exp_list[0]

            
            if not(predict):
                all_ripls = [self.sample(exp) for j in range(pop_size)]
            else:
                all_ripls = [self.predict(exp,label='sp%i'%j) for j in range(pop_size)]
                [self.forget('sp%i'%j) for j in range(pop_size)]
            
            indices = np.random.randint(0,self.no_ripls,no_groups)

            some_ripls= np.array([np.array(samp)[indices] for samp in all_ripls ])
            #p1=some_ripls[:,0] ...
            #some_ripls = [r for count,r in enumerate(all_ripls) if count in indices]
            out['values'][exp] = some_ripls

            if plot:
                fig,ax=plt.subplots(1,2,figsize=(14,4),sharex=True,sharey=False)
                f=self.lst_flatten(some_ripls)
                xr=np.linspace(min(f),max(f),80)
                lim = some_ripls.shape[1]
                for col in range(lim):
                    ax[0].hist(some_ripls[:,col],bins=20,normed=False,histtype='stepfilled')
                    
                    #ax[1].hist(some_ripls[:,col], bins=20,
                     #          histtype='stepfilled',alpha=1-(col/float(lim)) )

                    ax[1].plot(xr,gaussian_kde(some_ripls[:,col])(xr))
                ax[0].set_ylim((0,.66*pop_size))
                ## FIXME: make ylim for ax[0] some sensible thing, like 1.5 times max bar height
                ax[0].set_title('Sample populations: %s (population size= %i)' % (exp,pop_size))
                ax[1].set_title('Sample populations: %s (population size= %i)' % (exp,pop_size))
                out['figs']=fig
                
        if repeat:
            exp=exp_list[0]
            if not(predict):
                r_values = lst_flatten([self.sample(exp) for repeats in range(repeat)])
            else:
                r_values = lst_flatten([self.predict(exp) for repeats in range(repeat)])
            out['values'][exp] = r_values
            if plot:
                fig,ax=plt.subplots(figsize=(5,3))
                ax.hist(r_values,bins=20,normed=True,color='m')
                xr=np.linspace(min(r_values),max(r_values),40)
                ax.plot(xr,gaussian_kde(r_values)(xr),c='black',lw=2)
                ax.set_title('Predictive distribution: %s (repeats= %i)' % (exp,repeat))
                out['figs'] = fig
                                   
                                   

    
            if not(exp_list) and not(did_labels_list):
                no_exp=1; exp_list=['']
            else:
                no_exp=0
            if not isinstance(plot_past_values,list):
                plot_past_values = [plot_past_values]

            list_vals = [ past_out['values'].values()[0] for past_out in plot_past_values]
            if no_exp==0: list_vals.append( out['values'].values()[0] )
            
            fig,ax=plt.subplots(1,2,figsize=(14,3.5),sharex=True)
            f=self.lst_flatten(list_vals)
            xr=np.linspace(min(f),max(f),80)

            
            for count,past_vals in enumerate(list_vals):
                label='Pr [0]' if count==0 else 'Po [%i]'%count
                ax[0].hist( past_vals,bins=20,normed=True,label=label)
                
            for count,past_vals in enumerate(list_vals):
                label='Pr [0]' if count==0 else 'Po [%i]'%count
                ax[1].plot(xr,gaussian_kde(past_vals)(xr), label=label)
                    
            [ ax[i].legend(loc='upper left',ncol=len(list_vals)) for i in range(2)]
            ax[0].set_title('Past values hist: %s (ripls= %i)' % (exp_list[0],self.no_ripls) )
            ax[1].set_title('GKDE: %s (ripls= %i)' % (exp_list[0],self.no_ripls) )
            
            if plot_range:
                [ax[i].set_xlim(plot_range[:2]) for i in range(2)]
                if len(plot_range)>2: ax[0].set_ylim(plot_range[2],plot_range[3])
                        
            
            out['figs'] = fig
            return out
            

        if (plot or scatter) and not(sample_populations) and not(repeat):
            out['figs'] = self.plot(out,plot1d=plot,scatter=scatter,plot_range=plot_range)



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

        
    def plot(self,snapshot,plot1d=True,scatter=False,plot_range=None):
        '''Takes input from snapshot, checks type of values and plots accordingly.
        Plots are inlined on IPNB and output as figure objects.'''
        
        ## list of lists, values as an optional argument
        figs = []
        values = snapshot['values']
        no_trans = snapshot['total_transitions']
        no_ripls = self.no_ripls
        
        if plot1d:
            for label,vals in values.items():
                var_type = self.type_list(vals)

                if var_type =='float':
                    try:
                        kd=gaussian_kde(vals)(np.linspace(min(vals),max(vals),400))
                        kde=1
                    except:
                        kde=0
                    if kde:
                        fig,ax = plt.subplots(nrows=1,ncols=2,sharex=True,figsize=(9,2))

                        xr = np.linspace(min(vals),max(vals),400) 
                        ax[0].plot(xr,gaussian_kde(vals)(xr))
                        ax[0].set_title('GKDE: %s (transitions: %i, ripls: %i)' % (str(label), no_trans, no_ripls) )

                        ax[1].hist(vals)
                        ax[1].set_title('Hist: %s (transitions: %i, ripls: %i)' % (str(label), no_trans, no_ripls) )
                        [a.set_xlabel('Exp: %s' % str(label)) for a in ax]

                        if plot_range:
                            [ax[myax].set_xlim(plot_range) for myax in range(2)]

                    else:
                        fig,ax = plt.subplots(figsize=(4,2))
                        ax.hist(vals)
                        ax.set_title('Hist: %s (transitions: %i, ripls: %i)' % (str(label), no_trans, no_ripls) )
                        ax.set_xlabel('Exp: %s' % str(label))
                        if plot_range:
                            [ax[myax].set_xlim(plot_range) for myax in range(2)]
                        

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
            fig, ax  = plt.subplots(figsize=(4,2))
            ax.scatter(vals0,vals1)
            ax.set_xlabel(label0); ax.set_ylabel(label1)
            ax.set_title('%s vs. %s (transitions: %i, ripls: %i)' % (str(label0),str(label1),
                                                                    no_trans, no_ripls) )
            figs.append(fig)
        
        return figs


    def probes(self,did_label='',exp='',logscore=False,no_transitions=10,no_probes=2,plot_hist=None,plot_kde=None,plot_series=None):
        ## FIXME, should take a list of labels (like snapshot) and plot accordingly.
        '''Input: single did or label, or a single expression, no_transitions, number of points to
        take snapshots and optional plotting. Outputs snapshots and plots.'''
        
        ## FIXME: use expression instead of did_label if both are entered
        if logscore:
            label = ''; did_label=''; exp=''
        elif exp:
            label = exp; did_label=''
        else:
            label = did_label
        
        start = self.total_transitions
        probes = map(int,np.round( np.linspace(0,no_transitions,no_probes) ) )

        out = {'label':label, 'transition_limits':(start,start+no_transitions),
                  'probes':probes, 'series':[], 'snapshots':[], }
        

        # initialize list of snapshots and series. FIXME (once logscore interface fixed, share code)
        if not(logscore):
            snapshots = [  self.snapshot( did_labels_list = [did_label],exp_list=[exp], plot=False, scatter=False, logscore=False ), ]
            series = [snapshots[-1]['values'][label], ]

            for i in range(len(probes[:-1])):
                self.infer(probes[i+1]-probes[i])
                snapshots.append( self.snapshot( did_labels_list = [did_label],exp_list=[exp], plot=False, scatter=False, logscore=False ) )
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

def limit_mk_map_proc_string(mripl_name,mrid,proc_name,max_rips):
    return 'results[-1] = [%s(ripl) for count,ripl in enumerate(mripls[%i]) if count<%i] ' % ( proc_name, mrid,max_rips)
    
add_results_list_string = '''
try: results.append([])
except: results=[ [], ]'''


def mr_map(line, cell):
    '''cell magic allows mapping of functions across all ripls in an MRipl.
    syntax: %%mr_map mripl_name proc_name [store_variable_name, limit, local_ripl] '''
    ## FIXME:think about the use of %px, which will map code
    # across whichever is the active dview on engines. If someone is running
    # multiple sets of engines (e.g. separated into multiple clients or one client
    # separated into multiple views) we'll need to be wary of px mapping to 
    # wrong set of engines. (Could let the dview come from the mripl - so 
    # no extra input argument needed).
    ip = get_ipython()
    
    assert len(str(line).split()) >= 2, 'Error. Syntax: %%mr_map mripl_name proc_name [optional: store_variable_name] '
    # get inputs
    proc_name = str(line).split()[1]
    mripl_name =  str(line).split()[0]
    limit = None
    if len(str(line).split()) > 3:
        try: limit = int(str(line).split()[3])
        except: pass
    mripl = eval(mripl_name,globals(),ip.user_ns) ## FIXME ensure this works
    mrid = mripl.mrid

    # optionally update the local_ripl (for debugging), must include var_name
    if len(str(line).split()) > 4:
        ip.run_cell(cell) 
        eval( '%s( %s.local_ripl )' % (proc_name,mripl_name),globals(),ip.user_ns)


    # execute cell input across engines to define function
    ip.run_cell_magic("px", '', cell)  
    mripl.dview.execute(add_results_list_string)    

    if limit:
        mripl.dview.execute(limit_mk_map_proc_string(mripl_name,mrid,proc_name,limit) )
        
    else:    
        mripl.dview.execute(mk_map_proc_string(mripl_name,mrid,proc_name) )
    
    outputs_by_ripl = lst_flatten( mripl.dview.apply( interactive(lambda: results[-1])) ) # pull the result of map_proc
    
    ip.run_cell_magic("px",'','pass;') #'plt.show()') # display any figs inline

    out_dict = {'info':{'mripl':mripl_name,'proc':proc_name}, 'out':outputs_by_ripl }
    
    # optionally store in user_ns under input var_name
    if len(str(line).split()) > 2: 
        var_name = str(line).split()[2]
        ip.push({ var_name: out_dict } )
        print '%s = ' % var_name

    return out_dict



def mr_apply_proc(mripl,no_ripls,proc,*proc_args,**proc_kwargs):
    '''Push procedure into engine namespaces. Use execute to map across ripls.
    if no_ripls==0 or 'all', then does all'''
    if no_ripls==0 or no_ripls=='all':
        no_ripls = mripl.no_ripls
        no_local_ripls = mripl.no_local_ripls

    local_out=[proc(r,*proc_args,**proc_kwargs) for ind,r in enumerate(mripl.local_ripls) if ind<no_ripls]

    if mripl.local_mode: return local_out


    mripl.dview.push( {'ap_proc':(interactive(proc),
                                proc_args,proc_kwargs)} )

    apply_no_ripls_per_engine = int(np.ceil(no_ripls/float(mripl.no_engines)))
    per_eng = apply_no_ripls_per_engine
    
    s1='apply_out='
    s2='[ap_proc[0](r,*ap_proc[1],**ap_proc[2]) for ind,r in enumerate(mripls[%i]["%s"]) if ind<%i]' % (mripl.mrid,
                                                                                                      mripl.backend,per_eng)
    
    mripl.dview.execute(s1+s2)
    
    try: 
        ip=get_ipython()
        ip.run_cell_magic("px",'','pass') # display any figs inline
    except:
        pass

    remote_out = lst_flatten( mripl.dview['apply_out'] )
    ## FIXME should we slice this to 'no_ripls'?
    return mripl.output_mode(local_out,remote_out)



    # proc_name = 'user_proc_' + str( abs(hash(proc)) )
    # mripl.dview.push( { proc_name: interactive(proc)} )

    # # e.g. ask for 5 ripls, with 4*4=16, we get 5/4->2 ripls per eng
    
    # apply_no_ripls_per_engine = int(np.ceil(no_ripls/float(self.no_engines)))
   
    # per_eng = apply_no_ripls_per_engine
    # p=proc_name; mrid=mripl.mrid; backend=mripl.backend

    # s='out_lst_%s =[%s(r) for ind,r in enumerate(mripls[%i][%s]) if ind<%i]' % (p,p,mrid,backend,per_eng)
    
    
    # try: 
    #     ip=get_ipython()
    #     ip.run_cell_magic("px",'','pass') # display any figs inline
    # except:
    #     pass

    # remote_out = lst_flatten( mripl.dview['out_lst_%s' % proc_name] )
    # return mripl.output_mode(local_out,remote_out)





# Non-magic version of the magic above (callable from normal Python script)
# Takes an actual mripl and proc as inputs.
def mr_map_f(mripl,proc,limit=None):
    'Push procedure into engine namespaces. Use execute to map across ripls.'
    proc_name = 'user_proc_' + str( abs(hash(proc)) )
    mripl.dview.push( { proc_name: interactive(proc)} )
    #mripl.dview.execute(set_plotting_string) # matplotlib, inlining

    mripl.dview.execute('print %s' % proc_name)
    p=proc_name; mrid=mripl.mrid
    if limit:
        s='results_%s =[%s(ripl) for count,ripl in enumerate(mripls[%i]) if count<%i]' % (p,p,mrid,limit)
        mripl.dview.execute(s) 
    else:
        mripl.dview.execute( 'results_%s =  [ %s(ripl) for ripl in mripls[%i] ] ' % (p,p,mrid) )

                             
    ## FIXME: should this be the same as the magic?
    try: # if running ipy, try to plot any figures from the ripls
        ip=get_ipython()
        ip.run_cell_magic("px",'','pass') # display any figs inline
    except:
        pass

    outputs_by_ripl = lst_flatten( mripl.dview['results_%s' % proc_name] )
    
    out_dict = {'info':{'mripl':mripl.name_mrid,'proc':proc_name}, 'out':outputs_by_ripl }
    
    return out_dict


def reset_seeds(mr):
    def hasher(ripl):
        seed = np.mod( abs(int(hash(ripl))), 10**4)
        ripl.set_seed(seed)
        print 'new seed:', seed
        return None
    mr_map_f(mr,hasher)
    

def venture(line, cell):
    mripl_name =  str(line).split()[0]
    mripl = eval(mripl_name,globals(),ip.user_ns)
    out = mripl.execute_program(str(cell))
    
    if isinstance(mripl,MRipl):
        try:
            values = [[d['value']['value'] for d in ripl_out] for ripl_out in out ]
            for i,val in enumerate(values):
                if i<5:
                    print 'Ripl %i of %i: '%(i,mripl.no_ripls), val
                if i==5: print '...'
        except:
            pass
    else:
        try:
            values = [d['value']['value'] for d in out]
            print values
        except:
            pass

    return None  ##FIXME: maybe some values should be output
    

## Register the cell magic for IPython use
try:
    ip = get_ipython()
    ip.register_magic_function(mr_map, "cell")
    ip.register_magic_function(venture, "cell")
except:
    print 'no ipython'



library_string='''
[assume zeros (lambda (n) (if (= n 0) (list) (pair 0 (zeros (minus n 1)))))]
[assume ones (lambda (n) (if (= n 0) (list) (pair 1 (ones (minus n 1)))))]         [assume is_nil (lambda (lst) (= lst (list)) ) ]
[assume map (lambda (f lst) (if (is_nil lst) (list) (pair (f (first lst)) (map f (rest lst))) ) ) ]  
[assume repeat (lambda (th n) (if (= n 0) (list) (pair (th) (repeat th (- n 1) ) ) ) ) ]
[assume srange (lambda (b e s) (if (gte b e) (list) (pair b (srange (+ b s) e s) ) ) ) ]
[assume range (lambda (n) (srange 0 n 1) ) ]
[assume append (lambda (lst x) (if (is_nil lst) (list x) (pair (first lst) (append (rest lst) x) ) ) )]
[assume cat (lambda (xs ys) (if (is_nil ys) xs (cat (append xs (first ys)) (rest ys) ) ) )]
[assume fold (lambda (f l el) (if (is_nil l) el(f (first l) (fold f (rest l) el) ) ) ) ]
[assume suml (lambda (xs) (fold + xs 0) )]
[assume prodl (lambda (xs) (fold * xs 1) ) ]
'''
lite_addendum='''
[assume nil (list)]
'''

def test_ripls(print_lib=False):
    vs=[make_lite_church_prime_ripl(), make_church_prime_ripl()]
    [v.execute_program(library_string) for v in vs]
    vs[0].execute_program(lite_addendum)
    return vs


## Utility functions for working with MRipls

def display_directives(ripl_mripl,instruction='observe'):
    ## FIXME add replace with dict of symbls
    ## FIXME: add did and labels
    v=ripl_mripl
    mr=1  if isinstance(v,MRipl) else 0
    di_list = v.local_ripl.list_directives() if mr else v.list_directives()

    instruction_list = []
    for di in di_list:
        if di['instruction']==instruction:
            instruction_list.append( directive_to_string(di) )
            print directive_to_string(di)
    return instruction_list

def directive_to_string(d):
    ## FIXME: replace symbols
    if d['instruction']=='assume':
        return '[assume %s %s]' %( d['symbol'], build_exp(d['expression']) ) 
    elif d['instruction']=='observe':
        return '[observe %s %s]' %( build_exp(d['expression']), d['value']) 
    elif d['instruction']=='predict':
        return '[predict %s %s]' % build_exp(d['expression'])


## MRipl Regression Utilities:
###will all be imported to engines via the 'from ip_para import *' instruction for ripls
        
def if_lst_flatten(l):
    if type(l[0])==list: return [el for subl in l for el in subl]
    return l

def heatplot(n2array,nbins=100):
    """Input is an nx2 array, returns xi,yi,zi for colormesh""" 
    x, y = n2array.T
    k = kde.gaussian_kde(n2array.T)
    xi, yi = np.mgrid[x.min():x.max():nbins*1j, y.min():y.max():nbins*1j]
    zi = k(np.vstack([xi.flatten(), yi.flatten()]))
    # plot ax.pcolormesh(xi, yi, zi.reshape(xi.shape))
    return (xi, yi, zi.reshape(xi.shape))

def get_name(r_mr):
    'Input is ripl or mripl, out name string via "model_name" ripl variable'
    mr= 1 if isinstance(r_mr,MRipl) else 0
    # try:
    #     r_mr.dview; mr=1
    # except:
    #     mr=0
    di_l = r_mr.list_directives()[0] if mr else r_mr.list_directives()
    if 'model_name' in str(di_l):
        try:
            n = r_mr.sample('model_name')[0] if mr else r_mr.sample('model_name')
            return n
        except: pass
    else:
        return 'anon model'


def plot_conditional(ripl,data=[],x_range=[],number_xs=40,number_reps=30, return_fig=False,figsize=(16,3.5)):
    ##FIXME we should predict and forget for pivot and maybe everything
    
    name=get_name(ripl)

    # find data, set x-interval on which to sample f(x)
    
    # if data==[]: try: data=ripl_plotting_data; except: pass
    if data:
        d_xs,d_ys = zip(*data)
        if not x_range: x_range = (min(d_xs)-1,max(d_xs)+1)
    
    if not x_range: x_range = (-3,3)
    xr = np.linspace(x_range[0],x_range[1],number_xs)
    
    # sample f on xr and add noise (if noise is a float)
    f_xr = [ripl.sample('(f %f)' % x) for x in xr]
    if "'symbol': 'noise'" in str(ripl.list_directives()):
        noise=ripl.sample('noise')
        fixed_noise = isinstance(noise,float)
        if fixed_noise:
            f_u = [fx+noise for fx in f_xr]; f_l = [fx-noise for fx in f_xr]
    
    # sample (y_x x) for x in xr and compute 1sd intervals
    xys=[]; ymean=[]; ystd=[]
    for x in xr:
        x_y = [ripl.sample('(y_x %f)' % x) for r in range(number_reps)]        
        ymean.append( np.mean(x_y) )
        ystd.append( np.abs( np.std(x_y) ) )
        xys.extend( [(x,y) for y in x_y] )
    
    xs,ys = zip(*xys)
    ymean = np.array(ymean); ystd = np.array(ystd)
    y_u = ymean+ystd; y_l = ymean - ystd
    if not fixed_noise:
        f_u = y_u ; f_l = y_l

    # Plotting
    fig,ax = plt.subplots(1,3,figsize=figsize,sharex=True,sharey=True)
    
    # plot data and f with noise
    if data:
        ax[0].scatter(d_xs,d_ys,label='Data')
        ax[0].legend()
    
    ax[0].plot(xr, f_xr, 'k', color='#CC4F1B')
    ax[0].fill_between(xr,f_l,f_u,alpha=0.5,edgecolor='#CC4F1B',facecolor='#FF9848')
    ax[0].set_title('Ripl: f (+- 1sd noise) w/ data [name: %s]' % name )

    ax[1].scatter(xs,ys,alpha=0.7,s=5,facecolor='0.6', lw = 0)
    ax[1].plot(xr, ymean, 'k', alpha=.9,color='m',linewidth=1)
    ax[1].plot(xr, y_l, 'k', alpha=.8, color='m',linewidth=.5)
    ax[1].plot(xr, y_u, 'k', alpha=.8,color='m',linewidth=.5)
    ax[1].set_title('Ripl: Samples from P(y/X=x), w/ mean +- 1sd [name: %s]' % name )
        
    xi,yi,zi=heatplot(np.array(zip(xs,ys)),nbins=100)
    ax[2].pcolormesh(xi, yi, zi)
    ax[2].set_title('Ripl: GKDE P(y/X=x) [name: %s]' % name )
    
    fig.tight_layout()
    plt.show()

    my_fig = fig if return_fig else None
    return {'f':(xr,f_xr),'xs,ys':(xs,ys),'fig':my_fig}




def lst_plot_conditional(ripl_lst,engine_limit=0,data=[],x_range=(-3,3),number_xs=40,number_reps=40,figsize=(16,3.5)):
    if engine_limit:
        return [plot_conditional(v,data,x_range,number_xs,number_reps) for i,v in enumerate(ripl_lst) if i<engine_limit]
    else:
        return [plot_conditional(v,data,x_range,number_xs,number_reps) for i,v in enumerate(ripl_lst)]

def mr_plot_conditional(mr,plot=True,limit=0,data=[],x_range=(-3,3),number_xs=40,number_reps=40,figsize=(16,3.5)):
    # need to be careful of data: can send with string but maybe better to push the variable and 
    # and send the variable name, instead of potentially long string
    store_id = np.random.randint(10**8)
    no_engines = len(mr.cli.ids)
    engine_limit = int(np.ceil(limit/float(no_engines))) if limit else 0
    
    ## FIXME BACKEND
    s1 = 'plotcond_outs_%i = ' % store_id
    s2 = 'lst_plot_conditional(mripls[%i],engine_limit=%i,data=%s,x_range=%s,number_xs=%i,number_reps=%i,figsize=%s)' %(mr.mrid,
                                      engine_limit,str(data),str(x_range),number_xs,number_reps,str(figsize) )
    
    # dview.execute wouldn't do the inlining because it doesn't return
    if plot:
        try:
            ip=get_ipython()
            ip.run_cell_magic("px",'',s1+s2)
        except:
            pass
    else:
        mr.dview.execute(s1+s2)
    outs = if_lst_flatten( mr.dview.pull('plotcond_outs_%i' % store_id) )                                                                     
    return outs




def predictive(mripl,data=[],x_range=(-3,3),number_xs=40,number_reps=40,figsize=(16,3.5),return_fig=False ):
    mr = mripl
    name=get_name(mr)
    
    if data:
        d_xs,d_ys = zip(*data)
        x_range = (min(d_xs)-1,max(d_xs)+1)
        if not x_range: x_range = (min(d_xs)-1,max(d_xs)+1)
    
    if not x_range: x_range = (-3,3)
        
    xr = np.linspace(x_range[0],x_range[1],number_xs)
    
    list_out=mr_plot_conditional(mr,plot=False,limit=6,data=data,x_range=x_range,number_xs=number_xs,number_reps=1)
    fs = [ ripl_out['f'] for ripl_out in list_out]
    
    ## get y_xs from ripls and compute 1sd intervals
    xys=[]; ymean=[]; ystd=[]
    for x in xr:
        # we get number_reps predicts from each ripl in mr
        x_y=if_lst_flatten([mr.sample('(y_x %f)' % x) for r in range(number_reps)])   
        ymean.append( np.mean(x_y) )
        ystd.append( np.abs( np.std(x_y) ) )
        xys.extend( [(x,y) for y in x_y] )
    
    xs,ys = zip(*xys)
    ymean = np.array(ymean); ystd = np.array(ystd)
    y_u = ymean+ystd; y_l = ymean-ystd
    
     # Plotting
    fig,ax = plt.subplots(1,3,figsize=figsize,sharex=True,sharey=True)

    if data: [ax[col].scatter(d_xs,d_ys,label='Data') for col in [0,1]]
    # sampled fs from mripl
    [ax[0].plot(xr,f_xr,alpha=.8,linewidth=.5) for xr,f_xr in fs]
    if data: ax[0].legend()
    ax[0].set_title('MR: Sampled fs w/ data [name: %s] ' % name )
    
    ax[1].scatter(xs,ys,alpha=0.5,s=5,facecolor='0.6', lw = 0)
    ax[1].plot(xr, ymean, 'k', alpha=.9,color='m',linewidth=1)
    ax[1].plot(xr, y_l, 'k', alpha=.8, color='m',linewidth=.5)
    ax[1].plot(xr, y_u, 'k', alpha=.8,color='m',linewidth=.5)
    ax[1].set_title('MR: Samples from P(y/X=x), w/ mean +- 1sd [name: %s] ' % name )
    if data: ax[1].legend()
        
    xi,yi,zi=heatplot(np.array(zip(xs,ys)),nbins=100)
    ax[2].pcolormesh(xi, yi, zi)
    ax[2].set_title('MR: GKDE P(y/X=x) [name: %s] ' % name )

    [ax[i].set_xlim(x_range[0],x_range[1]) for i in range(3)]
    
    fig.tight_layout()
    
    return xs,ys


####### OLD DOCSTRING (still mostly applies)
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
