# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

import pylab
import cPickle as pickle
import os
import copy
import numpy as np
import random
import matplotlib.pyplot as plt

from utils import cartesianProduct, makeIterable


def plot(type):
    return type in {'boolean', 'real', 'number', 'atom', 'count'}


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
        self.data = []

        self.nameToType = {}

    @staticmethod
    def fromRuns(runs):
        if len(runs) == 0:
            return History()
        else:
            answer = History(runs[0].label, runs[0].parameters)
            for r in runs: answer.addRun(r)
            return answer

    def addSeries(self, name, type, label, values, hist=True):
        self._addSeries(name, type, Series(label, values, hist))

    def _addSeries(self, name, type, series):
        if name not in self.nameToSeries:
            self.nameToSeries[name] = []
            self.nameToType[name] = type
        self.nameToSeries[name].append(series)

    def addRun(self, run):
        #assert run.parameters == self.parameters
        ## don't want different seeds to preventing adding runs
        for (name, series) in run.namedSeries.iteritems():
            self._addSeries(name, run.nameToType[name], series)

    def addData(self, data):
        'Extend list of data. Input: data::[(exp,value)]'
        self.data.extend(data)

    def addDataset(self,dataset):
        'Input: dataset :: [(exp,value)]'
        self.data.append(dataset)

    def addGroundTruth(self,groundTruth,totalSamples):
        '''Add Series to self.nameToValues for true parameter values.
           Series will be displayed on plots.
           Inputs: groundTruth :: {symbol/expression:value}
                   totalSamples :: int
                      Length of Series in self.nameToValues.'''
        self.groundTruth = groundTruth

        for exp,value in self.groundTruth.iteritems():
            type = value['type']
            value = value['value'] # FIXME do with parseValue
            values=[value]*totalSamples # pad out with totalSamples for plotting
            self.addSeries(exp,type,'gTruth',values)

        ## FIXME GroundTruth Series must be removed from snapshots

    def sampleRuns(self,numSamples):
        '''Returns new History with pointers to *numSamples* randomly
        sampled Runs from self'''
        newHistory=History(label= self.label+'_sampled', parameters=self.parameters)

        noRuns = len(self.nameToSeries.items()[0][1])
        indices = random.sample(xrange(noRuns),numSamples)

        for name,listSeries in self.nameToSeries.iteritems():
            type = self.nameToType[name]
            subList = [listSeries[i] for i in indices]
            for s in subList:
                newHistory.addSeries(name, type, s.label, s.values, hist=s.hist)

        ## FIXME: addData and addGroundTruth (generally COPY HISTORY)
        return newHistory


    def averageValue(self, seriesName):
        'Returns the average over all series with the given name.'
        flatSeries = []
        for series in self.nameToSeries[seriesName]:
            if 'gtruth' not in series.label.lower():
                flatSeries.extend(series.values)
        return np.mean(flatSeries)

    def historyToSnapshots(self):
        '''
        Snapshot of values across series for each time-step.
        Created by copying scalar values from nameToSeries.
        Output = {name:[ snapshot_i ] }, where snapshot_i
        is [series.value[i] for series in nameToSeries[name]]'''
        snapshots={}
        # always ignore sweep time for snapshots
        ignore=('sweep time','sweep_iters')
        for name,listSeries in self.nameToSeries.iteritems():
            if any([s in name.lower() for s in ignore]):
                continue
            arrayValues = np.array( [s.values for s in listSeries] )
            snapshots[name] = map(list,arrayValues.T)
        return snapshots


    def compareSnapshots(self, names=None, probes=None):
        '''
        Compare samples across runs at two different probe points
        in History. Defaults to comparing all names and probes =
        (midPoint,lastPoint).'''

        allSnapshots = self.historyToSnapshots()
        samples = len(allSnapshots.items()[0][1])

        # restrict to probes
        probes = (int(.5*samples),-1) if probes is None else probes
        assert len(probes)==2

        # restrict to names
        if names is not None:
            filterSnapshots = filterDict(allSnapshots,keep=names)
        else:
            filterSnapshots = allSnapshots

        snapshotDicts=({},{})
        for name,snapshots in filterSnapshots.iteritems():
            for snapshotDict,probe in zip(snapshotDicts,probes):
                snapshotDict[name]=snapshots[probe]

        labels =[self.label+'_'+'snap_%i'%i for i in probes]
        return compareSampleDicts(snapshotDicts,labels,plot=True)

    # default directory for plots, created from parameters
    def defaultDirectory(self):
        name = self.label
        for (param, value) in self.parameters.iteritems():
            name += '_' + param + '=' + str(value)
        return name + '/'

    # directory specifies location of plots
    # default format is pdf
    def plot(self, fmt='pdf', directory=None):
        '''plot(fmt='pdf', directory=None)

           Save time-series and histogram for each name in self.nameToSeries.
           Default directory is given by self.defaultDirectory().'''
        self.save(directory)
        if directory == None:
            directory = self.defaultDirectory()

        ensure_directory(directory)

        for name in self.nameToSeries:
            if plot(self.nameToType[name]):
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
    def plotOneSeries(self, name, **kwargs):
        self._plotOne(plotSeries, name, **kwargs)

    def quickPlot(self, name, **kwargs):
        '''quickPlot( name, **kwargs)

           Show time-series plot of series in self.nameToSeries[name]
           with default labeling and formatting.

           Arguments
           ---------
           name :: string
             String in nameToSeries.keys() and either model.assumes
             or model.queryExps.
           ylabel :: string
           limitLegend :: int
             Limit how many series are listed on the legend. (To limit
             how many series are plotted, use self.sampleRuns).

           '''
        self._plotOne(plotSeries, name, save=False, show=True, **kwargs)

    def _plotOne(self, f, name, directory=None, **kwargs):
        if directory == None:
            directory = self.defaultDirectory()
        # ENS remove
        #ensure_directory(directory)
        if name in self.nameToSeries:
            f(name, self.nameToSeries[name], subtitle=self.label,
              parameters=self.parameters, directory=directory, **kwargs)
        else:
            raise Exception("Cannot plot non-existent series %s" % name)

    def plotOneHistogram(self, name, **kwargs):
        self._plotOne(plotHistogram, name, **kwargs)

    def quickHistogram(self, name, **kwargs):
        self._plotOne(plotHistogram, name, save=False, show=True, **kwargs)

    def quickScatter(self, name1, name2, **kwargs):
        if name1 in self.nameToSeries and name2 in self.nameToSeries:
            scatterPlotSeries(name1, self.nameToSeries[name1], name2, self.nameToSeries[name2],
                              subtitle=self.label, parameters=self.parameters, save=False, show=True, **kwargs)
        else:
            if name1 not in self.nameToSeries:
                raise Exception("Cannot plot non-existent series %s" % name1)
            else:
                raise Exception("Cannot plot non-existent series %s" % name2)

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


