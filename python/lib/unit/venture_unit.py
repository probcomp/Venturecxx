# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
import time, random
import numpy as np
from venture.ripl.ripl import _strip_types
from venture.venturemagics.ip_parallel import MRipl,mk_p_ripl,mk_l_ripl,mr_map_proc
from venture.venturemagics.ip_parallel import * ## FIXME:
from IPython.parallel.util import interactive
from history import History, Run, Series, historyOverlay
parseValue = _strip_types

## possible addition
# analytics mutates the ripl you give as input.
# assumes and observes are extracted as before.
# runFromConditionalOnce: you just do the infer.
# assumes can be recorded in the same way.

# this way, simple mripl map would allow us 
# to output mripl without need for serializing ripls.

# [for run from prior, you need to reload assumes.]


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


def directive_split(d):
    'Splits directive from *list_directives* into components'
    ## FIXME: replace Python values with strings for Venture.
    if d['instruction']=='assume':
        return (d['symbol'], build_exp(d['expression']) ) 
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

    # Masquerade as a ripl.
    def clear(self):
        self.assumes = []
        self.observes = []

    # Initializes parameters, generates the model, and prepares the ripl.
    def __init__(self, ripl, parameters=None):
        if parameters is None: parameters = {}
        self.ripl = ripl

        # FIXME: make consistent with analytics
        self.parameters = parameters.copy()
        if 'venture_random_seed' not in self.parameters:
            self.parameters['venture_random_seed'] = self.ripl.get_seed()
        else:
            self.ripl.set_seed(self.parameters['venture_random_seed'])

        
        self.assumes = []
        self.makeAssumes()

        self.observes = []
        self.makeObserves()
        
        self.analyticsArgs = (self.ripl,)
        self.analyticsKwargs = dict(assumes=self.assumes, observes=self.observes,
                           parameters=self.parameters)

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


