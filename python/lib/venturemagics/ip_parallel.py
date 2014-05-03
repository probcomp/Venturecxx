from IPython.parallel import Client
from IPython.parallel.util import interactive
from venture.shortcuts import make_puma_church_prime_ripl
from venture.shortcuts import make_lite_church_prime_ripl
import numpy as np
import matplotlib.pylab as plt
from scipy.stats import kde
gaussian_kde = kde.gaussian_kde
import subprocess,time,pickle
mk_l_ripl = make_lite_church_prime_ripl
mk_p_ripl = make_puma_church_prime_ripl

### IPython Parallel Magics

# TODO:
# doc_strings, check the outputs of functions, make mr_map_array work on lower no. engines
# get rid of use of interactive on certain utility funcs
# if it breaks use outside MRIPL

# move regression stuff to regression utils
# IMP: implement set_seeds
# make private methods private
# check for 'if varname' where varname=None by default



# Utility functions for working with ipcluster and mripl

def erase_initialize_mripls(client=None,no_erase=False):
    '''Clear engine namespaces and initialize with mripls list. Optionally specify
    a pre-existing client object. If *no_erase* then will only clear and
    initialize if mripls list and counter are not present in engines.'''
    
    if not client: client=Client(); print "Created new Client"
    if no_erase:
        try: # mripl vars already present: return client object
            client[:]['no_mripls']
        except:
            client[:].execute('mripls=[]; no_mripls=0')
        return client
    else:
        client.clear()
        print 'Cleared engine namespaces and created new empty list "mripls"'
        client[:].execute('mripls=[]; no_mripls=0')
        return client
    
def start_engines(no_engines,sleeptime=10):
    start = subprocess.Popen(['ipcluster', 'start', '--n=%i' % no_engines,'&'])
    time.sleep(sleeptime)
   
def stop_engines(): 
    stop=subprocess.Popen(['ipcluster', 'stop'])
    stop.wait()

        
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
        if exp['type']=='atom':
            return 'atom<%i>'%exp['value']
        else:
            return str(exp['value'])
    else:
        return '('+ ' '.join(map(build_exp,exp)) + ')'

## MRIPL CLASS