### Analysis Functions for History
from venture.test.stats import reportSameContinuous
import scipy.stats

def flattenRuns(history):
    '''Copy values from each series into one (flat) series and
       create new History'''
    newHistory = History(history.label,history.parameters)
    for name,listSeries in history.nameToSeries.iteritems():
        label = 'flattened_'+listSeries[0].label+'...'
        hist = listSeries[0].hist
        type = history.nameToType[name]
        flatValues = [el for series in listSeries for el in series.values]
        newHistory.addSeries(name,type,label,flatValues,hist=hist)
    return newHistory


def plotSnapshot(history,name,probe=-1):
    allSnapshots = history.historyToSnapshots()
    snap = allSnapshots[name][probe]
    title = 'Histogram: '+ name+'_snapshot_%i'%probe
    fig,ax = plt.subplots(figsize = (4,3))
    ax.hist(snap,bins=20,alpha=0.8,color='c')
    ax.set_xlabel(name)
    ax.set_ylabel('frequency')
    ax.set_title(title)
    return snap,fig


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


def filterDict(d,keep=(),ignore=()):
    '''Shallow copy of dictionary d filtered on keys.
       If *keep* nonempty copy its members. Else: copy items not in *ignore*'''
    assert isinstance(keep,(tuple,list))
    if keep:
        return dict([(k,v) for k,v in d.items() if k in keep])
    else:
        return dict([(k,v) for k,v in d.items() if k not in ignore])


def intersectKeys(dicts):
    return tuple(set(dicts[0].keys()).intersection(set(dicts[1].keys())))


class CompareSamplesReport(object):
    def __init__(self,labels,reportString=None,statsDict=None,compareFig=None):
        self.labels = labels
        if reportString:
            self.reportString = reportString
        if statsDict:
            self.statsDict = statsDict
        if compareFig:
            self.compareFig = compareFig


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
    statsString = ' '.join(['mean','std_err','median','N'])
    statsDict = {}
    report = ['compareSampleDicts: %s vs. %s \n'%(labels[0],labels[1])]

    for exp in intersectKeys(dicts):
        report.append( '\n---------\n Name:  %s \n'%exp )
        statsDict[exp] = {}

        for dict_i,label_i in zip(dicts,labels):
            samples=dict_i[exp]
            s_stats = tuple([s(samples) for s in stats])
            statsDict[exp]['stats: '+statsString]=s_stats
            labelStr='%s : %s ='%(label_i,statsString)
            report.append( labelStr+'  %.3f  %.3f  %.3f  %i\n'%s_stats )

        testResult=reportSameContinuous(dicts[0][exp],dicts[1][exp])
        ksOut='KS Test:   '+ '  '.join(testResult.report.split('\n')[-2:])
        report.append( ksOut )
        statsDict[exp]['KSSameContinuous']=testResult

    repSt = ' '.join(report)
    compareFig = qqPlotAll(dicts,labels) if plot else None
    return CompareSamplesReport(labels,repSt,statsDict,compareFig)


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

