from IPython.parallel import Client
from IPython.parallel.util import interactive
from venture.shortcuts import make_puma_church_prime_ripl
from venture.shortcuts import make_lite_church_prime_ripl
from venture.shortcuts import make_puma_venture_script_ripl
from venture.shortcuts import make_lite_venture_script_ripl
import numpy as np
import matplotlib.pylab as plt
from scipy.stats import kde
gaussian_kde = kde.gaussian_kde
import subprocess,time,pickle
mk_l_ripl = make_lite_church_prime_ripl
mk_p_ripl = make_puma_church_prime_ripl



### IPython Parallel Magics

# REFACTORING TO DEAL WITH SLOWDOWN DUE TO LOCAL RIPL
# 1. If we want to have 0 local ripls as default, we can
#  have following structure for a method

# def local_f(): return [proc(v) for v in localripls]

# def remote_f(ripl,mrid,..) return [f(mapped on remoted ripls)]

# if self.local_mode: return local_f()
# elif not_debug: return dview.apply(remote_f)
# else return local_f(),dview.apply(remote_f)

# note: might be able to simplify each (esp. local) with decorators.

# constructor:
# default is for only working with remotes. local_mode is only
# with local. then debug mode gives default of one local, with
# more as specified optionally.


# TODO:
# optional default inference program for mripl
# v.plot('x',**plottingkwargs) = v.snapshot(exp_list=['x'],plot=True,**kwargs)
# move local_out to debug mode
# move regression stuff to regression utils




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



## MRIPL CLASS

class MRipl():

    def __init__(self, no_ripls, backend='puma',
                 syntax='church_prime', local_mode=False,
                 seeds=None, debug_mode=False, set_no_engines=None):