class MRipl():
    
    def __init__(self, no_ripls, backend='puma', no_local_ripls=None,
                 output='remote',local_mode=False,seeds=None,verbose=False):
        '''
        MRipl(no_ripls,backend='puma',no_local_ripls=1,output='remote',local_mode=False,seeds=None,verbose=False)

        Create an Mripl. Will fail unless an IPCluster is already running
        or *local_model*=True.


        Arguments for Constructor
        ------------------------

        no_ripls : int
           Lower bound on number of remote ripls. 
           Actual number of ripls will be no_engines*ceil(no_ripls/no_engines)
        backend : 'puma' or 'lite'
           Set backend for both local and remote ripls. Can be switched later using
           self.switch_backend method at the cost of resetting inference.
        no_local_ripls : int => 1
           Number of local ripls. These ripls are accessed via the attribute
           self.local_ripls.
        output : 'remote','local','both'
           Unless local_mode=True, all directives are applied to both local and
           remote ripls. This parameter sets whether the output for an mripl
           directive comes from local, remote or both sets of ripls. 
        local_mode : bool
           If False, all directives are applied to both local and remote ripls.
           If True, directives are only applied locally. Thus no IPCluster needs
           to be running to work with Mripl objects.
        seeds : {"local":list,"remote":list}'
           Allows the seeds local and remote ripls to be set. Lists must be
           length specified by no_local_ripls and no_ripls. If None, seeds
           are set to range(no_local_ripls) and range(no_ripls) respectively.
        verbose : bool
          If True, prints information on state of Mripl and ripl inference.

        Attributes
        ----------
        backend : see above
        output : see above
        local_mode : see above
        no_ripls : see above
        no_local_ripls : see above
        local_ripls : list
           List of local ripls. 
        seeds : list
           List of remote seeds. These are divided between the engines such that
           Engine 0 gets seeds[0:k], Engine 1 gets seeds[k:2*k], where k is the
           ceil(no_ripls/no_engines).
        local_seeds : list
           Local seeds.
        cli : Client
           Client object for remote engines.
        dview : DirectView
           View on all engines. Blocking is set to True.
        no_engines : int
           len(self.cli.ids)
        no_ripls_per_engine : int
           = ceil(no_ripls/no_engines).
        mrid : int
           Mripl id, used as index into the mripls list on the remote engines.
           We need this because the mripls list will store ripls for multiple
           distinct Mripls. 
       no_transitions : int
           Records number of inference transitions. Won't record transitions
           specified via mr_map_proc and mr_map_array. 
        '''
        
        self.backend = backend
        assert output in ['remote','local','both']
        self.output = output   
        self.local_mode = local_mode 
        self.total_transitions = 0
        self.verbose = verbose

        # initialize local ripls
        if no_local_ripls is None:
            self.no_local_ripls = no_ripls if self.local_mode else 1
        else:
            self.no_local_ripls=no_local_ripls

        if self.local_mode:
            self.no_ripls=self.no_local_ripls
        self.local_seeds = range(self.no_local_ripls) if not seeds else seeds['local']  

        mk_ripl = mk_p_ripl if self.backend=='puma' else mk_l_ripl
        self.local_ripls=[mk_ripl() for i in range(self.no_local_ripls)]
        self.mr_set_seeds(local_seeds=self.local_seeds)
        if self.local_mode:
            self.seeds = self.local_seeds
            return



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
        self.dview.block = True   # FIXME reconsider async infer
        
        # Imports for remote ripls
        self.dview.execute('from venture.venturemagics.ip_parallel import *')
        # FIXME namespace issues
        self.dview.execute('%pylab inline --no-import-all')
        
        def p_getpids(): import os; return os.getpid()
        self.pids = self.dview.apply(p_getpids)

        self.mrid = self.dview.pull('no_mripls')[0]
        # id is index into mripls list
        self.dview.push({'no_mripls':self.mrid+1})

        
        # proc creates ripls, using ripls_per_engine attribute we send to engines
        @interactive
        def make_mripl_proc(no_ripls_per_engine):
            k=no_ripls_per_engine
            mripls.append({'lite':[make_lite_church_prime_ripl() for i in range(k)],
                           'puma':[make_puma_church_prime_ripl() for i in range(k)],
                           'seeds':[]})
            
        self.dview.apply(make_mripl_proc,self.no_ripls_per_engine)

        self.mr_set_seeds(self.seeds)
        
      
        # invariant
        @interactive
        def get_seeds(mrid): return mripls[mrid]['seeds']
        assert self.seeds==self.lst_flatten(self.dview.apply(get_seeds,self.mrid))

        
        if self.verbose: print self.ripls_info()



