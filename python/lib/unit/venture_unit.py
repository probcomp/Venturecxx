
# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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
import time, random
import numpy as np
from venture.lite.utils import FixedRandomness
from venture.ripl.utils import strip_types
from venture.shortcuts import make_puma_church_prime_ripl
from venture.shortcuts import make_lite_church_prime_ripl
mk_l_ripl = make_lite_church_prime_ripl
mk_p_ripl = make_puma_church_prime_ripl
from venture.venturemagics.ip_parallel import MRipl,build_exp
from history import History, Run, Series, historyOverlay,compareSampleDicts,filterDict,historyNameToValues

parseValue = strip_types


# TODO

# 0. FIXME: If Analytics is given a ripl with assumes/observes, it uses list_directives
# to extract them. This leads to the Python dict form of Venture values. For example,
# the symbol for an assume will be {'type':'symbol','value':'theta'}. Analytics then
# tries to build dicts that have these dicts as keys. Unit tests don't catch this
# because they specify *assumes* as an argument to Analytics, rather than implicitly
# by handing it a ripl and no *assumes* optional keyword argument.
# Fix is to switch from using list_directives to using the same unparsing as print_directive
# (note that execute_program doesn't play well t


# 1. simpleInfer option for runFromConditional avoids using sweeps
# and so gives fine-grained control of inference transitions.
# Currently this is only documented in runFromConditional doc-string.
# It doesn't have unit tests.

# 2. Proper integration of persistent/mutable mripl with all analytics
# options.

# 3. More tests for unit/analytics interaction.

# 4. Way of avoiding long names for analytics plots.



# PLAN: Persistent Ripls for Analytics

# benefits:
# 1. can add observes,assumes,infers at any time without
# going through analytics and then return to analytics object
# for more extensive inference/plotting etc.

# 2. after lots of inference, get back your mripl/ripl for more interaction.

# 3. simplify using analytics with custom interleaving of observe/infer:
#    e.g.
# for t in enumerate(observes):
#     model.updateObseves(observes[t])
#     history[t] = model.runFromConditional(infer=InferProg)
# then on final one you get the mripl back

# to implement this:
# currently we generate an mripl for runFromConditional. instead we should
# should just map runFromCond across the ripls (letting the runs be determined
# by the number of ripls). simplest version would avoid all the load/reload
# of assumes/observes stuff. we need that for runConditionedFromPrior, but one would simplify
# run from conditional by isolating it from that code (with v little cost).
# 1. input mripl (assumes/observes are extracted and stored)
# 2.you can updateObserves/queryexps/assumes as needed
# 3.runFromCond map_procs analytics runOnceFromCond onto each ripl in self.mripl and runs over combined
# 4.output history and pointer to self.mripl


# IMPLENTATION
# Done a crude implementation that works for runFromConditional. Currently

# prevents Analytics from ever clearing the ripl, which prevents runConditionalFromPrior. Whole point of this
# is to allow filtering/incremental inference with Analytics.
# So running on synthetic data from prior wouldn't in any case be doing the same

# prevent Analytics from ever clearing the ripl, which prevents run from prior. Whole point of this
# is to allow filtering/incremental inference with Analytics.
# So running on synth data from prior won't be doing the same

# inference procedure as an incremental one. ...


def directive_split(d):
    'Splits directive from *list_directives* into components'
    ## FIXME: replace Python values with strings for Venture.
    if d['instruction']=='assume':
        return (d['symbol']['value'], build_exp(d['expression']) )
    elif d['instruction']=='observe':
        return (build_exp(d['expression']), d['value'])
    elif d['instruction']=='predict':
        return build_exp(d['expression'])

def record(value):
    'Return ripl value if type is in approved set. SPs are not returned.'
    return value['type'] in {'boolean', 'real', 'number', 'atom', 'count', 'array', 'simplex'}


