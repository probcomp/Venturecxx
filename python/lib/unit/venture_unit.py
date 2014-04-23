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
import time
import random
import numpy as np
from venture.ripl.ripl import _strip_types

from history import History, Run, Series

parseValue = _strip_types

# VentureUnit is an experimental harness for developing, debugging and profiling Venture programs.
class VentureUnit(object):
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

        # FIXME: Should the random seed be stored, or re-initialized?
        self.parameters = parameters.copy()
        if 'venture_random_seed' not in self.parameters:
            self.parameters['venture_random_seed'] = self.ripl.get_seed()
        else:
            self.ripl.set_seed(self.parameters['venture_random_seed'])

        # FIXME: automatically assume parameters (and omit them from history)?
        self.assumes = []
        self.makeAssumes()

        self.observes = []
        self.makeObserves()

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

    def _loadObservesAsPredicts(self, track=0):
        predictToDirective = {}
        for (index, (expression, _)) in enumerate(self.observes):
            #print("self.ripl.predict('%s', label='%d')" % (expression, index))
            label = 'observe_%d' % index
            value = self.ripl.predict(expression, label=label, type=True)
            predictToDirective[index] = label

        # choose a random subset to track; by default all are tracked
        track = min(track, len(predictToDirective))
        # FIXME: need predictable behavior from RNG
        random.seed(self.parameters['venture_random_seed'])
        predictToDirective = dict(random.sample(predictToDirective.items(), track))

        return predictToDirective

    def _loadObserves(self, data=None):
        for (index, (expression, literal)) in enumerate(self.observes):
            datum = literal if data is None else data[index]
            self.ripl.observe(expression, datum)

    # Loads the assumes and changes the observes to predicts.
    # Also picks a subset of the predicts to track (by default all are tracked).
    # Prunes non-scalar values, unless prune=False.
    # Does not reset engine RNG.
    def loadModelWithPredicts(self, track=-1, prune=True):
        self.ripl.clear()

        assumeToDirective = self._loadAssumes(prune=prune)
        predictToDirective = self._loadObservesAsPredicts(track=track, prune=prune)

        return (assumeToDirective, predictToDirective)

    # Updates recorded values after an iteration of the ripl.
    def updateValues(self, keyedValues, keyToDirective):
        for (key, values) in keyedValues.items():
            if key not in keyToDirective: # we aren't interested in this series
                del keyedValues[key]
                continue

            value = self.ripl.report(keyToDirective[key], type=True)
            if len(values) > 0:
                if value['type'] == values[0]['type']:
                    values.append(value)
                else: # directive has returned a different type; discard the series
                    del keyedValues[key]
            values.append(value)

    # Gives a name to an observe directive.
    def nameObserve(self, index):
        return 'observe[' + str(index) + '] ' + self.observes[index][0]

    # Provides independent samples from the joint distribution (observes turned into predicts).
    # A random subset of the predicts are tracked along with the assumed variables.
    # Returns a History object that always represents exactly one Run.
    def sampleFromJoint(self, samples, track=5, verbose=False, name=None):
        assumedValues = {symbol:  [] for (symbol, _) in self.assumes}
        predictedValues = {index: [] for index in range(len(self.observes))}

        logscores = []

        for i in range(samples):
            if verbose:
                print "Generating sample " + str(i+1) + " of " + str(samples)

            (assumeToDirective, predictToDirective) = self.loadModelWithPredicts(track)

            logscores.append(self.ripl.get_global_logscore())

            self.updateValues(assumedValues, assumeToDirective)
            self.updateValues(predictedValues, predictToDirective)

        tag = 'sample_from_joint' if name is None else name + '_sample_from_joint'
        history = History(tag, self.parameters)

        history.addSeries('logscore', 'number', 'i.i.d.', logscores)

        for (symbol, values) in assumedValues.iteritems():
            history.addSeries(symbol, values[0]['type'], 'i.i.d.', map(parseValue, values))

        for (index, values) in predictedValues.iteritems():
            history.addSeries(self.nameObserve(index), values[0]['type'], 'i.i.d.', map(parseValue, values))

        return history

    # iterates until (approximately) all random choices have been resampled
    def sweep(self,infer=None):
        iterations = 0

        #FIXME: use a profiler method here
        get_entropy_info = self.ripl.sivm.core_sivm.engine.get_entropy_info

        while iterations < get_entropy_info()['unconstrained_random_choices']:
            step = get_entropy_info()['unconstrained_random_choices']
            if infer is None:
                self.ripl.infer(step)
            # TODO Incoming infer string or procedure may touch more
            # than "step" choices; how to count sweeps right?
            elif isinstance(infer, str):
                self.ripl.infer(infer)
            else:
                infer(self.ripl, step)
            iterations += step

        return iterations
    
    # TODO: run in parallel?
    def _runRepeatedly(self, f, tag, runs=3, verbose=False, profile=False, **kwargs):
        history = History(tag, self.parameters)

        for run in range(runs):
            if verbose:
                print "Starting run " + str(run+1) + " of " + str(runs)
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

    def _collectSamples(self, assumeToDirective, predictToDirective, sweeps=100, label=None, verbose=False, infer=None):
        answer = Run(label, self.parameters)

        assumedValues = {symbol : [] for symbol in assumeToDirective}
        predictedValues = {index: [] for index in predictToDirective}

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

            self.updateValues(assumedValues, assumeToDirective)
            self.updateValues(predictedValues, predictToDirective)

        answer.addSeries('sweep time (s)', 'count', Series(label, sweepTimes))
        answer.addSeries('sweep_iters', 'count', Series(label, sweepIters))
        answer.addSeries('logscore', 'number', Series(label, logscores))

        for (symbol, values) in assumedValues.iteritems():
            answer.addSeries(symbol, values[0]['type'], Series(label, map(parseValue, values)))

        for (index, values) in predictedValues.iteritems():
            answer.addSeries(self.nameObserve(index), values[0]['type'], Series(label, map(parseValue, values)))

        return answer

    # Computes the KL divergence on i.i.d. samples from the prior and inference on the joint.
    # Returns the sampled history, inferred history, and history of KL divergences.
    def computeJointKL(self, sweeps, samples, track=5, runs=3, verbose=False, name=None, infer=None):
        sampledHistory = self.sampleFromJoint(samples, track, verbose, name=name)
        inferredHistory = self.runFromJoint(sweeps, track=track, runs=runs, verbose=verbose, name=name, infer=infer)

        tag = 'kl_divergence' if name is None else name + '_kl_divergence'
        klHistory = History(tag, self.parameters)

        for (name, seriesList) in inferredHistory.nameToSeries.iteritems():
            if name not in sampledHistory.nameToSeries: continue

            for inferredSeries in seriesList:
                sampledSeries = sampledHistory.nameToSeries[name][0]

                klValues = [computeKL(sampledSeries.values, inferredSeries.values[:index+1]) for index in range(sweeps)]

                klHistory.addSeries('KL_' + name, 'number', inferredSeries.label, klValues, hist=False)

        return (sampledHistory, inferredHistory, klHistory)

    # Runs inference on the model conditioned on observed data.
    # By default the data is as given in makeObserves(parameters).
    def runFromConditional(self, sweeps, name=None, **kwargs):
        tag = 'run_from_conditional' if name is None else name + '_run_from_conditional'
        return self._runRepeatedly(self.runFromConditionalOnce, tag, sweeps=sweeps, **kwargs)
  
    def runFromConditionalOnce(self, data=None, **kwargs):
        self.ripl.clear()
        assumeToDirective = self._loadAssumes()
        self._loadObserves(data)
        return self._collectSamples(assumeToDirective, {}, **kwargs)

    # Run inference conditioned on data generated from the prior.
    def runConditionedFromPrior(self, sweeps, verbose=False, **kwargs):
        (data, prior_run) = self.generateDataFromPrior(sweeps, verbose=verbose)
        history = self.runFromConditional(sweeps, data=data, verbose=verbose, **kwargs)
        history.addRun(prior_run)
        history.label = 'run_conditioned_from_prior'
        return history

    # The "sweeps" argument specifies the number of times to repeat
    # the values collected from the prior, so that they are parallel
    # to the samples one intends to compare against them.
    def generateDataFromPrior(self, sweeps, verbose=False):
        if verbose:
            print 'Generating data from prior'

        (assumeToDirective, predictToDirective) = self.loadModelWithPredicts(prune=False)

        data = [self.ripl.report(predictToDirective[index], type=True) for index in range(len(self.observes))]

        prior_run = Run('run_conditioned_from_prior', self.parameters)
        assumedValues = {}
        for (symbol, directive) in assumeToDirective.iteritems():
            value = self.ripl.report(directive, type=True)
            assumedValues[symbol] = value
        logscore = self.ripl.get_global_logscore()
        prior_run.addSeries('logscore', 'number', Series('prior', [logscore]*sweeps, hist=False))
        for (symbol, value) in assumedValues.iteritems():
            prior_run.addSeries(symbol, value['type'], Series('prior', [parseValue(value)]*sweeps))
        return (data, prior_run)

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