## MRIPL METHODS FOR CONTROLLING REMOTE ENGINES/BACKEND
 

    def mr_set_seeds(self,seeds=None,remote_seeds=None,local_seeds=None):
        '''Set seeds for remote engines. Input: list of seeds of length
        self.no_mripls. Seeds distributed in order:
         (eng_id0,ripl_ind0), (eng_id0,ripl_id1), ... (eng_id1,ripl_id0), ...'''
        if seeds is not None:
            if self.local_mode:
                local_seeds = seeds
            else:
                remote_seeds = seeds
                
        if local_seeds is not None:
            assert len(local_seeds)==self.no_local_ripls
            self.local_seeds = local_seeds
            [v.set_seed(i) for (v,i) in zip(self.local_ripls,self.local_seeds)]
        if self.local_mode:
            self.seeds = self.local_seeds
            return
            
        if remote_seeds is None: return    

        assert len(remote_seeds)==self.no_ripls
        self.seeds = remote_seeds
        
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

        return


    def __del__(self):
        if not self.local_mode:
            if self.verbose:
                print '__del__ is closing client for mripl with mrid %i' % self.mrid
            self.cli.close()
    
    def lst_flatten(self,l): return [el for subl in l for el in subl]

    
    def mk_directives_string(self,ripl):
        di_string_lst = [directive_to_string(di) for di in ripl.list_directives() ]
        return '\n'.join(di_string_lst)
    
    def reset_seeds(self):
        'Assumes that set_seed has no output'
        [r.set_seed(seed) for r,seed in zip(self.local_ripls,self.local_seeds)]
        if self.local_mode: return

        @interactive
        def f(mrid,backend):
            seeds=mripls[mrid]['seeds']
            [r.set_seed(seed) for r,seed in zip(mripls[mrid][backend],seeds)]
        return self.dview.apply(f,self.mrid,self.backend)


    def switch_backend(self,backend):
        'Clears ripls for new backend and resets transition count'
        if backend==self.backend: return None
        self.backend = backend
        self.total_transitions = 0
        
        di_string = self.mk_directives_string(self.local_ripls[0])
        if not(di_string):
            print 'No directives.'; return None

        # Switch local backend
        mk_ripl = mk_p_ripl if self.backend=='puma' else mk_l_ripl
        self.local_ripls=[mk_ripl() for i in range(self.no_local_ripls)]
        [r.execute_program(di_string) for r in self.local_ripls]
        if self.local_mode:
            self.reset_seeds(); return
            
        # CLEAR ripls: else when switching back to a backend
        # we would redefine some variables
        @interactive
        def send_ripls_di_string(mrid,backend,di_string):
            mripl=mripls[mrid]
            [r.clear() for r in mripl[backend]]
            [r.execute_program(di_string) for r in mripl[backend]]

        self.dview.apply(send_ripls_di_string,self.mrid,self.backend,di_string)
        self.reset_seeds()


    def add_ripls(self,new_remote_ripls=0,new_local_ripls=0):
        'Add ripls with same directives as existing ripls.'

        di_string = self.mk_directives_string(self.local_ripls[0])
        if not(di_string_lst):
            print 'No directives.'; return None

        if new_local_ripls:
            nl = self.no_local_ripls
            self.local_seeds.extend( range(nl,nl+new_local_ripls) )
            mk_ripl = mk_p_ripl if self.backend=='puma' else mk_l_ripl
            self.local_ripls.extend( [mk_ripl() for i in range(new_local_ripls)] )
            for (r,seed) in zip(self.local_ripls,self.local_seeds)[nl]:
                r.set_seed(seed)
                r.execute_program(di_string)

            if self.local_mode: return

        if new_remote_ripls:
            print 'Not implemented yet'
            return


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
        



    ### MRIPL SHADOWED RIPL METHODS

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
    ## FIXME: need to serialize directives list

               
    ## MRIPL CONVENIENCE FEATURES: INFO AND SNAPSHOT
    
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

        if plot_range: # test plot_range == (xrange[,yrange])
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
        if self.local_mode: assert False, 'Local mode'
        assert len(exp_list)==1, 'len(exp_list)!=1'
        exp = exp_list[0]
        no_groups,pop_size = groups_popsize

        def pred_repeat_forget(r,exp,pop_size):
            vals=[r.predict(exp,label='snapsp_%i'%j) for j in range(pop_size)]
            [r.forget('snapsp_%i'%j) for j in range(pop_size)]
            return vals

        def fast_pred_repeat_forget(r,exp,pop_size):
            # if 'repeat9999' in r.list_directives(): don't define, else define
            rand_id = np.random.randint(10**9)
            r.assume('repeat%s'%rand_id,
                     '(lambda (th n) (if (= n 0) (list) (pair (th) (repeat%s th (- n 1) ) ) ) ) '%rand_id,
                     label='repeat%s'%rand_id)
            vals=r.predict('(repeat%s (lambda () %s ) %i)'%(rand_id,exp,pop_size),label='snapshot%s'%rand_id)
            
            r.forget('snapshot%s'%rand_id)
            return vals
        
        mrmap_values = mr_map_proc(self, no_groups,
                                pred_repeat_forget, exp, pop_size)

        #mrmap_values2 = mr_map_proc(self, no_groups,fast_pred_repeat_forget, exp, pop_size)

        if flatten: mrmap_values = self.lst_flatten(mrmap_values)

        out['values'][exp]=mrmap_values
        
        if not(plot): return out

        if plot and flatten: # Predictive (Repeat)
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
            current_vals = None
            exp_name = past_values_list[0]['values'].keys()[0]

        assert isinstance(past_values_list,(list,tuple))

        list_vals = [ past_out['values'].values()[0] for past_out in past_values_list]
        if current_vals: list_vals.append( current_vals ) 

        fig,ax=plt.subplots(1,2,figsize=(14,3.5),sharex=True)
        all_vals=self.lst_flatten(list_vals)
        xr=np.linspace(min(all_vals),max(all_vals),50)

        for count,past_vals in enumerate(list_vals):
            label='Pr [0]' if count==0 else 'Po [%i]'%count
            alpha = .9 - .1*(len(list_vals) - count )
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




        
### Functions defined on MRipl objects 


# Utility functions for mr_map functions
def lst_flatten(l): return [el for subl in l for el in subl]

def ipython_inline():
    '''Try to run ipython px cell magic on empty cell
    to display previously generated figs inline.'''
    try: 
        ip=get_ipython()
        ip.run_cell_magic("px",'','pass') # display any figs inline
    except:
        pass