class VentureUnit(object):
    '''Construct batch experiments. Run diagnostics and analytics on all parameter
    settings given by *parameters* dict.'''
    ripl = None
    parameters = {}
    assumes = []
    observes = []
    queryExps = []

    # Register an assume.
    def assume(self, symbol, expression):
        self.assumes.append((symbol, expression))

    # Override to create generative model.
    def makeAssumes(self): pass

    # Register an observe.
    def observe(self, expression, literal):
        self.observes.append((expression, literal))

    # Override to constrain model on data.
    def makeObserves(self): pass

    # Register a queryExp.
    def queryExp(self, expression):
        self.queryExps.append(expression)

    def makeQueryExps(self): pass

    # Masquerade as a ripl.
    def clear(self):
        self.assumes = []
        self.observes = []

    # Initializes parameters, generates the model, and prepares the ripl.
    def __init__(self, ripl, parameters=None):
        if parameters is None: parameters = {}
        self.ripl = ripl

        # FIXME: make consistent with Analytics
        self.parameters = parameters.copy()
        if 'venture_random_seed' not in self.parameters:
            self.parameters['venture_random_seed'] = self.ripl.get_seed()
        else:
            self.ripl.set_seed(self.parameters['venture_random_seed'])


        self.assumes = []
        self.makeAssumes()

        self.observes = []
        self.makeObserves()

        self.queryExps = []
        self.makeQueryExps()

        self.analyticsArgs = (self.ripl,)
        self.analyticsKwargs = dict(assumes=self.assumes, observes=self.observes,
                                    parameters=self.parameters, queryExps=self.queryExps)

    def getAnalytics(self,ripl_mripl,mutateRipl=False):
        '''Create Analytics object from assumes, observes and parameters.
           Use *ripl_mripl* to choose between ripls/mripl and backend.
           Use *mutateRipl* to have Analytics do inference by mutating
           the ripl/mripl rather than copying it.
        '''

        kwargs = self.analyticsKwargs.copy()
        kwargs['mutateRipl'] = mutateRipl

        return Analytics(ripl_mripl, **kwargs)


    def sampleFromJoint(self,*args,**kwargs):
        a = Analytics(*self.analyticsArgs, **self.analyticsKwargs)
        return a.sampleFromJoint(*args,**kwargs)

    def runFromJoint(self,*args,**kwargs):
        a = Analytics(*self.analyticsArgs, **self.analyticsKwargs)
        return a.runFromJoint(*args,**kwargs)

    def computeJointKL(self,*args,**kwargs):
        a = Analytics(*self.analyticsArgs, **self.analyticsKwargs)
        return a.computeJointKL(*args,**kwargs)

    def runFromConditional(self, *args, **kwargs):
        a = Analytics(*self.analyticsArgs, **self.analyticsKwargs)
        return a.runFromConditional(*args,**kwargs)

    def runConditionedFromPrior(self, *args, **kwargs):
        a = Analytics(*self.analyticsArgs, **self.analyticsKwargs)
        return a.runConditionedFromPrior(*args,**kwargs)

    def generateDataFromPrior(self, *args, **kwargs):
        a = Analytics(*self.analyticsArgs, **self.analyticsKwargs)
        return a.generateDataFromPrior(*args,**kwargs)


