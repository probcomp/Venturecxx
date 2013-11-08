import time
import random
import pdb
import numpy

# whether to record a value returned from the ripl
def record(value):
    return value['type'] in {'boolean', 'real', 'number', 'atom', 'count', 'probability', 'smoothed_count'}

def parseValue(value):
    return value['value']

# VentureUnit is an experimental harness for developing, debugging and profiling Venture programs.
class VentureUnit:
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
    
    # Initializes parameters, generates the model, and prepares the ripl.
    def __init__(self, ripl, parameters={}):
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
    
    # Loads the assumes and changes the observes to predicts.
    # Also picks a subset of the predicts to track (by default all are tracked).
    # Prunes non-scalar values, unless prune=False.
    # Does not reset engine RNG.
    def loadModelWithPredicts(self, track=-1, prune=True):
        self.ripl.clear()
        
        assumeToDirective = {}
        for (symbol, expression) in self.assumes:
            from venture.exception import VentureException
            try:
                value = self.ripl.assume(symbol, expression, label=symbol, type=True)
            except VentureException as e:
                print expression
                raise e
            if (not prune) or record(value):
                assumeToDirective[symbol] = symbol
        
        predictToDirective = {}
        for (index, (expression, literal)) in enumerate(self.observes):
            #print("self.ripl.predict('%s', label='%d')" % (expression, index))
            label = 'observe_%d' % index
            value = self.ripl.predict(expression, label=label, type=True)
            if (not prune) or record(value):
                predictToDirective[index] = label
        
        # choose a random subset to track; by default all are tracked
        if track >= 0:
            track = min(track, len(predictToDirective))
            # FIXME: need predictable behavior from RNG
            random.seed(self.parameters['venture_random_seed'])
            predictToDirective = dict(random.sample(predictToDirective.items(), track))
        
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
            elif record(value):
                values.append(value)
            else: # directive has returned a non-scalar type; discard the series
                del keyedValues[key]
    
    # Gives a name to an observe directive.
    def nameObserve(self, index):
        return 'observe[' + str(index) + '] ' + self.observes[index][0]
    
    # Provides independent samples from the joint distribution (observes turned into predicts).
    # A random subset of the predicts are tracked along with the assumed variables.
    def sampleFromJoint(self, samples, track=5, verbose=False):
        assumedValues = {}
        for (symbol, expression) in self.assumes:
          assumedValues[symbol] = []
        predictedValues = {}
        for index in range(len(self.observes)):
          predictedValues[index] = []
        
        logscores = []
        
        for i in range(samples):
            if verbose:
                print "Generating sample " + str(i)
            
            (assumeToDirective, predictToDirective) = self.loadModelWithPredicts(track)
            
            logscores.append(self.ripl.get_global_logscore())
            
            self.updateValues(assumedValues, assumeToDirective)
            self.updateValues(predictedValues, predictToDirective)
        
        history = History('sample_from_joint', self.parameters)
        
        history.addSeries('logscore', 'i.i.d.', logscores)
        
        series = assumedValues.copy()
        for (symbol, values) in assumedValues.iteritems():
            history.addSeries(symbol, 'i.i.d.', map(parseValue, values))
        
        for (index, values) in predictedValues.iteritems():
            history.addSeries(self.nameObserve(index), 'i.i.d.', map(parseValue, values))
        
        return history
    
    # iterates until (approximately) all random choices have been resampled
    def sweep(self):
        iterations = 0
        
        #FIXME: use a profiler method here
        get_entropy_info = self.ripl.sivm.core_sivm.engine.get_entropy_info
        
        while iterations < get_entropy_info()['unconstrained_random_choices']:
            step = get_entropy_info()['unconstrained_random_choices']
            self.ripl.infer(step)
            iterations += step
        
        return iterations
    
    # Runs inference on the joint distribution (observes turned into predicts).
    # A random subset of the predicts are tracked along with the assumed variables.
    # If profiling is enabled, information about random choices is recorded.
    def runFromJoint(self, sweeps, track=5, runs=3, verbose=False, profile=False):
        history = History('run_from_joint', self.parameters)
        
        for run in range(runs):
            if verbose:
                print "Starting run " + str(run)
            
            (assumeToDirective, predictToDirective) = self.loadModelWithPredicts(track)
            
            assumedValues = {symbol : [] for symbol in assumeToDirective}
            predictedValues = {index: [] for index in predictToDirective}
            
            sweepTimes = []
            sweepIters = []
            logscores = []
            
            for sweep in range(sweeps):
                if verbose:
                    print "Running sweep " + str(sweep)
                
                # FIXME: use timeit module for better precision
                start = time.time()
                iterations = self.sweep()
                end = time.time()
                
                sweepTimes.append(end-start)
                sweepIters.append(iterations)
                logscores.append(self.ripl.get_global_logscore())
                
                self.updateValues(assumedValues, assumeToDirective)
                self.updateValues(predictedValues, predictToDirective)
            
            history.addSeries('sweep_time', 'run ' + str(run), sweepTimes)
            history.addSeries('sweep_iters', 'run ' + str(run), sweepIters)
            history.addSeries('logscore', 'run ' + str(run), logscores)
            
            for (symbol, values) in assumedValues.iteritems():
                history.addSeries(symbol, 'run ' + str(run), map(parseValue, values))
            
            for (index, values) in predictedValues.iteritems():
                history.addSeries(self.nameObserve(index), 'run %d' % run, map(parseValue, values))
        
        if profile:
            history.profile = Profile(self.ripl)
        
        return history
    
    # Computes the KL divergence on i.i.d. samples from the prior and inference on the joint.
    # Returns the sampled history, inferred history, and history of KL divergences.
    def computeJointKL(self, sweeps, samples, track=5, runs=3, verbose=False):
        sampledHistory = self.sampleFromJoint(samples, track, verbose)
        inferredHistory = self.runFromJoint(sweeps, track, runs, verbose)
        
        klHistory = History('kl_divergence', self.parameters)
        
        for (name, seriesList) in inferredHistory.nameToSeries.iteritems():
            if name not in sampledHistory.nameToSeries: continue
            
            for inferredSeries in seriesList:
                sampledSeries = sampledHistory.nameToSeries[name][0]
                
                klValues = [computeKL(sampledSeries.values, inferredSeries.values[:index+1]) for index in range(sweeps)]
                
                klHistory.addSeries('KL_' + name, inferredSeries.label, klValues, hist=False)
        
        return (sampledHistory, inferredHistory, klHistory)
    
    # Runs inference on the model conditioned on observed data.
    # By default the data is as given in makeObserves(parameters).
    def runFromConditional(self, sweeps, data=None, runs=3, verbose=False, profile=False):
        history = History('run_from_conditional', self.parameters)
        
        for run in range(runs):
            if verbose:
                print "Starting run " + str(run)
            
            self.ripl.clear()
        
            assumeToDirective = {}
            for (symbol, expression) in self.assumes:
                value = self.ripl.assume(symbol, expression, symbol, type=True)
                if record(value): assumeToDirective[symbol] = symbol
        
            for (index, (expression, literal)) in enumerate(self.observes):
                datum = literal if data is None else data[index]
                self.ripl.observe(expression, datum)
            
            sweepTimes = []
            sweepIters = []
            logscores = []
            
            assumedValues = {}
            for symbol in assumeToDirective:
              assumedValues[symbol] = []
              
            for sweep in range(sweeps):
                if verbose:
                    print "Running sweep " + str(sweep)
                
                # FIXME: use timeit module for better precision
                start = time.time()
                iterations = self.sweep()
                end = time.time()
                
                sweepTimes.append(end-start)
                sweepIters.append(iterations)
                logscores.append(self.ripl.get_global_logscore())
                
                self.updateValues(assumedValues, assumeToDirective)
            
            history.addSeries('sweep_time', 'run ' + str(run), sweepTimes)
            history.addSeries('sweep_iters', 'run ' + str(run), sweepIters)
            history.addSeries('logscore', 'run ' + str(run), logscores)
            
            for (symbol, values) in assumedValues.iteritems():
                history.addSeries(symbol, 'run ' + str(run), map(parseValue, values))
            
            if profile:
                history.profile = Profile(self.ripl)
        
        return history
    
    # Run inference conditioned on data generated from the prior.
    def runConditionedFromPrior(self, sweeps, runs=3, verbose=False, profile=False):
        if verbose:
            print 'Generating data from prior'
        
        (assumeToDirective, predictToDirective) = self.loadModelWithPredicts(prune=False)
        
        data = [self.ripl.report(predictToDirective[index], type=True) for index in range(len(self.observes))]
        
        assumedValues = {}
        for (symbol, directive) in assumeToDirective.iteritems():
            value = self.ripl.report(directive, type=True)
            if record(value):
                assumedValues[symbol] = value
        
        logscore = self.ripl.get_global_logscore()
        
        history = self.runFromConditional(sweeps, data, runs, verbose, profile)
        
        history.addSeries('logscore', 'prior', [logscore]*sweeps, hist=False)
        for (symbol, value) in assumedValues.iteritems():
            history.addSeries(symbol, 'prior', [parseValue(value)]*sweeps)
        
        history.label = 'run_conditioned_from_prior'
        
        return history