#
# TODO Parameters have to agree for now
# FIXME does nameToType work with histOverlay?
# TODO have a sensible default naming (for convenience)
def historyOverlay(name, named_hists):
    ''':: string -> [(string,History)] -> History containing all those
    time series overlaid'''
    answer = History(label=name, parameters=named_hists[0][1].parameters)
    for (subname,subhist) in named_hists:
        for (seriesname,seriesSet) in subhist.nameToSeries.iteritems():
            seriesType = subhist.nameToType[seriesname]
            for subseries in seriesSet:
                answer.addSeries( seriesname, seriesType,
                                  subname+"_"+subseries.label,
                                  subseries.values, hist=subseries.hist)

    for (subname,subhist) in named_hists:
        answer.addDataset(subhist.data)
    return answer


def historyStitch(hists,nansAtStitches=False):
    '''Mutate hists[0] by appending values (in order) from rest of hists'''
    h0 = hists[0]
    h0.label + '--1st of %i stitched hists'%len(hists)
    for h in hists[1:]:
        for name,_ in h.nameToSeries.iteritems():
            h_values = h.nameToSeries[name][0].values
            h0.nameToSeries[name][0].values.extend( h_values )
            if nansAtStitches:
                h0.nameToSeries[name][0].values.extend( [NaN]*20 )

    return h0


class Run(object):
    """Data from a single run of a model.  A History is effectively a set
of Runs with the same label and parameters (but represented
differently)."""
    def __init__(self, label='empty_run', parameters=None, data=None):
        if parameters is None: parameters = {}
        if data is None: data = {}
        self.label = label # string
        self.parameters = parameters # :: {string: a}
        self.namedSeries = {}
        for (name, series) in data.iteritems():
            self.namedSeries[name] = series
        self.nameToType = {}

    #TODO Store the type somewhere
    def addSeries(self, name, type, series):
        self.nameToType[name] = type
        self.namedSeries[name] = series

# aggregates values for one variable over the course of a run
class Series(object):
    def __init__(self, label, values, hist=True, xvals=None):
        self.label = label   # string
        self.values = values # [a]
        # Boolean indicating whether this series is meant to be histogrammed
        self.hist = hist     # Appears to be unused TODO remove?
        self._xvals = xvals  # Maybe [Number] the ordinate values to plot at

    def xvals(self):
        if self._xvals is not None:
            return self._xvals
        else:
            return range(len(self.values)) # Should be the same as plotting just the values

# Displays parameters in top-left corner of the graph.
def showParameters(parameters):
    if len(parameters) == 0: return

    items = sorted(parameters.items())

    text = items[0][0] + ' = ' + str(items[0][1])
    for (name, value) in items[1:]:
        # TODO: something more principled to truncate overly long parameter values
        text += '\n' + name + ' = ' + str(value)[:20]

    plt.text(0, 1, text, transform=plt.axes().transAxes, va='top', size='small', linespacing=1.0)

def seriesBounds(seriesList):
    vmin = min([np.min(series.values) for series in seriesList])
    vmax = max([np.max(series.values) for series in seriesList])
    offset = 0.1 * max([(vmax - vmin), 1.0])
    return (vmin - offset, vmax + offset)

def setYBounds(seriesList, ybounds=None):
    if ybounds is None:
        (ylow, yhigh) = seriesBounds(seriesList)
        if not any([np.any([np.isinf(v) for v in series.values]) for series in seriesList]):
            plt.ylim([ylow, yhigh])
    else:
        [ylow,yhigh] = ybounds # Silly pylint not noticing case on maybe type pylint:disable=unpacking-non-sequence
        plt.ylim([ylow,yhigh])

# Plots a set of series.
def plotSeries(name, seriesList, subtitle="", xlabel='Sweep', **kwargs):
    _plotPrettily(_doPlotSeries, name, seriesList, title='Series for ' + name + '\n' + subtitle,
                  filesuffix='series', xlabel=xlabel, **kwargs)