class Analytics(object):

    def __init__(self, ripl_mripl, assumes=None,observes=None,queryExps=None,
                 parameters=None, mutateRipl=False):
        '''Methods for analyzing and debugging inference on a model.

        Arguments
        ---------
        ripl :: ripl (Puma or Lite)
            Inference is done on a fresh ripl with same backend. If no
            *assumes* are specified, assumes are extracted from ripl.

        assumes :: [(sym,exp)]
            List of assume pairs. If not None, replace ripl assumes.

        observes  :: [(exp,literal)]
            List of observe pairs. Values are used by *runFromConditional* as
            data. Expressions are used by *geweke* and *runConditionedFromPrior*.

        queryExps :: [exp]
            List of expressions which are evaluated and recorded at every sweep
            of inference (in addition to symbols in assumes).

        parameters :: {string: a}
            The optional *venture_random_seed* parameter can be used to set the
            seed for Analytics inference. All other parameters are ignored for inference
            and are simply stored in output History objects.

        mutateRipl :: bool
            If False, the input *ripl_mripl* is not mutated by Analytics and is just
            a source for directives. All inference takes place on freshly created
            ripls/mripls.

            If True, enables inference via *runFromConditional* on the ripl/mripl given
            by *ripl_mripl*. Not tested for anything but *runFromConditional*.'''

        assert not(assumes is None and observes is not None),'No *observes* without *assumes*.'
        assert queryExps is None or isinstance(queryExps,(list,tuple)), 'QueryExps must be list or tuple'

        if hasattr(ripl_mripl,'no_ripls'): # test for ripl vs. MRipl
            ripl=ripl_mripl.local_ripls[0] # only needed because of set_seed
            self.mripl = True
        else:
            ripl = ripl_mripl
            self.mripl = False

        # make fresh ripl with same backend as input ripl
        self.backend = ripl.backend()
        self.ripl = mk_p_ripl() if self.backend=='puma' else mk_l_ripl()

        directives_list = ripl.list_directives(type=True)


        if assumes is not None:
            self.assumes = assumes
            self.observes = list(observes) if observes is not None else []
        else:
            assumes = [d for d in directives_list if d['instruction']=='assume']
            self.assumes = map(directive_split,assumes)
            observes = [d for d in directives_list if d['instruction']=='observe']
            self.observes = map(directive_split,observes)

            # if REMOVE_SOME_TYPES_FROM_SYMBOLS:
            #   clean_assumes = []
            #   clean_observes = []

            #   for sym,exp in self.assumes:
            #       if isinstance(sym,dict) and 'value' in sym:
            #           clean_assumes.append( (sym['value'], exp) )
            #       else:
            #           clean_assumes.append( (sym, exp) )

            #   # for exp,value in self.observes:
            #   #     if isinstance(value,dict) and 'value' in value:
            #   #         clean_observes.append( (exp, value['value']) )
            #   #     else:
            #   #         clean_observes.append( (exp, value) )

            #   self.assumes = clean_assumes
            #   #self.observes = clean_observes


        self.queryExps=[] if queryExps is None else list(queryExps)

        if parameters is None: parameters = {}
        self.parameters = parameters.copy()
        if 'venture_random_seed' in self.parameters:
            self.ripl.set_seed(self.parameters['venture_random_seed'])
        else:
            self.parameters['venture_random_seed'] = 1 ## UNKNOWN SEED

        # make fresh mripl with same backend as input mripl

        ## FIXME: should have an attribute for *mripl_mode* and then an
        ## attribute pointing to actual mripl

        if self.mripl:
            self.mripl = MRipl(ripl_mripl.no_ripls,
                               backend = ripl_mripl.backend,
                               local_mode = ripl_mripl.local_mode)
            for sym,exp in self.assumes: self.mripl.assume(sym,exp)
            for exp,lit in self.observes: self.mripl.observe(exp,lit)

            self.backend = self.mripl.backend
            if self.mripl.local_mode is False:
                self.mripl.dview.execute('from venture.unit import Analytics')
            self.updateQueryExps()

        if self.ripl:
            # TODO Does this apply to mripls too?
            for (name, sp) in ripl.sivm.core_sivm.engine.foreign_sps.iteritems():
                self.ripl.bind_foreign_sp(name, sp)

        # Initialization for mutable ripl or MRipl

        if mutateRipl:
            self.muRipl = True

            if ripl_mripl.list_directives() == []:
                if not self.mripl:
                    for sym,exp in self.assumes: self.ripl.assume(sym,exp)
                    for exp,lit in self.observes: self.ripl.observe(exp,lit)
                    string = 'ripl'
                else:
                    string = 'mripl'
                print 'Analytics created new persistent %s'%string

            else:
                self.ripl = ripl_mripl
                if self.mripl:
                    self.mripl = ripl_mripl
                    string = 'mripl'
                else:
                    string = 'ripl'
                print 'Analytics will mutate the input %s'%string
        else:
            self.muRipl = False



    def updateObserves(self,newObserves=None,removeAllObserves=False):
        '''Extend list of observes or empty it.
           Input: newObserves :: [(exp,literal)], removeAllObserves :: bool.'''

        # add assert about getting form of input right

        if removeAllObserves:
            self.observes = []
        if newObserves is not None:
            assert not isinstance(newObserves,str), '*newObserves* is set of strings, not string'
            self.observes.extend( Observes )

        if self.muRipl:
            ripl = self.mripl if self.mripl else self.ripl
            [ripl.observe( exp, value ) for exp,value in newObserves]
            string='mripl' if self.mripl else 'ripl'
            print 'Observes applied to persistent %s.'%string

    def updateQueryExps(self,newQueryExps=None,removeAllQueryExps=False):
        '''Extend list of query expressions or empty it.
           Input: newQueryExps :: [(exp)], removeAllQueryExps :: bool.'''
        if removeAllQueryExps:
            self.queryExps = []
        if newQueryExps is not None:
            assert not isinstance(newObserves,str), '*newQueryExps* should be a set of strings, not a string'
            self.queryExps.extend( newQueryExps )
        # always update mripl engines with whatever is current self.queryExps
        if self.mripl and self.mripl.local_mode is False:
            self.mripl.dview.push({'queryExps':self.queryExps})


    def switchBackend(self,newBackend):
        'Switch backend while maintaining assumes and observes'
        ## FIXME make mripl compatible via mripl.switch_backends

        self.backend = newBackend
        self.ripl = mk_p_ripl() if self.backend=='puma' else mk_l_ripl()
        # self.ripl.set_seed(seed)


    def _clearRipl(self):
	# Record the foreign sps
        sps = [(name, sp) for name, sp in self.ripl.sivm.core_sivm.engine.foreign_sps.iteritems()]

        if self.muRipl:
            assert False,'Attempt to clear mutable ripl/mripl'
        else:
            self.ripl.clear()

	# Reload them
        for (name, sp) in sps:
            self.ripl.bind_foreign_sp(name, sp)

    def _loadAssumes(self, prune=True):

        assumeToDirective = {}

        for (symbol, expression) in self.assumes:
            from venture.exception import VentureException
            try:
                value = self.ripl.assume(symbol, expression, label=symbol, type=True)
            except VentureException as e:
                print expression
                raise e
            assumeToDirective[symbol] = symbol
        return assumeToDirective


    def _assumesFromRipl(self):

        assumeToDirective = {}
        for directive in self.ripl.list_directives(type=True):
            if directive["instruction"] == "assume":
                assumeToDirective[directive["symbol"]] = directive["directive_id"]
        return assumeToDirective


    def _loadObservesAsPredicts(self, track=0, prune=False):
        predictToDirective = {}
        for (index, (expression, _)) in enumerate(self.observes):
            #print("self.ripl.predict('%s', label='%d')" % (expression, index))
            label = 'observe_%d' % index
            value = self.ripl.predict(expression, label=label, type=True)
            predictToDirective[index] = label

        # choose a random subset to track; by default all are tracked
        if track < 0:
            return predictToDirective
        track = min(track, len(predictToDirective))
        with FixedRandomness():
            # TODO: Use a sane way to make sure the same predicts are tracked
            random.seed(self.parameters['venture_random_seed'])
            predictToDirective = dict(random.sample(predictToDirective.items(), track))

        return predictToDirective

    def _loadObserves(self, data=None):
        'If data not None, replace values in self.observes'
        for (index, (expression, literal)) in enumerate(self.observes):
            datum = literal if data is None else data[index]
            self.ripl.observe(expression, datum)

    # Loads the assumes and changes the observes to predicts.
    # Also picks a subset of the predicts to track (by default all are tracked).
    # Prunes non-scalar values, unless prune=False.
    # Does not reset engine RNG.
    def loadModelWithPredicts(self, track=-1, prune=True):
        self._clearRipl()

        assumeToDirective = self._loadAssumes(prune=prune)
        predictToDirective = self._loadObservesAsPredicts(track=track, prune=prune)

        return (assumeToDirective, predictToDirective)

    # Updates recorded values after an iteration of the ripl.
    def updateValues(self, keyedValues, keyToDirective=None):


        if keyToDirective is None: # queryExps are sampled and have no dids
            for key,values in keyedValues.items():
                values.append(self.ripl.sample(key,type=True))
            return

        for (key, values) in keyedValues.items():
            if key not in keyToDirective: # we aren't interested in this series
                del keyedValues[key]
                continue

            value = self.ripl.report(keyToDirective[key], type=True)

            if len(values) == 0:
                values.append(value)
            else:
                if value['type'] == values[0]['type']:
                    values.append(value)
                else: # directive returned different type; discard series
                    del keyedValues[key]


    # Gives a name to an observe directive.
    def nameObserve(self, index):
        return 'observe[' + str(index) + '] ' + self.observes[index][0]

    # Sample iid from joint distribution (observes turned into predicts).
    # A random subset of predicts, assumes, and queryExps are tracked.
    # Returns a History object that represents exactly one Run.
    def sampleFromJoint(self, samples, track=5, verbose=False, name=None,
                        mriplLocalMode=True, mriplTrackObserves=False,
                        useMRipl=False):
        '''If self.mripl and useMRipl, samples come from a big MRipl:
        MRipl(samples,local_mode=mriplLocalMode). MRipl runs in local_mode
        by default for speed. Set *mriplTrackObserves* to True to record
        observes. If self.mripl is False, loops over a single ripl, tracking
        *track* random observes.'''

        def mriplSample():
            assumedValues={}
            predictedValues={}
            queryExpsValues={}

            v = MRipl(samples, backend=self.backend, local_mode=mriplLocalMode)
            for sym,exp in self.assumes: v.assume(sym,exp,label=sym)

            observeLabels=[self.nameObserve(i) for i,_ in enumerate(self.observes)]
            if mriplTrackObserves is False:
                observeLabels = []

            for (exp,_),name in zip(self.observes,observeLabels):
                v.predict(exp,label=name)

            for (sym,_) in self.assumes:
                assumedValues[sym] = v.report(sym,type=True)
            for name in observeLabels:
                predictedValues[name] = v.report(name,type=True)
            for exp in self.queryExps:
                queryExpsValues[exp] = v.sample(exp,type=True)

            logscores=v.get_global_logscore()

            return assumedValues,predictedValues,queryExpsValues,logscores


        def riplSample():
            assumedValues = {symbol:  [] for (symbol, _) in self.assumes}
            predictedValues = {index: [] for index in range(len(self.observes))}
            queryExpsValues = {exp: [] for exp in self.queryExps}
            logscores = []
            for i in range(samples):
                if verbose:
                    print "Generating sample " + str(i+1) + " of " + str(samples)

                (assumeToDirective,predictToDirective) = self.loadModelWithPredicts(track)
                logscores.append(self.ripl.get_global_logscore())

                self.updateValues(assumedValues,keyToDirective=assumeToDirective)
                self.updateValues(predictedValues,keyToDirective=predictToDirective)
                self.updateValues(queryExpsValues, keyToDirective=None)

            return assumedValues,predictedValues,queryExpsValues,logscores


        tag = 'sample_from_joint' if name is None else name + '_sample_from_joint'
        history = History(tag, self.parameters)
        out = mriplSample() if self.mripl and useMRipl else riplSample()

        assumedValues,predictedValues,queryExpsValues,logscores = out

        if self.mripl:
            for (name,values) in predictedValues.iteritems():
                parsedValues = map(parseValue, values)
                history.addSeries(name,values[0]['type'],'iid',parsedValues)
        else:
            for (index, values) in predictedValues.iteritems():
                name = self.nameObserve(index)
                parsedValues = map(parseValue, values)
                history.addSeries(name,values[0]['type'],'iid',parsedValues)


        for (symbol, values) in assumedValues.iteritems():
            history.addSeries(symbol,values[0]['type'], 'i.i.d.', map(parseValue, values))

        for (exp, values) in queryExpsValues.iteritems():
            history.addSeries(exp,values[0]['type'], 'i.i.d.', map(parseValue, values))

        history.addSeries('logscore','number', 'i.i.d.', logscores)

        return history


    def _runInfer(self,infer=None,stepSize=1):
        if infer is None:
            self.ripl.infer(stepSize)

        elif isinstance(infer, str):
            self.ripl.infer(infer)

        else: # need to be careful passing function with MRipl
            infer(self.ripl, stepSize)


    # iterates until (approximately) all random choices have been resampled
    def sweep(self,infer=None,**kwargs):
        simpleInfer = kwargs.get('simpleInfer',None)
        stepSize = kwargs.get('stepSize',1)
        if simpleInfer:
            self._runInfer(infer,stepSize)
            return stepSize

        iterations = 0
        get_entropy_info = self.ripl.sivm.core_sivm.engine.get_entropy_info

        # if #unconstrainted_random_choices stays fixed after infer(step)
        # then we do #iterations=#u_r_c. if #u_r_c grows after infer, we do
        # another step (with larger stepsize) and repeat.
        while iterations < get_entropy_info()['unconstrained_random_choices']:
            step = get_entropy_info()['unconstrained_random_choices']
            self._runInfer(infer,step)
            iterations += step

        return iterations



    def _runRepeatedly(self, f, tag, runs=3, verbose=False, profile=False,
                       useMRipl=True,**kwargs):
        history = History(tag, self.parameters)

        if self.mripl and useMRipl and not self.muRipl:
            v = MRipl(runs,backend=self.backend,local_mode=self.mripl.local_mode)

            def sendf(ripl,fname,modelTuple,**kwargs):
                seed = ripl.sample('(uniform_discrete 0 (pow 10 5))') ## FIXME HACK
                params=dict(venture_random_seed=seed)
                assumes,observes,queries = modelTuple
                model = Analytics(ripl,assumes=assumes,observes=observes,
                                  queryExps=queries,parameters=params)
                return getattr(model,fname)(label='seed:%s'%seed,**kwargs)

            modelTuple=(self.assumes,self.observes,self.queryExps)
            results = v.map_proc('all',sendf, f.func_name, modelTuple,**kwargs)

            for r in results[:runs]: history.addRun(r)

            return history


        if self.mripl and useMRipl and self.muRipl:
            def sendf(ripl,fname,**kwargs):
                seed = ripl.sample('(uniform_discrete 0 (pow 10 5))') ## FIXME HACK
                model = Analytics(ripl,mutateRipl=True)
                return getattr(model,fname)(label='seed:%s'%seed,**kwargs)

            results = self.mripl.map_proc('all',sendf, f.func_name,**kwargs)
            for r in results[:runs]: history.addRun(r)
            return history


        # single ripl
        for run in range(runs):
            if verbose:
                print "Starting run " + str(run) + " of " + str(runs)

            res = f(label="run %s" % run, verbose=verbose, **kwargs)
            history.addRun(res)

        if profile:
            history.profile = Profile(self.ripl)
        return history


    # Runs inference on the joint distribution (observes turned into predicts).
    # A random subset of the predicts are tracked along with the assumed variables.
    # If profiling is enabled, information about random choices is recorded.
    def runFromJoint(self, sweeps, name=None, **kwargs):
        tag = 'run_from_joint' if name is None else name + '_run_from_joint'
        return self._runRepeatedly(self.runFromJointOnce, tag, sweeps=sweeps, **kwargs)

    def runFromJointOnce(self, track=5, **kwargs):
        (assumeToDirective, predictToDirective) = self.loadModelWithPredicts(track)
        return self._collectSamples(assumeToDirective, predictToDirective, **kwargs)

    # Returns a History reflecting exactly one Run.
    def collectStateSequence(self, name=None, profile=False, **kwargs):
        assumeToDirective = self._assumesFromRipl()

        tag = 'run_from_conditional' if name is None else name + '_run_from_conditional'
        history = History(tag, self.parameters)
        history.addRun(self._collectSamples(assumeToDirective, {}, label="interactive", **kwargs))
        if profile:
            history.profile = Profile(self.ripl)
        return history

    def _collectSamples(self, assumeToDirective=None, predictToDirective=None, sweeps=100, label=None, verbose=False, infer=None, force=None, **kwargs):
        if assumeToDirective is None:
            assumeToDirective = self._assumesFromRipl()
        if predictToDirective is None:
            predictToDirective = {}
        answer = Run(label, self.parameters)

        assumedValues = {symbol : [] for symbol in assumeToDirective}
        predictedValues = {index: [] for index in predictToDirective}
        queryExpsValues = {exp: [] for exp in self.queryExps}

        sweepTimes = []
        sweepIters = []
        logscores = []

        if verbose:
            print "Using inference program"
            print infer
        for sweep in range(sweeps):
            if verbose:
                print "Running sweep " + str(sweep+1) + " of " + str(sweeps)

            # FIXME: use timeit module for better precision
            start = time.time()
            iterations = self.sweep(infer=infer, **kwargs)
            end = time.time()

            sweepTimes.append(end-start)
            sweepIters.append(iterations)
            logscores.append(self.ripl.get_global_logscore())

            self.updateValues(assumedValues,keyToDirective=assumeToDirective)
            self.updateValues(predictedValues,keyToDirective=predictToDirective)
            self.updateValues(queryExpsValues,keyToDirective=None)

        answer.addSeries('sweep time (s)', 'count', Series(label, sweepTimes))
        answer.addSeries('sweep_iters', 'count', Series(label, sweepIters))
        answer.addSeries('logscore', 'number', Series(label, logscores))

        for (symbol, values) in assumedValues.iteritems():
            answer.addSeries(symbol, values[0]['type'], Series(label, map(parseValue, values)))

        for (index, values) in predictedValues.iteritems():
            answer.addSeries(self.nameObserve(index), values[0]['type'], Series(label, map(parseValue, values)))

        for (exp, values) in queryExpsValues.iteritems():
            answer.addSeries(exp,values[0]['type'], Series(label, map(parseValue, values)))

        return answer


    def runFromConditional(self, sweeps, name=None, data=None,**kwargs):
        '''Runs inference on the model conditioned on data.
           By default data is values of self.observes.

           To avoid using the *sweep* method for inference, set
           *simpleInfer* to True. This will record after
           each call to your inference program. (You can thin the number
           of samples recorded using the *transitions* argument for the
           inference program).

           Example:
           > m.runFromConditional(100,infer='(mh default one 5)',simpleInfer=True)

           This will collect 100 samples with 5 MH transitions between samples.


           Arguments
           ---------
           sweeps :: int
               Total number of iterations of inference program. Values are
               recorded after every sweep.
           simpleInfer :: bool [optional]
               If True, run inference without attempting to hit all variables
               before recording. Use optional *stepSize* argument to specify
               numbers of steps between recording.
           runs :: int  [optional]
               Number of parallel chains for inference. Default=3.
           infer :: string | function on ripl
               Inference program.
           name :: string
               Label this set of runs for output History and plots.
           data :: [values]
               List of values that replace values in self.observes for this
               inference run only.
           verbose :: bool
               Display start of runs and sweeps.

           Returns
           -------
           history :: History
               history.History with nameToSeries dictionary of runs*Series
               for each recorded expression.
           ripl :: ripl
               Pointer to self.ripl, i.e. a ripl with same backend as given to
               constructor, mutated by assumes,observes (with values given by
               data) and inference. If runs>1, it's ripl after last run.'''

        tag = 'run_from_conditional' if name is None else name + '_run_from_conditional'

        history = self._runRepeatedly(self.runFromConditionalOnce,
                                      tag, data=data, sweeps=sweeps, **kwargs)
        ## FIXME ensure observe values are parsed (not typed)

        if data is not None:
            data = [(exp,datum) for (exp,_),datum in zip(self.observes,data)]
        else:
            data = self.observes
        history.addData(data)

        return (history,self.ripl) if not self.mripl else (history,self.mripl)


    def runFromConditionalOnce(self, data=None, force=None, **kwargs):
        if not self.muRipl:
            self._clearRipl()
            assumeToDirective = self._loadAssumes()
            self._loadObserves(data)
        else:
            assumeToDirective = None

        if force is not None:
            for symbol,value in force.iteritems():
                self.ripl.force(symbol,value)

        # note: we loadObserves, but predictToDirective arg = {}
        # so we are not collecting sample of the observes here.
        return self._collectSamples(assumeToDirective, {}, **kwargs)



    def testFromPrior(self,noDatasets,sweeps,**kwargs):
        ## TODO implement this. currently buggy.

        randRipl = np.random.randint(0,self.mripl.no_ripls)
        force={}

        for symbol,_ in self.assumes:
            value = self.mripl.sample(symbol)[randRipl]
            if isinstance(value,(int,float)): force[symbol]=value

        def fromPrior(r,sweeps,queryExps,force=None,**kwargs):
            model = Analytics(r,queryExps=queryExps)
            h,_ = model.runConditionedFromPrior(sweeps, force=force,
                                                runs=1,**kwargs)
            return h

        histories = self.mripl.map_proc(noDatasets, fromPrior,
                                sweeps, self.queryExps, force=None, **kwargs)

        pairs = zip(['Ripl%i'%i for i in range(noDatasets)],histories)
        historyOV = historyOverlay('testFromPrior',pairs)

        return historyOV, self.mripl



    # Run inference conditioned on data generated from the prior.
    def runConditionedFromPrior(self, sweeps, verbose=False, **kwargs):
        ## FIXME: add docstring describing groundtruth and outputting ripl.

        (data, groundTruth) = self.generateDataFromPrior(verbose=verbose)

        history,_ = self.runFromConditional(sweeps, data=data, verbose=verbose, **kwargs)
        history.addGroundTruth(groundTruth,sweeps) #sweeps vs. totalSamples
        history.label = 'run_conditioned_from_prior'

        return (history,self.ripl) if not self.mripl else (history,self.mripl)



    def generateDataFromPrior(self, verbose=False):
        if verbose:
            print 'Generating data from prior'

        (assumeToDirective,predictToDirective) = self.loadModelWithPredicts(prune=False)
        data=[]
        for i,_ in enumerate(self.observes):
            data.append(self.ripl.report(predictToDirective[i],type=True))

        assumedValues = {}
        for (symbol, directive) in assumeToDirective.iteritems():
            value = self.ripl.report(directive, type=True)
            assumedValues[symbol] = value

        queryExpsValues = {}
        for exp in self.queryExps:
            value = self.ripl.sample(exp,type=True)
            queryExpsValues[exp] = value

        groundTruth = assumedValues.copy() # store groundTruth as {exp:value}
        groundTruth.update(queryExpsValues.copy())

        return (data, groundTruth)


    # Computes the KL divergence on i.i.d. samples from the prior and inference on the joint.
    # Returns the sampled history, inferred history, and history of KL divergences.
    def computeJointKL(self, sweeps, samples, track=5, runs=3, verbose=False, name=None, infer=None):
        sampledHistory = self.sampleFromJoint(samples, track, verbose, name=name)
        inferredHistory = self.runFromJoint(sweeps, track=track, runs=runs, verbose=verbose, name=name, infer=infer)

        tag = 'kl_divergence' if name is None else name + '_kl_divergence'
        klHistory = History(tag, self.parameters)

        for (name, seriesList) in inferredHistory.nameToSeries.iteritems():
            if name not in sampledHistory.nameToSeries: continue
            if sampledHistory.nameToType[name] not in {'number'}: continue


            for inferredSeries in seriesList:
                sampledSeries = sampledHistory.nameToSeries[name][0]