# Reads the profile data from the ripl.
# Returns a map from (random choice) addresses to info objects.
# The info contains the trials, successes, acceptance_rate, proposal_time, and source_location.
class Profile:
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
        return hot[:maxnum]
    
    def coldspots(self, num=5):
        cold = sorted(self.addressToInfo.values(), key=lambda info: info.acceptance_rate)
        return cold[:num]

from numpy import mean

# Records data for each sweep. Typically, all scalar assumes are recorded.
# Certain running modes convert observes to predicts. In those cases, a random subset of the observes (now predicts) are tracked.
# Some extra data is also recorded, such as the logscore, sweep_time, and sweep_iters.
class History:
    def __init__(self, label='empty_history', parameters={}):
        self.label = label
        self.parameters = parameters
        self.nameToSeries = {}
    
    def addSeries(self, name, label, values, hist=True):
        if name not in self.nameToSeries:
            self.nameToSeries[name] = []
        self.nameToSeries[name].append(Series(label, values, hist))
    
    # Returns the average over all series with the given name.
    def averageValue(self, seriesName):
        return mean([mean(series.values) for series in self.nameToSeries[seriesName]])
    
    # default directory for plots, created from parameters
    def defaultDirectory(self):
        name = self.label
        for (param, value) in self.parameters.iteritems():
            name += '_' + param + '=' + str(value)
        return name + '/'
    
    # directory specifies location of plots
    # default format is pdf
    def plot(self, fmt='pdf', directory=None):
        if directory == None:
            directory = self.defaultDirectory()
        
        if not os.path.exists(directory):
            os.mkdir(directory)
        
        for (name, seriesList) in self.nameToSeries.iteritems():
            plotSeries(name, self.label, seriesList, self.parameters, fmt, directory)
            plotHistogram(name, self.label, seriesList, self.parameters, fmt, directory)
        
        print 'plots written to ' + directory

