import pylab
import cPickle as pickle
import os
import copy
import numpy as np

from utils import cartesianProduct, makeIterable

class History(object):
    """Aggregates data collected from a typical Venture experiment.

The actual data are a mapping from arbitrary strings to lists of
Series objects (defined below).  The string keys are typically the
names of some of the model variables.  The Series represent the
values of those variables after each sweep.  The lists represent
different runs (they are all parallel; that is, the same run will be
in the same location in each key's list).

A few extra series are typically also stored:
"logscore", "time (s)", "sweep_iters", and "sweep time (s)".

Certain VentureUnit running modes convert observes to predicts. In
those cases, a random subset of the observes (now predicts) are
typically also tracked."""
    def __init__(self, label='empty_history', parameters=None):
        if parameters is None: parameters = {}
        self.label = label # :: string
        self.parameters = parameters # :: {string: a}  the model parameters leading to the data stored here
        self.nameToSeries = {} # :: {string: [Series]} the list is over multiple runs

    def addSeries(self, name, label, values, hist=True):
        if name not in self.nameToSeries:
            self.nameToSeries[name] = []
        self.nameToSeries[name].append(Series(label, values, hist))

    # Returns the average over all series with the given name.
    def averageValue(self, seriesName):
        return np.mean([np.mean(series.values) for series in self.nameToSeries[seriesName]])

    # default directory for plots, created from parameters
    def defaultDirectory(self):
        name = self.label
        for (param, value) in self.parameters.iteritems():
            name += '_' + param + '=' + str(value)
        return name + '/'

    # directory specifies location of plots
    # default format is pdf
    def plot(self, fmt='pdf', directory=None):
        self.save(directory)
        if directory == None:
            directory = self.defaultDirectory()

        ensure_directory(directory)

        for name in self.nameToSeries:
            self.plotOneSeries(name, fmt=fmt, directory=directory)
            self.plotOneHistogram(name, fmt=fmt, directory=directory)

        # TODO There is a better way to expose computed series like
        # this: make the nameToSeries lookup be a method that does
        # this computation.
        if "logscore" in self.nameToSeries and "sweep time (s)" in self.nameToSeries:
            logscores = self.nameToSeries["logscore"] # :: [Series]
            sweep_times = self.nameToSeries["sweep time (s)"]
            score_v_time = [Series(run_logs.label, run_logs.values, True, xvals=np.cumsum(run_times.values))
                            for (run_logs, run_times) in zip(logscores, sweep_times)]
            plotSeries("logscore_vs_wallclock", score_v_time, subtitle=self.label,
                       parameters=self.parameters, fmt=fmt, directory=directory, xlabel="time (s)")

        print 'plots written to ' + directory

    # Plots one series of interest, offering greater control over the
    # configuration of the plot.
    # TODO Carefully spec which names are available to plot.
    def plotOneSeries(self, name, directory=None, **kwargs):
        # TODO Is it ok for a method to have the same name as a global
        # function in Python?
        if directory == None:
            directory = self.defaultDirectory()
        ensure_directory(directory)
        if name in self.nameToSeries:
            plotSeries(name, self.nameToSeries[name], subtitle=self.label,
                       parameters=self.parameters, directory=directory, **kwargs)
        else:
            raise Exception("Cannot plot non-existent series %s" % name)

    def plotOneHistogram(self, name, directory=None, **kwargs):
        if directory == None:
            directory = self.defaultDirectory()
        ensure_directory(directory)
        if name in self.nameToSeries:
            plotHistogram(name, self.nameToSeries[name], subtitle=self.label,
                          parameters=self.parameters, directory=directory, **kwargs)
        else:
            raise Exception("Cannot histogram non-existent series %s" % name)

    def save(self, directory=None):
        if directory == None:
            directory = self.defaultDirectory()
        ensure_directory(directory)
        filename = directory + "/" + self.label
        pickle.dump(self, open(filename, "wb" ) )
        print "History dumped to %s using pickle" % filename

def ensure_directory(directory):
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory)
        except OSError:
            if os.path.isdir(directory):
                pass
            else:
                raise

def loadHistory(filename):
    return pickle.load(open(filename))

# :: string -> [(string,History)] -> History containing all those time series overlaid
# TODO Parameters have to agree for now
def historyOverlay(name, named_hists):
    answer = History(label=name, parameters=named_hists[0][1].parameters)
    for (subname,subhist) in named_hists:
        for (seriesname,seriesSet) in subhist.nameToSeries.iteritems():
            for subseries in seriesSet:
                answer.addSeries(seriesname, subname + "_" + subseries.label, subseries.values, subseries.hist)
    return answer

# aggregates values for one variable over the course of a run
class Series(object):
    def __init__(self, label, values, hist, xvals=None):
        self.label = label
        self.values = values
        self.hist = hist
        self._xvals = xvals

    def xvals(self):
        if self._xvals is not None:
            return self._xvals
        else:
            return range(len(self.values)) # Should be the same as plotting just the values

import matplotlib
#matplotlib.use('pdf')
matplotlib.use('Agg')
import matplotlib.pyplot as plt
#from matplotlib.backends.backend_pdf import PdfPages