# KL between all fwd samples and inferredSeries samples up to index
# why not combine inferred series into snapshots?
## FIXME: note that currently one of runs is not appearing
                klValues = [computeKL(sampledSeries.values, inferredSeries.values[:index+1]) for index in range(sweeps)]

                klHistory.addSeries('KL_' + name,'number', inferredSeries.label, klValues, hist=False)

        return (sampledHistory, inferredHistory, klHistory)



    def gewekeTest(self, samples, infer=None, plot=True, track=5, names=None,
                   useMRipl=False, mriplTrackObserves=False, compareObserves=False):
        '''Geweke-style Test. Use *names* to only analyse samples for names.
           Use *compareObserves* to specify whether to analyse observes. '''

        if useMRipl:
            fh= self.sampleFromJoint(samples,mriplTrackObserves=mriplTrackObserves,
                                     useMRipl=True)
            ih= self.runFromJoint(samples, infer=infer, runs=1, useMRipl=True)
        else:
            fh = self.sampleFromJoint(samples, track=track, useMRipl=False)
            ih = self.runFromJoint(samples, track=track, infer=infer, runs=1, useMRipl=False)

        forwardHistory,inferHistory = fh,ih
        ## FIXME: should be able to take multiple runs and flatten them
        #  inferHistory = flattenRuns(inferHistory)

        # convert history objects
        hs = (forwardHistory,inferHistory)
        labels=('Forward iid','Inference')
        dicts = map(historyNameToValues,hs)

        # filter on observes and names
        if compareObserves is False:
            names = dicts[0].keys()
            obsKeys = [n for n in names if 'observe' in str(n)]
            dicts=[filterDict(d,ignore=obsKeys) for d in dicts]

        if names is not None:
            dicts=[filterDict(d,keep=names) for d in dicts]

        compareReport = compareSampleDicts(dicts,labels,plot=plot)

        gewekeStr='''
        Geweke-style Test of Inference:
        Compare iid (forward) samples from joint to dependent
        samples from inference (*observes* changed to *predicts*)
        -------------\n\n'''
        compareReport.reportString = gewekeStr + compareReport.reportString

        return forwardHistory,inferHistory,compareReport