# aggregates values for one variable over the course of a run
class Series:
    def __init__(self, label, values, hist):
        self.label = label
        self.values = values
        self.hist = hist

import matplotlib
#matplotlib.use('pdf')
matplotlib.use('Agg')
import matplotlib.pyplot as plt
#from matplotlib.backends.backend_pdf import PdfPages
import os

# Displays parameters in top-left corner of the graph.
def showParameters(parameters):
    items = sorted(parameters.items())
    
    text = items[0][0] + ' = ' + str(items[0][1])
    for (name, value) in items[1:]:
        text += '\n' + name + ' = ' + str(value)
    
    plt.text(0, 1, text, transform=plt.axes().transAxes, va='top', size='small', linespacing=1.0)

# Plots a set of series.
def plotSeries(name, subtitle, seriesList, parameters, fmt, directory):
    fig = plt.figure()
    plt.clf()
    plt.title('Series for ' + name + '\n' + subtitle)
    plt.xlabel('Sweep')
    plt.ylabel(name)
    showParameters(parameters)
    
    plots = [plt.plot(series.values)[0] for series in seriesList]
    
    plt.legend(plots, [series.label for series in seriesList])

    ymin = min([min(series.values) for series in seriesList])
    ymax = max([max(series.values) for series in seriesList])

    offset = 0.1 * max([(ymax - ymin), 1.0])

    if not any([any([numpy.isinf(v) for v in series.values]) for series in seriesList]):
        plt.ylim([ymin - offset, ymax + offset])
    
    #plt.tight_layout()
    fig.savefig(directory + name.replace(' ', '_') + '_series.' + fmt, format=fmt)

# Plots histograms for a set of series.
def plotHistogram(name, subtitle, seriesList, parameters, fmt, directory):
    fig = plt.figure()
    plt.clf()
    plt.title('Histogram of ' + name + '\n' + subtitle)
    plt.xlabel(name)
    plt.ylabel('Frequency')
    showParameters(parameters)
    
    # FIXME: choose a better bin size
    plt.hist([series.values for series in seriesList], bins=20, label=[series.label for series in seriesList])
    plt.legend()
    
    #plt.tight_layout()
    fig.savefig(directory + name.replace(' ', '_') + '_hist.' + fmt, format=fmt)

# smooths out a probability distribution function
def smooth(pdf, amt=0.1):
    return [(p + amt / len(pdf)) / (1.0 + amt) for p in pdf]