# TODO DEBUG MODE should probably run inference
        '''
        MRipl(no_ripls,backend='puma',local_mode=False,seeds=None,debug_mode=False)

        Create an Mripl. Will fail unless an IPCluster is already running
        or *local_model*=True.


        Arguments for Constructor
        ------------------------

        no_ripls : int
           Lower bound on number of remote ripls.
           Actual number of ripls will be no_engines*ceil(no_ripls/no_engines)
        backend : 'puma' or 'lite'
           Set backend for both local and remote ripls. Can be switched later using
           self.switch_backend method (resets inference).
        local_mode : bool
           If False, all directives are applied to both local and remote ripls.
           If True, directives are only applied locally. Thus no IPCluster needs
           to be running to work with Mripl objects.
        seeds : list
           Set ripl seeds to seeds[:no_ripls]. If None, ripl seeds are range[:no_ripls].

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

        # initialize attributes
        self.backend = backend
        self.output = 'remote' if not debug_mode else 'both'
        self.total_transitions = 0
        self.verbose = True if debug_mode else False
        assert not (local_mode and debug_mode), 'Local_mode must be False for debug_mode.'

        # set local vs. remote mode
        if local_mode is False:
            try:
                self.cli=Client()
                self.local_mode = False
            except:
                print 'Failed to create IPython Parallel Client object.'
                print 'MRipl is running in local (serial) model.'
                self.local_mode = True
        else:
            self.local_mode = True


        # initialize local ripls
        if self.local_mode is True:
            self.no_local_ripls = no_ripls
            self.no_ripls = self.no_local_ripls
        elif debug_mode:
            self.no_local_ripls = no_ripls
        else:
            self.no_local_ripls = 1

        if not seeds:
            self.local_seeds = range(self.no_local_ripls)
        else:
            self.local_seeds = seeds[:self.no_local_ripls]

        self.syntax = syntax
        if self.backend=='puma':
            if self.syntax == 'church_prime':
                mk_ripl = make_puma_church_prime_ripl
            else:
                mk_ripl = make_puma_venture_script_ripl
        else:
            if self.syntax == 'church_prime':
                mk_ripl = make_lite_church_prime_ripl
            else:
                mk_ripl = make_lite_venture_script_ripl
                
        self.local_ripls=[mk_ripl() for i in range(self.no_local_ripls)]
        self.mr_set_seeds(local_seeds=self.local_seeds)

        # set _n_prelude
        self._n_prelude = self.local_ripls[0]._n_prelude

        if self.local_mode:
            self.seeds = self.local_seeds
            return  # can't initialze remote ripl without ipcluster


        ## initialize remote ripls
        if set_no_engines is not None:
            assert set_no_engines <= len(self.cli.ids), 'Not enough ipcluster engines'
            self.no_engines = set_no_engines
            self.dview = self.cli[:set_no_engines]
        else:
            self.no_engines = len(self.cli.ids)
            self.dview=self.cli[:]

        try:
            self.dview['no_mripls']
        except:
            self.dview.execute('mripls=[]; no_mripls=0')
            print "New list *mripls* created on remote engines."

        self.no_ripls_per_engine = int(np.ceil(no_ripls/float(self.no_engines)))
        self.no_ripls = self.no_engines * self.no_ripls_per_engine
        s='MRipl has %i ripls and %i ripl(s) per engine'%(self.no_ripls,
                                                        self.no_ripls_per_engine)
        print s


        self.seeds = range(self.no_ripls) if not seeds else seeds[:self.no_ripls]

        self.dview.block = True

        # Imports for remote ripls: needed for creating ripls on engines
        self.dview.execute('from venture.venturemagics.ip_parallel import *')
        self.dview.execute('%pylab inline --no-import-all')

        def p_getpids(): import os; return os.getpid()
        self.pids = self.dview.apply(p_getpids)

        self.mrid = self.dview.pull('no_mripls')[0] # id is index into mripls list
        self.dview.push({'no_mripls':self.mrid+1})


        # proc creates ripls, using ripls_per_engine attribute we send to engines
        @interactive
        def make_mripl_proc(no_ripls_per_engine,syntax):
            k=no_ripls_per_engine

            if syntax == 'church_prime':
                mk_puma = make_puma_church_prime_ripl
                mk_lite = make_lite_church_prime_ripl
            else:
                mk_puma = make_puma_venture_script_ripl
                mk_lite = make_lite_venture_script_ripl
                
            mripls.append({'lite':[mk_lite() for i in range(k)],
                           'puma':[mk_puma() for i in range(k)], 'seeds':[]})

        self.dview.apply(make_mripl_proc,
                         self.no_ripls_per_engine, self.syntax)
        self.mr_set_seeds(self.seeds)

        # test invariant
        def get_seeds(mrid): return mripls[mrid]['seeds']
        assert self.seeds==lst_flatten(self.dview.apply( interactive(get_seeds), self.mrid))

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



    def __del__(self):
        if not self.local_mode:
            if self.verbose:
                print '__del__ is closing client for mripl with mrid %i' % self.mrid
            self.cli.close()


    def reset_seeds(self):
        'Set seeds back to seeds specified in constructuor'
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

        di_string = mk_directives_string(self.local_ripls[0])
        if not(di_string):
            print 'No directives.'; return None

        # Switch local backend
        mk_ripl = mk_p_ripl if self.backend=='puma' else mk_l_ripl
        self.local_ripls=[mk_ripl() for i in range(self.no_local_ripls)]
        [r.execute_program(di_string) for r in self.local_ripls]
        if self.local_mode:
            self.reset_seeds(); return

        # Clear ripls: else when switching back to a backend
        # we would redefine some variables
        @interactive
        def send_ripls_di_string(mrid,backend,di_string):
            mripl=mripls[mrid]
            [r.clear() for r in mripl[backend]]
            [r.execute_program(di_string) for r in mripl[backend]]

        self.dview.apply(send_ripls_di_string,self.mrid,self.backend,di_string)
        self.reset_seeds()


    def _add_ripls(self,new_remote_ripls=0,new_local_ripls=0):
        'Add ripls with same directives as existing ripls.'

        di_string = mk_directives_string(self.local_ripls[0])
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


    def _output_mode(self,local,remote):
        if self.output=='local':
            return local
        elif self.output=='remote':
            return remote
        else:
            return (local,remote)


    def _mr_apply(self,local_out,f,*args,**kwargs):
        if self.local_mode: return local_out

        # all remote apply's have to pick a mrid and backend
        remote_out = lst_flatten( self.dview.apply(f,self.mrid,self.backend,*args,**kwargs) )
        return self._output_mode(local_out,remote_out)




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

        apply_out=self._mr_apply(local_out,f)
        self.reset_seeds() # otherwise all seeds the same
        return apply_out


    def assume(self,sym,exp,**kwargs):
        local_out = [r.assume(sym,exp,**kwargs) for r in self.local_ripls]

        @interactive
        def f(mrid,backend,sym,exp,**kwargs):
            mripl=mripls[mrid]
            out = [r.assume(sym,exp,**kwargs) for r in mripl[backend]]
            return backend_filter(backend,out)

        return self._mr_apply(local_out,f,sym,exp,**kwargs)


    def observe(self,exp,val,label=None):
        local_out = [r.observe(exp,val,label=label) for r in self.local_ripls]

        @interactive
        def f(mrid,backend,exp,val,label=None):
            mripl=mripls[mrid]
            out = [r.observe(exp,val,label) for r in mripl[backend]]
            return backend_filter(backend,out)

        return self._mr_apply(local_out,f,exp,val,label=label)


    def predict(self,exp,label=None,type=False):
        local_out = [r.predict(exp,label=label,type=type) for r in self.local_ripls]

        @interactive
        def f(mrid,backend,exp,label=None,type=False):
            mripl=mripls[mrid]
            out = [r.predict(exp,label=label,type=type) for r in mripl[backend]]
            return backend_filter(backend,out)

        return self._mr_apply(local_out,f,exp,label=label,type=type)


    def sample(self,exp,type=False):
        local_out = [r.sample(exp,type=type) for r in self.local_ripls]

        @interactive
        def f(mrid,backend,exp,type=False):
            mripl=mripls[mrid]
            out = [r.sample(exp,type=type) for r in mripl[backend]]
            return backend_filter(backend,out)

        return self._mr_apply(local_out,f,exp,type=type)


    def _update_transitions(self,params):
        if isinstance(params,int):
            self.total_transitions += params
        elif isinstance(params,dict) and 'transitions' in params:
            self.total_transitions += params['transitions']
        else:
            self.total_transitions += 1

        if self.verbose: print 'total transitions: ',self.no_transitions


    def infer(self,params,block=True):
        self._update_transitions(params)

        if self.local_mode:
            return [r.infer(params) for r in self.local_ripls]
        else:
            local_out = [None] * self.no_local_ripls

        @interactive
        def f(mrid,backend,params):
            return [r.infer(params) for r in mripls[mrid][backend] ]

        if block:
            remote_out= lst_flatten( self.dview.apply_sync(f,self.mrid,self.backend,params) )
        else:
            remote_out = lst_flatten( self.dview.apply_async(f,self.mrid,self.backend,params) )


        return self._output_mode(local_out,remote_out)



    def report(self,label_or_did,**kwargs):
        local_out = [r.report(label_or_did,**kwargs) for r in self.local_ripls]

        @interactive
        def f(mrid,backend,label_or_did,**kwargs):
            mripl=mripls[mrid]
            out = [r.report(label_or_did,**kwargs) for r in mripl[backend]]
            return backend_filter(backend,out)

        return self._mr_apply(local_out,f,label_or_did,**kwargs)


    def forget(self,label_or_did):
        local_out = [r.forget(label_or_did) for r in self.local_ripls]
        # if it's an int and it's forgetting a prelude command, decrement _n_prelude
        if isinstance(label_or_did,int) and (label_or_did <= self._n_prelude):
            self._n_prelude -= 1
        @interactive
        def f(mrid,backend,label_or_did):
            return [r.forget(label_or_did) for r in mripls[mrid][backend]]

        return self._mr_apply(local_out,f,label_or_did)

    def force(self,expression,value):
        ##FIXME why pickling error
        local_out = [r.force(expression,value) for r in self.local_ripls]
        @interactive
        def f(mrid,backend,expression,value):
            [r.force(expression,value) for r in mripls[mrid][backend]]
            return None
        return self._mr_apply(local_out,f,expression,value)


    ## FIXME: need to be rewritten
    def _continuous_inference_status(self):
        self.local_ripl.continuous_inference_status()
        @interactive
        def f(mrid):
            return [ripl.continuous_inference_status() for ripl in mripls[mrid]]
        return lst_flatten( self.dview.apply(f, self.mrid) )

    def _start_continuous_inference(self, params=None):
        self.local_ripl.start_continuous_inference(params)
        @interactive
        def f(params, mrid):
            return [ripl.start_continuous_inference(params) for ripl in mripls[mrid]]
        return lst_flatten( self.dview.apply(f, params, self.mrid) )

    def _stop_continuous_inference(self):
        self.local_ripl.stop_continuous_inference()
        @interactive
        def f(mrid):
            return [ripl.stop_continuous_inference() for ripl in mripls[mrid]]
        return lst_flatten( self.dview.apply(f, self.mrid) )
    ## END FIXME


    def execute_program(self,program_string,params=None):

        local_out=[r.execute_program(program_string, params) for r in self.local_ripls]

        @interactive
        def f(mrid,backend,program_string, params ):
            mripl=mripls[mrid]
            out = [r.execute_program(program_string, params) for r in mripl[backend]]
            return backend_filter(backend,out)

        out_execute= self._mr_apply(local_out,f,program_string,params)

        if '[clear]' in program_string.lower():
            self.total_transitions = 0
            print 'Clear. Total MRipl transitions reset to 0'
            self.reset_seeds()

        return out_execute

    def load_prelude(self):
        local_out=[r.load_prelude() for r in self.local_ripls]

        @interactive
        def f(mrid,backend):
            mripl=mripls[mrid]
            out = [r.load_prelude() for r in mripl[backend]]
            return backend_filter(backend,out)

        out_execute= self._mr_apply(local_out,f)

        return


    def get_global_logscore(self):
        local_out = [r.get_global_logscore() for r in self.local_ripls]

        @interactive
        def f(mrid,backend):
            return [r.get_global_logscore() for r in mripls[mrid][backend]]

        return self._mr_apply(local_out,f)


    def list_directives(self,type=False, include_prelude=False):
        return self.local_ripls[0].list_directives(type=type,
                                                   include_prelude=include_prelude)
    ## FIXME: need to serialize directives list

    def print_directives(self,*instructions,**kwargs):
        return self.local_ripls[0].print_directives(*instructions,**kwargs)


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

        remote_out = lst_flatten( self.dview.apply(get_info,self.mrid,self.backend) )

        return self._output_mode(local_out,remote_out)


# TODO: refactor as special case of map_proc_list
    def map_proc(self,no_ripls,proc,*proc_args,**proc_kwargs):
        '''Map a procedure *proc*, which must take a single ripl as first
        positional argument, across a subset of ripls in MRipl.
        If *no_ripls* is "all" or is > self.no_ripls, then maps across all.
        Maps procedure *proc* across local ripls only if in local_mode.'''

        if no_ripls==0 or no_ripls=='all' or no_ripls>self.no_ripls:
            no_ripls = self.no_ripls

        # map across local ripls
        if self.local_mode:
            local_out=[proc(r,*proc_args,**proc_kwargs) for i,r in enumerate(self.local_ripls) if i<no_ripls]
            return local_out
        else:
            local_out = [None]*no_ripls

        # map across remote ripls
        self.dview.push({'proc':interactive(proc),'p_args':proc_args,
                         'p_kwargs':proc_kwargs})

        if no_ripls < self.no_engines:
            map_view = self.cli[:no_ripls] # view on engines we need
            per_eng = 1
        else:
            map_view = self.dview
            per_eng = int(np.ceil(no_ripls/float(self.no_engines)))

        params = (self.mrid,self.backend,per_eng)
        s1='apply_out='
        s2='[proc(r,*p_args,**p_kwargs) for i,r in enumerate(mripls[%i]["%s"]) if i<%i]'%params

        map_view.execute(s1+s2)
        ipython_inline()
        remote_out = lst_flatten( map_view['apply_out'] )

        return remote_out[:no_ripls] if self.output=='remote' else local_out


    def map_proc_list(self, proc, proc_args_list, only_p_args=True):
        '''
        Maps a procedure *proc*, taking single ripl as first positional
        argument, across subset of ripls in MRipl.

        Additional arguments to proc are in lists in proc_args_list
        and may vary across ripls.

        proc_args_list = [ [ arg_i0, arg_i1, ..., arg_ik  ], ...,  ]
        where k is the # positional args for proc and i=0 to # calls to proc.

        number of calls to proc == len(proc_args_list) <= self.no_ripls

        For kwargs: set only_p_args=False and then
        proc_args_list = [ ( p_args_list, kwargs_dict) ].

        To find which args went to which engines:
            %px eng_args
        These can be matched to seeds via self.ripls_info.

        Examples:
        v=MRipl(2)
        def f(ripl,x,y): return ripl.sample('(+ %f %f)'%(x,y))

        proc_args_list = [ [10,20], [100,200] ]
        v.map_proc_list(f,proc_args_list)
        Out: [30,300]

        def f(ripl,x,y=1): return ripl.sample('(+ %f %f)'%(x,y))

        proc_args_list = [  [ [10],{'y':10} ],  [ [30],{} ] ]
        v.map_proc_list(f,proc_args_list,only_p_args=False)
        Out: [20,31]
        '''

        no_args = len(proc_args_list)
        assert 0 < no_args <= self.no_ripls, 'Either 0 argumentss or more arguments than ripls.'

        # map across local ripls (TODO? include: (self.local_seeds[i],proc_args_list[i]))
        if self.local_mode:
            arg_ripl = zip(proc_args_list, self.local_ripls[:no_args])
            if only_p_args:
                local_out = [proc(r,*args) for args,r in arg_ripl]
            else:
                local_out = [proc(r,*args,**kwargs) for (args,kwargs),r in arg_ripl]
            return local_out
        else:
            local_out = [None]*no_args

        # map across remote ripls
        no_args_per_engine = int(np.ceil(no_args/float(self.no_engines)))
        remote_out = []
        for i in range(self.no_engines):
            start=i*no_args_per_engine
            eng_args = proc_args_list[start: start + no_args_per_engine]
            if not eng_args: break
            eng_view = self.cli[i]
            eng_view.push({'mapped_proc_l':interactive(proc),'eng_args':eng_args})
            eng_view.push({'list_out':[]})

            @interactive
            def f(mrid,backend,eng_args,only_p_args):
                 arg_ripl = zip(eng_args, mripls[mrid][backend][:len(eng_args)])
                 if only_p_args:
                     list_out.extend( [mapped_proc_l(r,*args) for args,r in arg_ripl] )
                 else:
                     list_out.extend( [mapped_proc_l(r,*args,**kwargs) for (args,kwargs),r in arg_ripl] )

            eng_view.apply_sync(f,self.mrid,self.backend,eng_args,only_p_args)
            remote_out.extend(eng_view['list_out'])
            # NB: eng_args pushed but not needed. ALT VERSION
            # s1= 'eng_ripls= mripls[%i][%s][:len(eng_args)]'%(self.mrid,
            # eng_view.execute(s1)
            # @interactive
            # def f1():
            #     out = [proc_l(r,*args) for r,args in zip(eng_ripls,eng_args)]
            #     list_out.extend(out)
        ipython_inline()

        return remote_out if self.output=='remote' else local_out







    def snapshot(self, exp_list=(), did_labels_list=(),
                 plot=False, scatter=False, xlims_ylims=None,
                 plot_past_values=(),
                 sample_populations=None, repeat=None,
                 predict=True, logscore=False):

        '''Input: Sequence of Venture expressions (or dids/labels).
           Output: { expression: list of values of expression for each ripl }
                    (along with *self.ripls_info()*)
           Optional args:
             plot: Plot histogram of the snapshot values (for each expression).
             xlims_ylims: ( (xmin,xmax), (ymin,ymax) ), specify axes limits
                          to override automatic limits.
             logscore: Snapshot of logscore.'''


        if isinstance(did_labels_list,(int,str)):
            did_labels_list = [did_labels_list]
        else:
            did_labels_list = list(did_labels_list)
        if isinstance(exp_list,str):
            exp_list = [exp_list]
        else:
            exp_list = list(exp_list)

        plot_past_values = list(plot_past_values)

        plot_range = xlims_ylims

        if plot_range:
            assert isinstance(plot_range[0],(list,tuple)), 'xlims_ylims form: ( (xmin,xmax)[,(ymin,ymax)])'

        out = {'values':{},
               'total_transitions':self.total_transitions,
               'ripls_info': self.ripls_info() }


        # special options: (return before basic snapshot)
        if sample_populations:
            return self._sample_populations(exp_list,out, sample_populations,
                                            plot=plot, plot_range=plot_range)
        elif repeat:
            no_groups = self.no_local_ripls if self.output=='local' else self.no_ripls
            return self._sample_populations(exp_list, out, (no_groups,repeat),
                                            flatten=True, plot=plot,
                                            plot_range=plot_range)


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
            return self._plot_past_values(exp_list, out, plot_past_values,
                                         plot_range=plot_range)

        # logscore current must go after plot_past_values to avoid errors
        if logscore: out['values']['global_logscore']= self.get_global_logscore()

        if plot or scatter:
            out['figs'] = self._plot(out,scatter=scatter,plot_range=plot_range)


        return out


    def sample_populations(self,exp,no_groups,population_size,xlims_ylims=None):
        '''Input *exp* will be repeatedly sampled from (*population_size* times)
           for each group in *no_groups*. The expression *exp* should be
           stochastic.

           Example:
           mripl.assume('mean','(normal 0 100)')
           mripl.sample_populations('(normal mean 1)',4,30)'''
        return self.snapshot(exp_list = (exp,), plot=True,
                             sample_populations=(no_groups,population_size),
                             xlims_ylims=xlims_ylims)

    def _sample_populations(self,exp_list,out,groups_popsize,flatten=False,plot=False,plot_range=None):

        assert len(exp_list)==1, 'len(exp_list) != 1'
        exp = exp_list[0]
        no_groups,pop_size = groups_popsize

        ## maybe keep this for cases involving memoization
        # def pred_repeat_forget(r,exp,pop_size):
        #     vals=[r.predict(exp,label='snapsp_%i'%j) for j in range(pop_size)]
        #     [r.forget('snapsp_%i'%j) for j in range(pop_size)]
        #     return vals

        def batch_sample(ripl,exp,pop_size,syntax='church_prime'):
            if syntax=='church_prime':
                lst_string = '(list '+ ' '.join([exp]*pop_size) + ')'
            else:
                lst_string = 'list('+ ','.join([exp]*pop_size) + ')'
                
            return ripl.sample(lst_string)

        mrmap_values = self.map_proc(no_groups,batch_sample,exp,pop_size,self.syntax)

        if flatten: mrmap_values = lst_flatten(mrmap_values)

        out['values'][exp]=mrmap_values

        if not(plot): return out

        if plot and flatten: # Predictive (Repeat)
            fig,ax=plt.subplots(figsize=(6,3))
            ax.hist(mrmap_values, bins=20,alpha=.4, normed=True, color='m', histtype='stepfilled')
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
            all_vals=lst_flatten(mrmap_values)
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


    def compare_snapshots(self, list_snapshot_outputs ):
        '''Input: List of outputs from calls to *snapshot* for the same
                  expression.
           Output: Plots the snapshots on same axis.'''
        assert all ( [isinstance(el,dict) for el in list_snapshot_outputs] )
        return self.snapshot(plot_past_values = list_snapshot_outputs)


    def _plot_past_values(self, exp_list, out, past_values_list,plot_range):
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
        all_vals=lst_flatten(list_vals)
        xr=np.linspace(min(all_vals),max(all_vals),50)

        for count,past_vals in enumerate(list_vals):
            label='Prior [0]' if count==0 else 'Post [%i]'%count
            alpha = .9 - .1*(len(list_vals) - count )
            ax[0].hist( past_vals, bins=20,alpha=alpha,
                        normed=True,label=label)
            ax[1].plot(xr,gaussian_kde(past_vals)(xr),
                       alpha=alpha, label=label)

        [ ax[i].legend(loc='upper left',ncol=len(list_vals)) for i in range(2)]
        ax[0].set_title('Compare snapshots: %s (ripls= %i)' % (exp_name,self.no_ripls) )
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


    def _plot(self,snapshot,scatter=False,plot_range=None):
        '''Takes input from snapshot, checks type of values and plots accordingly.
        Plots are inlined on IPNB and output as figure objects.'''

        def draw_hist(vals,label,ax,plot_range=None):
            ax.hist(vals,alpha=.8)
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
                ax.set_xlim(plot_range[0])
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
                    figs.append(fig)
                else:
                    fig,ax = plt.subplots(figsize=(4,2))
                    draw_hist(vals,label,ax,plot_range=plot_range)
                    figs.append(fig)
            elif var_type in 'int':
                fig,ax = plt.subplots()
                draw_hist(vals,label,ax,plot_range=plot_range)
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

        if len(figs)>0: [f.tight_layout() for f in figs]
        return figs





# Utility functions for mripl and other functions
def lst_flatten(l): return [el for subl in l for el in subl]

def ipython_inline():
    '''Try to run ipython px cell magic on empty cell
    to display previously generated figs inline.'''
    try:
        ip=get_ipython()
        ip.run_cell_magic("px",'','pass') # display any figs inline
    except:
        pass


def mk_directives_string(ripl):
        di_string_lst = [directive_to_string(di) for di in ripl.list_directives() ]
        return '\n'.join(di_string_lst)

def display_directives(ripl_mripl,instruction='observe'):
    ## FIXME: add did and labels
    #v=ripl_mripl
    #mr=1  if isinstance(v,MRipl) else 0
    #di_list = v.local_ripls[0].list_directives() if mr else v.list_directives()

    di_list = ripl_mripl.list_directives()
    instruction_list = []
    for di in di_list:
        if di['instruction'] in instruction.lower():
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

def build_exp(exp):
    'Take expression from directive_list and build the Lisp string'
    if type(exp)==str:
        return exp
    elif type(exp)==dict:
        if exp['type']=='atom':
            return 'atom<%i>'%exp['value']
        elif exp['type']=='boolean':
            return str(exp['value']).lower()
        else:
            return str(exp['value'])
    else:
        return '('+ ' '.join(map(build_exp,exp)) + ')'



### Functions defined on MRipl objects

def mr_map_proc(mripl,no_ripls,proc,*proc_args,**proc_kwargs):
    '''Push procedure into engine namespaces. Use execute to map across ripls.
    if no_ripls==0, 'all' or >mripl.no_ripls, then maps across all.
    Maps proc across local ripls IFF in local_mode or mripl.output=="local".'''

    ## FIXME: should be able to supress stdout from local_ripls when in remote mode
    if no_ripls==0 or no_ripls=='all' or no_ripls>mripl.no_ripls:
        no_ripls = mripl.no_ripls
        no_local_ripls = mripl.no_local_ripls

    # map across local ripls
    if mripl.local_mode:
        local_out=[proc(r,*proc_args,**proc_kwargs) for i,r in enumerate(mripl.local_ripls) if i<no_ripls]
        return local_out
    else:
        local_out = [None]*no_ripls

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

    no_args = len(proc_args_list)
    assert no_args <= mripl.no_ripls, 'More arguments than ripls'

    # map across local ripls
    if mripl.local_mode:
        id_local_out=[]; local_out=[]
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
        return local_out
    else:
        local_out = [None]*no_args

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
    'args: ripl_mripl_name [,no_ripl_values_output]'
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
    pass