# Reads the profile data from the ripl.
# Returns a map from (random choice) addresses to info objects.
# The info contains the trials, successes, acceptance_rate, proposal_time, and source_location.
class Profile(object):
    def __init__(self, ripl):
        random_choices = ripl.profiler_list_random_choices()
        self.addressToInfo = {}
        self.locationToInfo = {}

        for address in random_choices:
            info = object()
            info.address = address

            acceptance = self.ripl.profiler_get_acceptance_rate(address)
            info.trials = acceptance[0]
            info.successes = acceptance[1]
            info.acceptance_rate = info.successes / info.trials

            info.proposal_time = self.ripl.profiler_get_proposal_time(address)

            info.source_location = self.ripl.profiler_address_to_source_code_location()

            self.addressToInfo[address] = info

            if info.proposal_time not in self.locationToAddress:
                self.locationToAddress[info.proposal_time] = []

            self.locationToAddress[info.proposal_time].append(info)

        # aggregates multiple info objects into one
        def aggregate(infos):
            agg = object()

            for attr in ['trials', 'successes', 'proposal_time']:
                setattr(agg, attr, sum([getattr(info, attr) for info in infos]))

            agg.acceptance_rate = agg.successes / agg.trials

            return agg

        self.locationToAggregate = dict([(location, aggregate(infos)) for (location, infos) in self.locationToInfo.items()])

    # The [5] longest
    def hotspots(self, num=5):
        hot = sorted(self.addressToInfo.values(), key=lambda info: info.proposal_time, reverse=True)
        return hot[:num]

    def coldspots(self, num=5):
        cold = sorted(self.addressToInfo.values(), key=lambda info: info.acceptance_rate)
        return cold[:num]

import math

# Approximates the KL divergence between samples from two distributions.
# 'reference' is the "true" distribution
# 'approx' is an approximation to 'reference'
def computeKL(reference, approx, numbins=20):

    # smooths out a probability distribution function
    def smooth(pdf, amt=0.1):
        return [(p + amt / len(pdf)) / (1.0 + amt) for p in pdf]

    mn = min(reference + approx)
    mx = max(reference + approx)

    refHist = np.histogram(reference, bins=numbins, range = (mn, mx), density=True)[0]
    apxHist = np.histogram(approx, bins=numbins, range = (mn, mx), density=True)[0]

    refPDF = smooth(refHist)
    apxPDF = smooth(apxHist)

    kl = 0.0

    for (p, q) in zip(refPDF, apxPDF):
        kl += math.log(p/q) * p * (mx-mn) / numbins

    return kl