def mr_map_proc(mripl,no_ripls,proc,*proc_args,**proc_kwargs):
    '''Push procedure into engine namespaces. Use execute to map across ripls.
    if no_ripls==0, 'all' or >mripl.no_ripls, then maps across all.
    Maps proc across local ripls IFF in local_mode or mripl.output=="local".'''

    ## FIXME: should be able to supress stdout from local_ripls when in remote mode
    if no_ripls==0 or no_ripls=='all' or no_ripls>mripl.no_ripls:
        no_ripls = mripl.no_ripls
        no_local_ripls = mripl.no_local_ripls

    # map across local ripls
    local_out=[proc(r,*proc_args,**proc_kwargs) for i,r in enumerate(mripl.local_ripls) if i<no_ripls]
    if mripl.local_mode: return local_out

    # map across remote ripls
    mripl.dview.push({'map_proc':interactive(proc),'map_args':proc_args,
                      'map_kwargs':proc_kwargs})

    if no_ripls < mripl.no_engines:
        map_view = mripl.cli[:no_ripls]
        per_eng = 1
        mripl.dview.execute('apply_out=None')
    else:
        per_eng = int(np.ceil(no_ripls/float(mripl.no_engines)))
    
    s1='apply_out='
    s2='[map_proc(r,*map_args,**map_kwargs) for i,r in enumerate(mripls[%i]["%s"]) if i<%i]' % (mripl.mrid,
                                                                                                mripl.backend,per_eng)
    mripl.dview.execute(s1+s2)  
    
    ipython_inline()

    remote_out = lst_flatten( mripl.dview['apply_out'] )
    
    return remote_out[:no_ripls] if mripl.output=='remote' else local_out 


def mr_map_array(mripl,proc,proc_args_list,no_kwargs=True,id_info_out=False):
    '''REDO DOCTSTRING
    proc_args_list = [ [ list_args_i, dict_kwargs_i ],   ], i= 0 to no_args
    where no_args <= mripl.no_ripls.

    Examples:
    v=MRipl(2)
    def f(ripl,x,y): return ripl.sample('(+ %f %f)'%(x,y))
    proc_args_list = [ [10,20], [100,200] ]
    mr_map_array(v,f,proc_args_list)[1] == [30,300] 

    def f(ripl,x,y=1): return ripl.sample('(+ %f %f)'%(x,y))
    proc_args_list = [  [ [10],{'y':10} ],  [ [30],{} ] ]
    mr_map_array(v,f,proc_args_list,no_kwargs=False)[1] == [20,31] 
    '''
    ##FIXME should support limiting the number of ripls to < no_engines
    
    no_args = len(proc_args_list)
    assert no_args <= mripl.no_ripls, 'More arguments than ripls'
    
    # map across local ripls
    id_local_out=[]
    local_out=[]
    for i,r in enumerate(mripl.local_ripls):
        if i<no_args:
            id_args = (mripl.local_seeds[i],proc_args_list[i])
            if no_kwargs:
                outs = proc(r,*proc_args_list[i])
            else:
                outs = proc(r,*proc_args_list[i][0],**proc_args_list[i][1])
            local_out.append( outs )
            id_local_out.append( (id_args,outs))
    local_out = id_local_out if id_info_out else local_out
    if mripl.local_mode: return local_out
              
    # map across remote ripls
    no_args_per_engine = int(np.ceil(no_args/float(mripl.no_engines)))
    extra_ripls = no_args_per_engine - no_args
    proc_args_list = proc_args_list + [proc_args_list[-1]]*extra_ripls # pad args with last element

    for i in range(mripl.no_engines):
        engine_view = mripl.cli[i]
        start=i*no_args_per_engine
        eng_args = proc_args_list[start:start+no_args_per_engine]
        engine_view.push({'ar_proc':interactive(proc),'eng_args':eng_args,
                          'per_eng':len(eng_args)})
        engine_view.push({'array_out':[]})

        @interactive
        def f(mrid,backend,eng_args,no_kwargs):
            import os
            for i,r in enumerate(mripls[mrid][backend]):
                if i<per_eng:
                    id_args = (os.getpid(), mripls[mrid]['seeds'][i], eng_args[i]),
                    if no_kwargs:
                        outs =ar_proc(r,*eng_args[i])
                    else:
                        outs=ar_proc(r,*eng_args[i][0],**eng_args[i][1])
                    array_out.append((id_args,outs))
            return None

        engine_view.apply_sync(f,mripl.mrid,mripl.backend,eng_args,no_kwargs)

    ipython_inline()
    id_remote_out = (('pid','seed','arg'),lst_flatten( mripl.dview['array_out'] ) )
    remote_out = [outs for id_args,outs in id_remote_out[1]]
    remote_out = remote_out if not id_info_out else id_remote_out

    return remote_out if mripl.output=='remote' else local_out 