def _doPlotSeries(seriesList, ybounds=None,**kwargs):
    for series in seriesList:
        if series.label and 'gtruth' in series.label.lower():
            plt.plot(series.xvals(), series.values,linestyle=':',
                     markersize=6, label=series.label)
        else:
            plt.plot(series.xvals(), series.values, label=series.label)
    setYBounds(seriesList, ybounds)

# Plots histograms for a set of series.
def plotHistogram(name, seriesList, subtitle="", ylabel='Frequency', **kwargs):
    _plotPrettily(_doPlotHistogram, name, seriesList, title='Histogram of ' + name + '\n' + subtitle,
                  filesuffix='hist', ylabel=ylabel, **kwargs)

def _doPlotHistogram(seriesList, bins=20):
    # FIXME: choose a better bin size
    plt.hist([series.values for series in seriesList], bins=bins, label=[series.label for series in seriesList])

def scatterPlotSeries(name1, seriesList1, name2, seriesList2, subtitle="", **kwargs):
    name = "%s vs %s" % (name2, name1)
    _plotPrettily(_doScatterPlot, name, [seriesList1, seriesList2], title="Scatter of %s\n%s" % (name, subtitle),
                  filesuffix='scatter', xlabel=name1, ylabel=name2, **kwargs)

def _doScatterPlot(data, style=' o', ybounds=None, contour_func=None, contour_delta=0.125):
    ## FIXME: correct this
    xSeries, ySeries = data
    for (xs, ys) in zip(xSeries, ySeries):
        plt.plot(xs.values, ys.values, style,label=xs.label) # Assume ys labels are the same
                 #marker='+',
                 #lw=.2,markersize=.4,

        setYBounds(ySeries, ybounds)
    if contour_func is not None:
        [xmin, xmax] = seriesBounds(xSeries)
        [ymin, ymax] = seriesBounds(ySeries)
        plotContours(xmin, xmax, ymin, ymax, contour_func, contour_delta)

def plotContours(xmin, xmax, ymin, ymax, contour_func, contour_delta):
    x = np.arange(xmin, xmax, contour_delta)
    y = np.arange(ymin, ymax, contour_delta)
    X, Y = np.meshgrid(x, y)
    Z = np.vectorize(contour_func)(X,Y)
    plt.contour(X, Y, Z)

def _plotPrettily(f, name, data, title="", parameters=None, filesuffix='',
                  fmt='pdf', directory='.', xlabel=None, ylabel=None, show=False, save=True, **kwargs):
    plt.figure()
    plt.clf()
    plt.title(title)
    if xlabel is None:
        xlabel = name
    plt.xlabel(xlabel)
    if ylabel is None:
        ylabel = name
    plt.ylabel(ylabel)
    if parameters is not None:
        showParameters(parameters)

    f(data, **kwargs)

    legend_outside(**kwargs)


    if save:
        ensure_directory(directory)
        filename = directory + name.replace(' ', '_') + '_' + filesuffix + '.' + fmt
        savefig_legend_outside(filename)
    if show:
        plt.show()

from collections import namedtuple
from matplotlib import cm

# Sets key to value and returns the updated dictionary.
def addToDict(dictionary, key, value):
    answer = copy.copy(dictionary)
    answer[key] = value
    return answer


#TODO probably bit-rotted
# is meant to work with *parameters* dict from VentureUnit object
# need to adjust Unit/Analytics or function below to make
# it easy to plot e.g. number of observes vs. runtime.

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
                    ensure_directory(directory)
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
                ensure_directory(directory)
                fig.savefig(directory + filename.replace(' ', '_') + '_asymptotics.' + fmt, format=fmt)


def legend_outside(ax=None, bbox_to_anchor=(0.5, -.05), loc='upper center',
                   ncol=None, label_cmp=None, limitLegend=8,**kwargs):
    # labels must be set in original plot call: plot(..., label=label)
    if ax is None:
        ax = pylab.gca()
    handles, labels = ax.get_legend_handles_labels()

    if len(handles)>limitLegend:
        title='(%i data-series of %i not shown on legend)'%( (len(handles)-limitLegend),len(handles) )
    else:
        title = None

    label_to_handle = dict(zip(labels, handles)[:limitLegend])

    # always include groundTruth on legend
    for label,handle in zip(labels,handles):
        if 'gtruth' in label.lower():
            label_to_handle[label] = handle

    labels = label_to_handle.keys()
    if label_cmp is not None:
        labels = sorted(labels, cmp=label_cmp)
    handles = [label_to_handle[label] for label in labels]
    if ncol is None:
        ncol = min(len(labels), 4)


    ax.legend(handles, labels, loc=loc, ncol=ncol, title=title,
              bbox_to_anchor=bbox_to_anchor, prop={"size":10})
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