import numpy as np
#np.seterr(all='raise')
import math

# Approximates the KL divergence between samples from two distributions.
# 'reference' is the "true" distribution
# 'approx' is an approximation of 'reference'
def computeKL(reference, approx, numbins=20):
    
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

import itertools
from collections import namedtuple
from matplotlib import cm

def makeIterable(obj):
    return obj if hasattr(obj, '__iter__') else [obj]

def cartesianProduct(keyToValues):
    items = [(key, makeIterable(value)) for (key, value) in keyToValues.items()]
    (keys, values) = zip(*items)
    
    Key = namedtuple('Key', keys)
    return [Key._make(t) for t in itertools.product(*values)]

# Produces histories for a set of parameters.
# Here the parameters can contain lists. For example, {'a':[0, 1], 'b':[2, 3]}.
# Then histories will be computed for the parameter settings ('a', 'b') = (0, 1), (0, 2), (1, 2), (1, 3)
# Runner should take a given parameter setting and produce a history.
# For example, runner = lambda params : Model(ripl, params).runConditionedFromPrior(sweeps, runs, track=0)
# Returned is a dictionary mapping each parameter setting (as a namedtuple) to the history.
def produceHistories(parameters, runner, verbose=False):
    def _runner(params):
        if verbose:
            print(params)
        return runner(params._asdict())
    
    return {params : _runner(params) for params in cartesianProduct(parameters)}

# Sets key to value and returns the updated dictionary.
def addToDict(dictionary, key, value):
    dictionary[key] = value
    return dictionary

# Produces plots for a a given variable over a set of runs.
# Variable parameters are the x-axis, 'seriesName' is the y-axis.
# If aggregate=True, multiple plots that differ in only one parameter are overlayed.
def plotAsymptotics(parameters, histories, seriesName, fmt='pdf', directory=None, verbose=False, aggregate=False):
    if directory is None:
        directory = seriesName + '_asymptotics/'
    
    if not os.path.exists(directory):
        os.mkdir(directory)
    
    # Hashable tuple with named entries (like a dict).
    Key = namedtuple('Key', parameters.keys())
    
    # Map from parameters to the average value of the seriesName for those parameters.
    paramsToValue = {params : history.averageValue(seriesName) for (params, history) in histories.items()}
    
    # Pick a parameter for the x-axis.
    for (key, values) in parameters.items():
        # don't use single parameter values
        if not hasattr(values, '__iter__'):
            continue
        # or non-numeric parameters
        if type(values[0]) in {str}:
            continue
        
        others = parameters.copy()
        del others[key]
        
        if aggregate:
            # Pick another parameter to aggregate over.
            for (other, otherValues) in others.items():
                otherValues = makeIterable(otherValues)
                
                rest = others.copy()
                del rest[other]
                
                # Loop over all possible combinations of the remaining parameters.
                for params in cartesianProduct(rest):
                    fig = plt.figure()
                    plt.clf()
                    plt.title(seriesName + ' versus ' + key)
                    plt.xlabel(key)
                    plt.ylabel(seriesName)
                    showParameters(params._asdict())
                    
                    colors = cm.rainbow(np.linspace(0, 1, len(otherValues)))
                    
                    # For each setting of the aggregate parameter, plot the values with respect to the x-axis parameter.
                    for (otherValue, c) in zip(otherValues, colors):
                        p = addToDict(params._asdict(), other, otherValue)
                        plt.scatter(values, [paramsToValue[Key(**addToDict(p, key, value))] for value in values],
                            label=other+'='+str(otherValue), color=c)
                    
                    plt.legend()
                    
                    filename = key
                    for (param, value) in params._asdict().items():
                        filename += '_' + param + '=' + str(value)
                    
                    #plt.tight_layout()
                    fig.savefig(directory + filename.replace(' ', '_') + '_asymptotics.' + fmt, format=fmt)
        else:
            for params in cartesianProduct(others):
                fig = plt.figure()
                plt.clf()
                plt.title(seriesName + ' versus ' + key)
                plt.xlabel(key)
                plt.ylabel(seriesName)
                showParameters(params._asdict())
                
                plt.scatter(values, [paramsToValue[Key(**addToDict(params._asdict(), key, v))] for v in values])
                
                filename = key
                for (param, value) in params._asdict().items():
                    filename += '_' + param + '=' + str(value)
                
                #plt.tight_layout()
                fig.savefig(directory + filename.replace(' ', '_') + '_asymptotics.' + fmt, format=fmt)