# Displays parameters in top-left corner of the graph.
def showParameters(parameters):
    if len(parameters) == 0: return

    items = sorted(parameters.items())

    text = items[0][0] + ' = ' + str(items[0][1])
    for (name, value) in items[1:]:
        text += '\n' + name + ' = ' + str(value)

    plt.text(0, 1, text, transform=plt.axes().transAxes, va='top', size='small', linespacing=1.0)

def setYBounds(seriesList, ybounds=None):
    if ybounds is None:
        ymin = min([min(series.values) for series in seriesList])
        ymax = max([max(series.values) for series in seriesList])

        offset = 0.1 * max([(ymax - ymin), 1.0])

        if not any([any([np.isinf(v) for v in series.values]) for series in seriesList]):
            plt.ylim([ymin - offset, ymax + offset])
    else:
        [ylow,yhigh] = ybounds # Silly pylint not noticing case on maybe type pylint:disable=unpacking-non-sequence
        plt.ylim([ylow,yhigh])

# Plots a set of series.
def plotSeries(name, seriesList, subtitle="", parameters=None,
               fmt='pdf', directory='.', xlabel='Sweep', ylabel=None, ybounds=None):
    plt.figure()
    plt.clf()
    plt.title('Series for ' + name + '\n' + subtitle)
    plt.xlabel(xlabel)
    if ylabel is None:
        ylabel = name
    plt.ylabel(ylabel)
    if parameters is not None:
        showParameters(parameters)

    for series in seriesList:
        plt.plot(series.xvals(), series.values, label=series.label)

    legend_outside()
    setYBounds(seriesList, ybounds)

    filename = directory + name.replace(' ', '_') + '_series.' + fmt
    savefig_legend_outside(filename)

# Plots histograms for a set of series.
def plotHistogram(name, seriesList, subtitle="", parameters=None,
                  fmt='pdf', directory='.', xlabel=None, ylabel='Frequency', bins=20):
    plt.figure()
    plt.clf()
    plt.title('Histogram of ' + name + '\n' + subtitle)
    if xlabel is None:
        xlabel = name
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if parameters is not None:
        showParameters(parameters)

    # FIXME: choose a better bin size
    plt.hist([series.values for series in seriesList], bins=bins, label=[series.label for series in seriesList])
    legend_outside()

    filename = directory + name.replace(' ', '_') + '_hist.' + fmt
    savefig_legend_outside(filename)

from collections import namedtuple
from matplotlib import cm

# Sets key to value and returns the updated dictionary.
def addToDict(dictionary, key, value):
    answer = copy.copy(dictionary)
    answer[key] = value
    return answer

# Produces plots for a given variable over a set of runs.
# Variable parameters are the x-axis, 'seriesName' is the y-axis.
# If aggregate=True, multiple plots that differ in only one parameter are overlayed.
def plotAsymptotics(parameters, histories, seriesName, fmt='pdf', directory=None, aggregate=False):
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
                    showParameters(params)

                    colors = cm.rainbow(np.linspace(0, 1, len(otherValues)))

                    # For each setting of the aggregate parameter, plot the values with respect to the x-axis parameter.
                    for (otherValue, c) in zip(otherValues, colors):
                        p = addToDict(params, other, otherValue)
                        plt.scatter(values, [paramsToValue[Key(**addToDict(p, key, value))] for value in values],
                                    label=other+'='+str(otherValue), color=c)

                    #plt.legend()
                    legend_outside()

                    filename = key
                    for (param, value) in params.items():
                        filename += '_' + param + '=' + str(value)

                    #plt.tight_layout()
                    #fig.savefig(directory + filename.replace(' ', '_') + '_asymptotics.' + fmt, format=fmt)
                    filename = directory + filename.replace(' ', '_') + '_asymptotics.' + fmt
                    savefig_legend_outside(filename)
        else:
            for params in cartesianProduct(others):
                fig = plt.figure()
                plt.clf()
                plt.title(seriesName + ' versus ' + key)
                plt.xlabel(key)
                plt.ylabel(seriesName)
                showParameters(params)

                plt.scatter(values, [paramsToValue[Key(**addToDict(params, key, v))] for v in values])

                filename = key
                for (param, value) in params.items():
                    filename += '_' + param + '=' + str(value)

                #plt.tight_layout()
                fig.savefig(directory + filename.replace(' ', '_') + '_asymptotics.' + fmt, format=fmt)


def legend_outside(ax=None, bbox_to_anchor=(0.5, -.10), loc='upper center',
                   ncol=None, label_cmp=None):
    # labels must be set in original plot call: plot(..., label=label)
    if ax is None:
        ax = pylab.gca()
    handles, labels = ax.get_legend_handles_labels()
    label_to_handle = dict(zip(labels, handles))
    labels = label_to_handle.keys()
    if label_cmp is not None:
        labels = sorted(labels, cmp=label_cmp)
    handles = [label_to_handle[label] for label in labels]
    if ncol is None:
        ncol = min(len(labels), 3)
    ax.legend(handles, labels, loc=loc, ncol=ncol,
              bbox_to_anchor=bbox_to_anchor, prop={"size":14})
    return

def savefig_legend_outside(filename, ax=None, bbox_inches='tight'):
    if ax is None:
        ax = pylab.gca()
    lgd = ax.get_legend()
    pylab.savefig(filename,
                  bbox_extra_artists=(lgd,),
                  bbox_inches=bbox_inches,
                  )
    return