def venture(line, cell):
    'args: r_mr_name [,no_ripls_output]'
    ##FIXME: we should recursively extract value when assigning to 'values'
    mripl_name =  str(line).split()[0]
    if len(str(line).split())>1:
        limit = int(str(line).split()[1])
    else:
        limit = 5
    mripl = eval(mripl_name,globals(),ip.user_ns)
    out = mripl.execute_program(str(cell))
    
    if isinstance(mripl,MRipl):
        try:
            values = [[d['value']['value'] for d in ripl_out] for ripl_out in out ]
            for i,val in enumerate(values):
                if i<limit:
                    print 'Ripl %i of %i: '%(i,mripl.no_ripls), val
                if i==limit: print '...'
        except:
            pass
    else:
        try:
            values = [d['value']['value'] for d in out]
            print values
        except:
            pass

    return None  
    

## Register the cell magic for IPython use
try:
    ip = get_ipython()
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
    vs=[mk_l_ripl(),mk_p_ripl()]
    [v.execute_program(library_string) for v in vs]
    vs[0].execute_program(lite_addendum)
    return vs


## Utility functions for working with MRipls

def display_directives(ripl_mripl,instruction='observe'):
    ## FIXME add replace with dict of symbls
    ## FIXME: add did and labels
    v=ripl_mripl
    mr=1  if isinstance(v,MRipl) else 0
    di_list = v.local_ripls[0].list_directives() if mr else v.list_directives()

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
        return '[predict %s]' % build_exp(d['expression'])


def directive_split(d):
    ## FIXME: replace symbols
    if d['instruction']=='assume':
        return (d['symbol'], build_exp(d['expression']) ) 
    elif d['instruction']=='observe':
        return (build_exp(d['expression']), d['value']) 
    elif d['instruction']=='predict':
        return build_exp(d['expression'])



## MRipl Regression Utilities:
# these are imported to engines via 'from ip_parallel import *' instruction for ripls
# note that we don't need plot condition here
# we can put it in regression utils, and let heatplot etc be defined
# inside its local scope. 
        
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
    'Input: ripl or mripl. Output: name string via "model_name" ripl variable'
    di_l = r_mr.list_directives()
    if 'model_name' in str(di_l):
        for di in di_l:
            if di['symbol']=='model_name': return di['value']
    return 'anon model'


def plot_conditional(ripl,data=[],x_range=[],number_xs=40,number_reps=30, return_fig=False,figsize=(16,3.5),plot=True):
    ##FIXME we should predict and forget for pivot and maybe everything
    
    name=get_name(ripl)

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
    my_fig = None
    if plot:
        fig,ax = plt.subplots(1,3,figsize=figsize,sharex=True,sharey=True)

        # plot data and f with noise
        if data:
            ax[0].scatter(d_xs,d_ys,label='Data')
            ax[0].legend()

        ax[0].plot(xr, f_xr, 'k', color='#CC4F1B')
        ax[0].fill_between(xr, f_l, f_u, alpha=0.5,
                           edgecolor='#CC4F1B',facecolor='#FF9848')
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
    #plt.show()  #FIXME: uncommenting leads to notebook not inlining images. why?
        my_fig = fig if return_fig else None

    return {'f':(xr,f_xr),'xs,ys':(xs,ys),'fig':my_fig}



def predictive(mripl,data=[],x_range=(-3,3),number_xs=40,number_reps=40,figsize=(16,3.5),return_fig=False ):
    mr = mripl
    name=get_name(mr)
    
    if data:
        d_xs,d_ys = zip(*data)
        x_range = (min(d_xs)-1,max(d_xs)+1)
        if not x_range: x_range = (min(d_xs)-1,max(d_xs)+1)
    
    if not x_range: x_range = (-3,3)
        
    xr = np.linspace(x_range[0],x_range[1],number_xs)
    
                        
    list_out=mr_map_proc(mr,min(mr.no_ripls,6),plot_conditional,
                         data=data,x_range=x_range,number_xs=number_xs,
                         number_reps=1,plot=False)
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