class Analytics(object):

    def __init__(self, ripl_mripl, assumes=None,observes=None,queryExps=None,
                 parameters=None):
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
            FIXME explain'''
 
        assert not(assumes is None and observes is not None),'No *observes* without *assumes*.'
        assert queryExps is None or isinstance(queryExps,(list,tuple))

        if isinstance(ripl_mripl,MRipl):
            ripl=ripl_mripl.local_ripls[0] # only needed because of set_seed
            self.mripl = True
        else:
            ripl = ripl_mripl
            self.mripl = False
        

        # make fresh ripl with same backend as input ripl
        self.backend = ripl.backend()
        self.ripl = mk_p_ripl() if self.backend=='puma' else mk_l_ripl()
        
        directives_list = ripl.list_directives()
        
        if assumes is not None:
            self.assumes = assumes
            self.observes = observes if observes is not None else []
        else:
            assumes = [d for d in directives_list if d['instruction']=='assume']
            self.assumes = map(directive_split,assumes)
            observes = [d for d in directives_list if d['instruction']=='observe']
            self.observes = map(directive_split,observes)

        self.queryExps=[] if queryExps is None else queryExps


        if parameters is None: parameters = {}
        self.parameters = parameters.copy()
        if 'venture_random_seed' in self.parameters:
            self.ripl.set_seed(self.parameters['venture_random_seed'])
        else:
            self.parameters['venture_random_seed'] = 1 ## UNKNOWN SEED


        # make fresh mripl with same backend as input mripl
        if self.mripl:
            self.mripl = MRipl(ripl_mripl.no_ripls,
                               backend = ripl_mripl.backend,
                               local_mode = ripl_mripl.local_mode)
            [self.mripl.assume(sym,exp) for sym,exp in self.assumes]
            [self.mripl.observe(exp,lit) for exp,lit in self.observes]

            self.backend = self.mripl.backend
            if self.mripl.local_mode is False:
                self.mripl.dview.execute('from venture.unit import Analytics')
            self.updateQueryExps()
        


    def updateObserves(self,newObserves=None,removeAllObserves=False):
        '''Extend list of observes or empty it.
           Input: newObserves :: [(exp,literal)], removeAllObserves :: bool.'''
        if removeAllObserves:
            self.observes = []
        if newObserves is not None:
            self.observes.extend( newObserves )
    
        
    def updateQueryExps(self,newQueryExps=None,removeAllQueryExps=False):
        '''Extend list of query expressions or empty it.
           Input: newQueryExps :: [(exp)], removeAllQueryExps :: bool.'''
        if removeAllQueryExps:
            self.queryExps = []
        if newQueryExps is not None:
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
        self.ripl.clear()

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
        # FIXME: need predictable behavior from RNG
        random.seed(self.parameters['venture_random_seed'])
        predictToDirective = dict(random.sample(predictToDirective.items(), track))

        return predictToDirective

    def _loadObserves(self, data=None):
        'If data not None, replace values in self.observes'
        for (index, (expression, literal)) in enumerate(self.observes):
            datum = literal if data is None else data[index]
            datum= parseValue(datum)
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
        observes. If self.mripl is False, loop over a single ripl, tracking
        *track* random observes.'''
        
        def mriplSample():
            assumedValues={}
            predictedValues={}
            queryExpsValues={}
        
            v = MRipl(samples, backend=self.backend, local_mode=mriplLocalMode)
            [v.assume(sym,exp) for sym,exp in self.assumes]

            rangeAssumes=range(1,1+len(self.assumes))
            observeLabels=[self.nameObserve(i) for i,_ in enumerate(self.observes)]
            if mriplTrackObserves is False:
                observeLabel = []

            for (exp,_),name in zip(self.observes,observeLabels):
                v.predict(exp,label=name)
                
            for did, (sym,_) in zip( rangeAssumes,self.assumes):
                assumedValues[sym] = v.report(did,type=True)
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



    # iterates until (approximately) all random choices have been resampled
    def sweep(self,infer=None):
        iterations = 0
        get_entropy_info = self.ripl.sivm.core_sivm.engine.get_entropy_info

        while iterations < get_entropy_info()['unconstrained_random_choices']:
            step = get_entropy_info()['unconstrained_random_choices']
            if infer is None:
                self.ripl.infer(step)
                
            elif isinstance(infer, str):
                self.ripl.infer(infer)
            else:
                infer(self.ripl, step)
            iterations += step

        return iterations
    
  
    def _runRepeatedly(self, f, tag, runs=3, verbose=False, profile=False,
                       **kwargs):
        history = History(tag, self.parameters)
        
        if self.mripl:
            v = MRipl(runs,backend=self.backend,local_mode=self.mripl.local_mode)
            
            def sendf(ripl,fname,modelTuple,**kwargs):
                seed = ripl.sample('(uniform_discrete 0 (pow 10 5))') ## FIXME HACK
                params=dict(venture_random_seed=seed)
                assumes,observes,queries = modelTuple
                model = Analytics(ripl,assumes=assumes,observes=observes,
                                  queryExps=queries)
                return getattr(model,fname)(label='seed:%s'%seed,**kwargs)
                
            modelTuple=(self.assumes,self.observes,self.queryExps)
            results = mr_map_proc(v,'all',sendf, f.func_name, modelTuple,**kwargs)

            [history.addRun(r) for r in results[:runs] ]

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

    def _collectSamples(self, assumeToDirective, predictToDirective, sweeps=100, label=None, verbose=False, infer=None, force=None):
        answer = Run(label, self.parameters)
        

        assumedValues = {symbol : [] for symbol in assumeToDirective}
        predictedValues = {index: [] for index in predictToDirective}
        queryExpsValues = {exp: [] for exp in self.queryExps}

        sweepTimes = []
        sweepIters = []
        logscores = []

        for sweep in range(sweeps):
            if verbose:
                print "Running sweep " + str(sweep+1) + " of " + str(sweeps)

            # FIXME: use timeit module for better precision
            start = time.time()
            iterations = self.sweep(infer=infer)
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


    def runFromConditional(self, sweeps, name=None, data=None, **kwargs):
        '''Runs inference on the model conditioned on data.
           By default data is values of self.observes.

           Arguments
           ---------
           sweeps :: int
               Total number of iterations of inference program. Values are
               recorded after every sweep.
           runs :: int
               Number of parallel chains for inference. Default=3.
           infer :: string | function on ripl
               Inference program.
           name :: string
               Label this set of runs for output History and plots.
           data :: [values]
               List of values that replace values in self.observes for this
               inference run only.
           verbose :: bool
               Print when initiating runs and sweeps.

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
        self._clearRipl()
        assumeToDirective = self._loadAssumes()
        self._loadObserves(data)

        if force is not None:
            for symbol,value in force.iteritems():
                self.ripl.force(symbol,value)
        
        # note: we loadObserves, but predictToDirective arg = {}
        # so we are not collecting sample of the observes here. 
        return self._collectSamples(assumeToDirective, {}, **kwargs)



    def testFromPrior(self,noDatasets,sweeps,**kwargs):

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
            
        histories = mr_map_proc(self.mripl, noDatasets, fromPrior,
                                sweeps, self.queryExps,force=None, **kwargs)
        
        pairs = zip(['Ripl%i'%i for i in range(noDatasets)],histories)
        historyOV = historyOverlay('testFromPrior',pairs)
        
        return historyOV, self.mripl
            
                                        

    # Run inference conditioned on data generated from the prior.
    def runConditionedFromPrior(self, sweeps, verbose=False, **kwargs):
        ## FIXME: add docstring describing groundtruth and outputting ripl.
        
        (data, groundTruth) = self.generateDataFromPrior(sweeps, verbose=verbose)

        history,_ = self.runFromConditional(sweeps, data=data, verbose=verbose, **kwargs)
        history.addGroundTruth(groundTruth,sweeps) #sweeps vs. totalSamples
        history.label = 'run_conditioned_from_prior'

        return (history,self.ripl) if not self.mripl else (history,self.mripl)




    # The "sweeps" argument specifies the number of times to repeat
    # the values collected from the prior, so that they are parallel
    # to the samples one intends to compare against them.
    def generateDataFromPrior(self, sweeps, verbose=False):
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



    def gewekeTest(self,samples,infer=None,plot=True,names=None,track=5,
                   compareObserves=False,useMRipl=False):
        '''Geweke-style Test. Tracks and records all assumes, observes,
           and queryExpressions in history. Argument *compareObserves*
           specifies whether observes are analyzed. If optional *names* is given,
           only those names from nameToHistory are analyzed.'''
        forwardHistory = self.sampleFromJoint(samples, track=track,
                                              mriplTrackObserves=compareObserves,
                                              useMRipl=useMRipl)
        inferHistory = self.runFromJoint(samples,infer=infer,runs=1)
        ## FIXME: should be able to take multiple runs and flatten them
        #  inferHistory = flattenRuns(inferHistory)

        print 'Geweke-style Test of Inference: \n'
        print '''
        Compare iid (forward) samples from joint to dependent
        samples from inference (*observes* changed to *predicts*)\n'''
        print '-------------\n'
        
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
            
        compareStats,fig = compareSampleDicts(dicts,labels,plot=plot)
        
        return forwardHistory,inferHistory,compareStats



from venture.test.stats import reportSameContinuous
import scipy.stats

def flattenRuns(history):
    for name,listSeries in history.nameToSeries.iteritems():
        label = listSeries[0].label
        hist=  listSeries[0].hist
        values = [e for series in listSeries for e in series.values]
        listSeries = [Series(label,values,hist=hist)]
        

def historyToSnapshots(history):
    '''output = {name:[ snapshot_i ] }, where snapshot_i
    is [series.value[i] for series in nameToSeries[name]]''' 
    snapshots={}
    # always ignore sweep time for snapshots
    ignore=('sweep time','sweep_iters')
    for name,listSeries in history.nameToSeries.iteritems():
        if any([s in name.lower() for s in ignore]):
            continue
        arrayValues = np.array( [s.values for s in listSeries] )
        snapshots[name] = map(list,arrayValues.T) 
    return snapshots


def filterDict(d,keep=(),ignore=()):
    '''Shallow copy of dictionary d filtered on keys.
       If *keep* nonempty, keep items in keep.
       If *keep* empty, keep items not in ignore.'''
    assert isinstance(keep,(tuple,list))
    if keep:
        return dict([(k,v) for k,v in d.items() if k in keep])
    else:
        return dict([(k,v) for k,v in d.items() if k not in ignore])


def compareSnapshots(history,names=None,probes=None):
    '''
    Compare samples across runs at two different probe points
    in History. Defaults to comparing all names and probes=
    (midPoint,lastPoint).'''
    
    allSnapshots = historyToSnapshots(history)
    samples = len(allSnapshots.items()[0][1])

    # restrict to probes
    if probes is None:
        probes = (int(round(.5*samples)),-1)
    else:
        assert len(probes)==2

    # restrict to names
    if names is not None:
        filterSnapshots = filterDict(allSnapshots,keep=names)
    else:
        filterSnapshots = allSnapshots

    snapshotDicts=({},{})
    for name,snapshots in filterSnapshots.iteritems():
        for d,probe in zip(snapshotDicts,probes):
            d[name]=snapshots[probe]

    labels =[history.label+'_'+'snap_%i'%i for i in probes]
    return compareSampleDicts(snapshotDicts,labels,plot=True)



def qqPlotAll(dicts,labels):
    # FIXME do interpolation where samples have different lengths
    exps = intersectKeys(dicts)
    fig,ax = plt.subplots( len(exps),2,figsize=(12,4*len(exps)) )
    
    for i,exp in enumerate(exps):
        s1,s2 = (dicts[0][exp],dicts[1][exp])
        assert len(s1)==len(s2)

        def makeHists(ax):
            ax.hist(s1,bins=20,alpha=0.8,color='b',label=labels[0])
            ax.hist(s2,bins=20,alpha=0.6,color='y',label=labels[1])
            ax.legend()
            ax.set_title('Histogram: %s'%exp)

        def makeQQ(ax):
            ax.scatter(sorted(s1),sorted(s2),s=4,lw=0)
            ax.set_xlabel(labels[0])
            ax.set_ylabel(labels[1])
            ax.set_title('QQ Plot %s'%exp)
            xr = np.linspace(min(s1),max(s1),30)
            ax.plot(xr,xr)
            
        if len(exps)==1:
            makeHists(ax[0])
            makeQQ(ax[1])
        else:
            makeHists(ax[i,0])
            makeQQ(ax[i,1])

    fig.tight_layout()
    return fig


def filterScalar(dct):
    'Remove non-scalars from {exp:values}'
    scalar=lambda x:isinstance(x,(float,int))
    scalarDct={}
    for exp,values in dct.items():
        if all(map(scalar,values)):
            scalarDct[exp]=values
    return scalarDct


def intersectKeys(dicts):
    return tuple(set(dicts[0].keys()).intersection(set(dicts[1].keys())))

def compareSampleDicts(dicts_hists,labels,plot=False):
    '''Input: dicts_hists :: ({exp:values}) | (History)
     where the first Series in History is used as values. History objects
     are converted to dicts. Flatten History to include all Series.''' 

    if not isinstance(dicts_hists[0],dict):
        dicts = [historyNameToValues(h,seriesInd=0) for h in dicts_hists]
    else:
        dicts = dicts_hists
        
    dicts = map(filterScalar,dicts) # could skip for Analytics
        
    
    stats = (np.mean,scipy.stats.sem,np.median,len)
    statsString = ' '.join(['mean','sem','med','N'])
    stats_dict = {}
    print 'compareSampleDicts: %s vs. %s \n'%(labels[0],labels[1])
    
    for exp in intersectKeys(dicts):
        print '\n---------'
        print 'Name:  %s'%exp
        stats_dict[exp] = []
        
        for dict_i,label_i in zip(dicts,labels):
            samples=dict_i[exp]
            s_stats = tuple([s(samples) for s in stats])
            stats_dict[exp].append(s_stats)
            labelStr='%s : %s ='%(label_i,statsString)
            print labelStr+'  %.3f  %.3f  %.3f  %i'%s_stats


        testResult=reportSameContinuous(dicts[0][exp],dicts[1][exp])
        print 'KS Test:   ', '  '.join(testResult.report.split('\n')[-2:])
        stats_dict[exp].append( testResult )
        
    fig = qqPlotAll(dicts,labels) if plot else None
    
    return stats_dict,fig


def historyNameToValues(history,seriesInd=0,flatten=False):
    ''':: History -> {name:values}. Default is to take first series.
    If flatten then we combine all.'''
    nameToValues={}
    for name,listSeries in history.nameToSeries.items():
        if flatten:
            values = [el for series in listSeries for el in series.values]
        else:
            values = listSeries[seriesInd].values
        nameToValues[name]=values
    return nameToValues









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













