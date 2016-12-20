import time
import os
import random
from collections import OrderedDict
#TODO: clean up this mess of imports
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.colors import BoundaryNorm
from matplotlib.colors import LogNorm
from matplotlib import colors, ticker, cm
import matplotlib
import pandas as pd
import numpy as np
import seaborn

import venture.lite.types as t
from venture.lite.sp_help import deterministic_typed
import venture.lite.value as v
import scipy.ndimage as ndimage

def new_figure():
    plt.figure()

def make_title(title, width=6, height=6):
    try:
       axes
    except:
        ax = plt.gca()
    else:
        if not axes:
            fig, ax = plt.subplots(1,1, figsize=(width, height))
        else:
            ax = plt.gca()
    ax.set_title(title, fontsize=20)

def legend():
    ax = plt.gca()
    handles, labels = ax.get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles))
    legend_object = ax.legend(by_label.values(), by_label.keys(), 
    fontsize=15, frameon = 1)
    for l in legend_object.get_lines():
        l.set_alpha(1)
    legend_object.get_frame().set_facecolor('white')

def scatter_plot(x, y, dict_of_plotting_parameters={}):
    seaborn.set()
    if "width" in dict_of_plotting_parameters:
        width = dict_of_plotting_parameters["width"].getNumber()
    else:
        width = 6
    if "height" in dict_of_plotting_parameters:
        height  = dict_of_plotting_parameters["height"].getNumber()
    else:
        height = 6
    
    if "alpha" in dict_of_plotting_parameters:
        alpha = dict_of_plotting_parameters["alpha"].getNumber()
    else:
        alpha = 1

    if "marker" in dict_of_plotting_parameters:
        marker = dict_of_plotting_parameters["marker"].getString()
    else:
        marker = "x" 

    if "label" in dict_of_plotting_parameters:
        label = dict_of_plotting_parameters["label"].getString()
    else:
        label = None 

    if "color" in dict_of_plotting_parameters:
        color = dict_of_plotting_parameters["color"].getString()
    else:
        color = "k" 

    if "markersize" in dict_of_plotting_parameters:
        markersize = dict_of_plotting_parameters["markersize"].getNumber()
    else:
        markersize = 200

    if "fontsize_scale" in dict_of_plotting_parameters:
        fontsize_scale = dict_of_plotting_parameters["fontsize_scale"].getNumber()
    else:
        fontsize_scale = 1

    if "seaborn_style" in dict_of_plotting_parameters:
        seaborn_style =  dict_of_plotting_parameters["seaborn_style"].getString()
        change_seaborn_style = True 
    else:
        change_seaborn_style = False 
 
    if change_seaborn_style:
        seaborn.set_style(seaborn_style)

    fig = plt.gcf()
    if fig is not None:
        fig.set_size_inches(width, height)
    else:
        plt.figure(figsize=(width, height))

    plt.scatter(x, y, zorder=2, alpha=alpha, marker=marker,
        s=markersize, linewidths=2, color = color, label=label)

    if "title" in dict_of_plotting_parameters:
        plt.title(dict_of_plotting_parameters["title"].getString(),
            fontsize=20 * fontsize_scale)

    if "xlabel" in dict_of_plotting_parameters:
        plt.xlabel(dict_of_plotting_parameters["xlabel"].getString(),
            fontsize=20 * fontsize_scale)
    if "ylabel" in dict_of_plotting_parameters:
        plt.ylabel(dict_of_plotting_parameters["ylabel"].getString(),
            fontsize=20 * fontsize_scale)
    if "xlim" in dict_of_plotting_parameters:
        plt.xlim([lim.getNumber() for lim in dict_of_plotting_parameters["xlim"].getArray()])
    if "ylim" in dict_of_plotting_parameters:
        plt.ylim([lim.getNumber() for lim in dict_of_plotting_parameters["ylim"].getArray()])

    ax = plt.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(15 * fontsize_scale) 
    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(15 * fontsize_scale) 

def dist_plot(x, dict_of_plotting_parameters={}):
    ax = seaborn.distplot(x)
    if "xlabel" in dict_of_plotting_parameters:
        plt.xlabel(dict_of_plotting_parameters["xlabel"].getString(),
            fontsize=20)
    if "ylabel" in dict_of_plotting_parameters:
        plt.ylabel(dict_of_plotting_parameters["ylabel"].getString(),
            fontsize=20)
    if "xlim" in dict_of_plotting_parameters:
        plt.xlim([lim.getNumber() for lim in dict_of_plotting_parameters["xlim"].getArray()])
    if "ylim" in dict_of_plotting_parameters:
        plt.ylim([lim.getNumber() for lim in dict_of_plotting_parameters["ylim"].getArray()])

def line_plot(x, y, dict_of_plotting_parameters={}):
    seaborn.set()
    if "alpha" in dict_of_plotting_parameters:
        alpha = dict_of_plotting_parameters["alpha"].getNumber()
    else:
        alpha = 1
    if "width" in dict_of_plotting_parameters:
        width = dict_of_plotting_parameters["width"].getNumber()
    else:
        width = 6
    if "height" in dict_of_plotting_parameters:
        height  = dict_of_plotting_parameters["height"].getNumber()
    else:
        height = 6
    if "color" in dict_of_plotting_parameters:
        color = dict_of_plotting_parameters["color"].getString()
    else:
        color = "green"
    if "label" in dict_of_plotting_parameters:
        label = dict_of_plotting_parameters["label"].getString()
    else:
        label = None
    if "fontsize_scale" in dict_of_plotting_parameters:
        fontsize_scale = dict_of_plotting_parameters["fontsize_scale"].getNumber()
    else:
        fontsize_scale = 1
    if "hide_first_xtick" in dict_of_plotting_parameters:
        hide_first_xtick = dict_of_plotting_parameters["hide_first_xtick"].getBool()
    else:
        hide_first_xtick = False 

    if "line_width" in dict_of_plotting_parameters:
        line_width = dict_of_plotting_parameters["line_width"].getNumber()
    else:
        line_width =  1.
    if "seaborn_style" in dict_of_plotting_parameters:
        seaborn_style =  dict_of_plotting_parameters["seaborn_style"].getString()
        change_seaborn_style = True 
    else:
        change_seaborn_style = False 
 
    if change_seaborn_style:
        seaborn.set_style(seaborn_style)

    fig = plt.gcf()
    if fig is not None:
        fig.set_size_inches(width, height)
    else:
        plt.figure(figsize=(width, height))
    plt.plot(x, y, color=color, alpha=alpha, label=label, lw=line_width)

    if "title" in dict_of_plotting_parameters:
        plt.title(dict_of_plotting_parameters["title"].getString(),
            fontsize=20 * fontsize_scale)

    if "xlabel" in dict_of_plotting_parameters:
        plt.xlabel(dict_of_plotting_parameters["xlabel"].getString(),
            fontsize=20 * fontsize_scale)
    if "ylabel" in dict_of_plotting_parameters:
        plt.ylabel(dict_of_plotting_parameters["ylabel"].getString(),
            fontsize=20 * fontsize_scale)
    if "xlim" in dict_of_plotting_parameters:
        plt.xlim([lim.getNumber() for lim in dict_of_plotting_parameters["xlim"].getArray()])
    if "ylim" in dict_of_plotting_parameters:
        plt.ylim([lim.getNumber() for lim in dict_of_plotting_parameters["ylim"].getArray()])

    ax = plt.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(15 * fontsize_scale) 
    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(15 * fontsize_scale) 

    # quick and dirty for figure production:  remove the first label.
    if (hide_first_xtick):
        xticks = ax.xaxis.get_major_ticks()
        xticks[0].label1.set_visible(False)
    return 0


def kde_plot(x, y, dict_of_plotting_parameters):
    seaborn.set_style("white") 

    if "colormap" in dict_of_plotting_parameters:
        cmap= dict_of_plotting_parameters["colormap"].getString()
    else:
        cmap="Greens"

    if "xlabel" in dict_of_plotting_parameters:
        xlabel = dict_of_plotting_parameters["xlabel"].getString()
        plt.xlabel(xlabel, fontsize=15)
    else:
        raise ValueError("""xlabel must be provided in the
            dict for plotting-parameters""")

    if "ylabel" in dict_of_plotting_parameters:
        ylabel = dict_of_plotting_parameters["ylabel"].getString()
        plt.ylabel(ylabel, fontsize=15)
    else:
        raise ValueError("""ylabel must be provided in the
            dict for plotting-parameters""")

    ax = seaborn.kdeplot(np.array(x), np.array(y), shade=True, cmap=cmap)
    ax.collections[0].set_alpha(0)


    if "title" in dict_of_plotting_parameters:
        plt.title(dict_of_plotting_parameters["title"].getString(), fontsize=20)

    if "xlim" in dict_of_plotting_parameters:
        plt.xlim([lim.getNumber() for lim in dict_of_plotting_parameters["xlim"].getArray()])
    if "ylim" in dict_of_plotting_parameters:
        plt.ylim([lim.getNumber() for lim in dict_of_plotting_parameters["ylim"].getArray()])
        

def drop_duplicates(x, y):
    df = pd.DataFrame({"x":x, "y":y})
    df = df.drop_duplicates(subset=["x","y"])
    return df["x"], df["y"]

def trajectory_plot(x, y, dict_of_plotting_parameters):
  
    try:
       axes
    except:
        ax = plt.gca()
        fig = plt.gcf()
    else:
        if not axes:
            fig, ax = plt.subplots(1,1, figsize=(6,6))
        else:
            ax = plt.gca()
            fig = plt.gcf()

    if "xlabel" in dict_of_plotting_parameters:
        xlabel = dict_of_plotting_parameters["xlabel"].getString()
    else:
        raise ValueError("""xlabel must be provided in the
            dict for plotting-parameters""")

    if "ylabel" in dict_of_plotting_parameters:
        ylabel = dict_of_plotting_parameters["ylabel"].getString()
    else:
        raise ValueError("""ylabel must be provided in the
            dict for plotting-parameters""")
   
    if "title" in dict_of_plotting_parameters:
        ax.set_title(dict_of_plotting_parameters["title"].getString(), fontsize=20)
    
    number_of_total_sweeps = len(x)
    x,y = drop_duplicates(x, y)

    transition_color = np.linspace(0,1,len(x)) 

    # TODO - make this more robust
    if "plot_as_scatter_from" in dict_of_plotting_parameters:
        n_trajectory = int(dict_of_plotting_parameters["plot_as_scatter_from"].getNumber() -1)
    else:
        n_trajectory = len(x)

    if n_trajectory > len(x):
        n_trajectory = len(x)

    # Set the colormap and norm to correspond to the data for which
    # the colorbar will be used.
    cmap = plt.cm.Greens_r

    ax.plot(x[:n_trajectory], y[:n_trajectory],
        color="gray", zorder = 2, label = "" )
    ax.scatter(x[0], y[0],
        c="white", s=100,
        zorder = 0, label="First of the first %d accepted transitions" % (n_trajectory,))
    ax.scatter(x[:n_trajectory], y[:n_trajectory],
        c=range(n_trajectory), cmap=cmap, s=100,
        zorder = 3, label="Last of the first %d accepted transitions" % (n_trajectory,))
    if n_trajectory < len(x):
        ax.scatter(x[n_trajectory:], y[n_trajectory:],
            label = "Rest of the %d accepted transitions" %\
            (len(x),), zorder = 4) 

    if "xlim" in dict_of_plotting_parameters:
        plt.xlim([lim.getNumber() for lim in dict_of_plotting_parameters["xlim"].getArray()])
    if "ylim" in dict_of_plotting_parameters:
        plt.ylim([lim.getNumber() for lim in dict_of_plotting_parameters["ylim"].getArray()])
    plt.xlabel(xlabel, fontsize=15)
    plt.ylabel(ylabel, fontsize=15)
  
    ax.legend()
    leg = ax.get_legend()
    leg.legendHandles[0].set_color("green")
    leg.legendHandles[1].set_color("white")
    
    '''
    Make a colorbar as a separate figure.
    '''
    # define the colormap
    cmap = plt.cm.Greens_r
    # extract all colors from the .jet map
    cmaplist = [cmap(i) for i in range(cmap.N)]

    # define the bins and normalize
    bounds = np.linspace(0, n_trajectory -1 , n_trajectory)
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)


    # create a second axes for the colorbar
    ax2 = fig.add_axes([0.95, 0.1, 0.03, 0.8])
    cb = matplotlib.colorbar.ColorbarBase(ax2, cmap=cmap, norm=norm, spacing='proportional', ticks=bounds, boundaries=bounds, format='%1i')


    ax2.set_ylabel("Color indicates the i'th accepted transition", size=15)  
 
def density_line_plot(dataset, dict_of_plotting_parameters):
    seaborn.set()

    # got to select subsamples of the pdf.
    df = dataset.datum.asPandas()
    # last of the column is the collected variable
    x = range(len(df))
    y = df["prt. log wgt."]
    plt.plot(x, y, linestyle="--", marker="o")
    #df["prt. log wgt."].iloc[::10].plot(kind="bar")
    if "title" in dict_of_plotting_parameters:
        plt.title(dict_of_plotting_parameters["title"].getString(), fontsize=20)

    if "xlabel" in dict_of_plotting_parameters:
        plt.xlabel(dict_of_plotting_parameters["xlabel"].getString(),
            fontsize=15)
    if "ylabel" in dict_of_plotting_parameters:
        plt.ylabel(dict_of_plotting_parameters["ylabel"].getString(),
            fontsize=15)
 

def density_bar_plot(dataset, dict_of_plotting_parameters):
    seaborn.set()

    # got to select subsamples of the pdf.
    df = dataset.datum.asPandas()
    # last of the column is the collected variable
    print df["prt. log wgt."]
    df["prt. log wgt."].plot(kind="bar")
    #df["prt. log wgt."].iloc[::10].plot(kind="bar")
    if "title" in dict_of_plotting_parameters:
        plt.title(dict_of_plotting_parameters["title"].getString(), fontsize=20)

    if "xlabel" in dict_of_plotting_parameters:
        plt.xlabel(dict_of_plotting_parameters["xlabel"].getString(),
            fontsize=15)
    plt.ylabel("Density", fontsize=15)
 
def hist_plot(data_array):
    seaborn.set()
    if  all(isinstance(datum, v.VentureString) for datum in data_array):
        data_array = [datum.getString() for datum in data_array]
    elif  all(isinstance(datum, v.VentureNumber) for datum in data_array):
        data_array = [datum.getNumber() for datum in data_array]

    df = pd.DataFrame({"data":data_array})
    # last of the column is the collected variable
    df[df.columns[-1]].value_counts().plot(kind="bar")
    plt.ylabel("Frequency of Samples", fontsize=15)

    ax = plt.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(15) 

def heatmap(dataset, dict_of_plotting_parameters):
    seaborn.set_style("white")
    df = dataset.datum.asPandas()
    # last of the column is the collected variable
    if "xlabel" in dict_of_plotting_parameters:
        xlabel = dict_of_plotting_parameters["xlabel"].getString()
    else:
        raise ValueError("""xlabel must be provided in the
            dict for plotting-parameters""")

    if "ylabel" in dict_of_plotting_parameters:
        ylabel = dict_of_plotting_parameters["ylabel"].getString()
    else:
        raise ValueError("""ylabel must be provided in the
            dict for plotting-parameters""")

    x = df[xlabel]
    y = df[ylabel]
    particle_weights = 0 - df["prt. log wgt."]
    plt.hist2d(x,y, bins = 40, weights = particle_weights, # normalize by
    # subtract max, possibly show the max on the side that I subtraced of. : 
        norm=colors.LogNorm(vmin=np.min(particle_weights),
        vmax=np.max(particle_weights)),  cmap = matplotlib.cm.afmhot_r)
    #seaborn.distplot(particle_weights)
    #plt.scatter(x,y,edgecolors='none',s=1,c=particle_weights ,
    #            norm=colors.LogNorm())

    if "xlim" in dict_of_plotting_parameters:
        plt.xlim([lim.getNumber() for lim in dict_of_plotting_parameters["xlim"].getArray()])
    if "ylim" in dict_of_plotting_parameters:
        plt.ylim([lim.getNumber() for lim in dict_of_plotting_parameters["ylim"].getArray()])

    if "title" in dict_of_plotting_parameters:
        plt.title(dict_of_plotting_parameters["title"].getString(), fontsize=20)

    plt.xlabel(xlabel, fontsize=15)
    plt.ylabel(ylabel, fontsize=15)
    
    return 0

def simple_contour_plot(x,y,z, dict_of_plotting_parameters={}):
    seaborn.set_style("white") 
    if "width" in dict_of_plotting_parameters:
        width = dict_of_plotting_parameters["width"].getNumber()
    else:
        width = 8
    if "height" in dict_of_plotting_parameters:
        height  = dict_of_plotting_parameters["height"].getNumber()
    else:
        height = 6


    Z = np.array(z).reshape(len(x),len(y))

    cmap ="magma"

    fig = plt.gcf()
    try:
        axes = fig.get_axes()
        ax = axes[0]
    except:
        ax = plt.gca()
            
    if "extent" in dict_of_plotting_parameters:
        extent = [dim.getNumber() for dim in dict_of_plotting_parameters["extent"].getArray()]
        cax = ax.imshow(Z, interpolation='bilinear', origin='lower', aspect='auto',
                    cmap=cmap, extent=(extent[0], extent[1], extent[2], extent[3]))
    else:
        cax = ax.imshow(Z, interpolation='bilinear', origin='lower', aspect='auto',
                    cmap=cmap)
   
    if "xlim" in dict_of_plotting_parameters:
        xmin = dict_of_plotting_parameters["xlim"].getArray()[0].getNumber()
        xmax = dict_of_plotting_parameters["xlim"].getArray()[1].getNumber()
        number_x_ticks = 7
        xlabels = np.linspace(xmin, xmax, number_x_ticks)
        ax.set_xticks(np.linspace(-0.5, len(x)-0.5, number_x_ticks))
        ax.set_xticklabels(xlabels)
    if "ylim" in dict_of_plotting_parameters:
        ymin = dict_of_plotting_parameters["ylim"].getArray()[0].getNumber()
        ymax = dict_of_plotting_parameters["ylim"].getArray()[1].getNumber()
        number_y_ticks = 5
        ylabels = np.linspace(ymin, ymax, number_y_ticks)
        ax.set_yticks(np.linspace(-0.5, len(y)-0.5, number_y_ticks))
        ax.set_yticklabels(ylabels)

    if "xlabel" in dict_of_plotting_parameters:
        ax.set_xlabel(dict_of_plotting_parameters["xlabel"].getString(),
            fontsize=20)
    if "ylabel" in dict_of_plotting_parameters:
        ax.set_ylabel(dict_of_plotting_parameters["ylabel"].getString(),
            fontsize=20)
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(15) 
    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(15) 

    # create a second axes for the colorbar
    ax2 = fig.add_axes([0.1, -0.05, 0.8, 0.03])
    cb = matplotlib.colorbar.ColorbarBase(ax2, cmap=cmap, orientation = 'horizontal')


   

def contour_plot(dataset, dict_of_plotting_parameters):
    matplotlib.rcParams['xtick.direction'] = 'out'
    matplotlib.rcParams['ytick.direction'] = 'out'

    df = dataset.datum.asPandas()
    if "parameter_values_x_axis" in dict_of_plotting_parameters:
        grid_x = [10 * pocket for pocket in dict_of_plotting_parameters["parameter_values_x_axis"].getArray()]
    else:
        raise ValueError(""" the grid must be provided in the
            dict that parameterizes (as key ["grid", array(1,2)] for the contour_plot """)

    if "parameter_values_y_axis" in dict_of_plotting_parameters:
        grid_y = [10 * pocket for pocket in dict_of_plotting_parameters["parameter_values_y_axis"].getArray()]
    else:
        raise ValueError(""" the grid must be provided in the
            dict that parameterizes (as key ["grid", array(1,2)] for the contour_plot """)
    if "title" in dict_of_plotting_parameters:
        plt.title(dict_of_plotting_parameters["title"].getString(), fontsize=20)
                
    if "xlabel" in dict_of_plotting_parameters:
        plt.xlabel(dict_of_plotting_parameters["xlabel"].getString(),
            fontsize=15)
    if "ylabel" in dict_of_plotting_parameters:
        plt.ylabel(dict_of_plotting_parameters["ylabel"].getString(),
            fontsize=15)
    if "normalize" in dict_of_plotting_parameters:
        normalize = dict_of_plotting_parameters["width"].getBool()
    else:
        normalize = True 

    
    delta = 0.025
    X, Y = np.meshgrid(grid_x, grid_y)

    # get the particle weights in terms of neg log probability - because
    # matplotlib does n't do well with negative log values.
    particle_weights = 0 - df["prt. log wgt."].values.reshape(len(grid_x), len(grid_y))

    cut_off_value = 400
    cut_off_value_contours = 120
    particle_weights[particle_weights > cut_off_value]  = cut_off_value 

    # undoing the negation and get the min
    min_particle_weight = - np.max(particle_weights)
    max_particle_weight = - np.min(particle_weights)
    
  
    fig = plt.gcf()
    # define the colormap
    cmap = plt.cm.viridis_r
    axes = fig.get_axes()
    if not axes:
        fig, ax = plt.subplots(1,1, figsize=(6,6))
        ax.set_title("Probability Heatmap")
    else:
        ax = axes[0]
    #ax = seaborn.heatmap(particle_weights, vmin=-100, vmax=-80,
    #xticklabels=grid, yticklabels=grid)
    if "xlim" in dict_of_plotting_parameters:
        ax.set_xlim([lim.getNumber() for lim in dict_of_plotting_parameters["xlim"].getArray()])
    if "ylim" in dict_of_plotting_parameters:
        ax.set_ylim([lim.getNumber() for lim in dict_of_plotting_parameters["ylim"].getArray()])

    #CS = ax.contourf(X, Y, particle_weights, 200,cmap=cm.YlOrBr_r)
    plt.figure(2,figsize=(6,6))

    contour_levels = np.logspace(0, np.sqrt(max_particle_weight - min_particle_weight),
    100, base=1.35) - max_particle_weight 
    contour_levels = contour_levels[contour_levels <= cut_off_value]  
    contour_levels = contour_levels.tolist()
    contour_levels = [-max_particle_weight] + contour_levels + [-min_particle_weight] 
    
    CS2 = ax.contourf(grid_x, grid_y, particle_weights.T, 200, levels=contour_levels, cmap=cmap)


    contour_levels_lines = np.logspace(0, np.sqrt(max_particle_weight - min_particle_weight),
        8, base=1.35) + min_particle_weight - max_particle_weight
    contour_levels_lines = [-min_particle_weight] + contour_levels_lines
    contour_levels_lines = contour_levels_lines[contour_levels_lines <= cut_off_value]  

    CS3 = ax.contour(grid_x, grid_y, particle_weights, colors="black",
        levels=contour_levels_lines)
    for c in CS3.collections:
        c.set_linestyle("dashed")
    fmt = {}
    for level in CS3.levels:
        fmt[level] = "-" +  str(np.round(level)) 
    ax.clabel(CS3, inline=1, fontsize=8, fmt=fmt)


    # extract all colors from the .jet map
    cmaplist = [cmap(i) for i in range(cmap.N)]

    # define the bins and normalize
    bounds = np.linspace(min_particle_weight, max_particle_weight, 9) 
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)


    # create a second axes for the colorbar
    ax2 = fig.add_axes([0.1, -0.05, 0.8, 0.03])
    cb = matplotlib.colorbar.ColorbarBase(ax2, cmap=cmap, norm=norm,
        spacing='proportional', orientation = 'horizontal', boundaries=bounds, format='%1i')

    labels = [item.get_text() for item in ax2.get_xticklabels()]
    labels[0] = "< - %d" % (cut_off_value,)
    ax2.set_xticklabels(labels[::-1])

    ax2.set_xlabel("Global log joint", size=15)  

    return 0

def gradient_trajectory_plot(x, y, dict_of_plotting_parameters):

  

    if "xlabel" in dict_of_plotting_parameters:
        xlabel = dict_of_plotting_parameters["xlabel"].getString()
    else:
        raise ValueError("""xlabel must be provided in the
            dict for plotting-parameters""")

    if "ylabel" in dict_of_plotting_parameters:
        ylabel = dict_of_plotting_parameters["ylabel"].getString()
    else:
        raise ValueError("""ylabel must be provided in the
            dict for plotting-parameters""")
   
    try:
       axes
    except:
        ax = plt.gca()
        fig = plt.gcf()
    else:
        if not axes:
            fig, ax = plt.subplots(1,1, figsize=(6,6))
        else:
            ax = plt.gca()
            fig = plt.gcf()
    
    if "title" in dict_of_plotting_parameters:
        ax.set_title(dict_of_plotting_parameters["title"].getString(), fontsize=20)
    
    number_of_total_sweeps = len(x)

    transition_color = np.linspace(0,1,len(x)) 


    # Set the colormap and norm to correspond to the data for which
    # the colorbar will be used.
    cmap = plt.cm.Greens_r

    ax.plot(x, y,
        color="gray", zorder = 2, label = "" )
    ax.scatter(x[0], y[0],
        c="white", s=100,
        zorder = 0, label="First gradient step")
    ax.scatter(x, y,
        c=range(len(x)), cmap=cmap, s=100,
        zorder = 3, label="Last of gradient step")

    if "xlim" in dict_of_plotting_parameters:
        plt.xlim([lim.getNumber() for lim in dict_of_plotting_parameters["xlim"].getArray()])
    if "ylim" in dict_of_plotting_parameters:
        plt.ylim([lim.getNumber() for lim in dict_of_plotting_parameters["ylim"].getArray()])
    plt.xlabel(xlabel, fontsize=15)
    plt.ylabel(ylabel, fontsize=15)
  
    ax.legend()
    leg = ax.get_legend()
    leg.legendHandles[0].set_color("green")
    leg.legendHandles[1].set_color("white")
    
    '''
    Make a colorbar as a separate figure.
    '''



    # extract all colors from the .jet map
    cmaplist = [cmap(i) for i in range(cmap.N)]

    # define the bins and normalize
    bounds = np.linspace(0, len(x) -1 , len(x))
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)


    # create a second axes for the colorbar
    ax2 = fig.add_axes([0.95, 0.1, 0.03, 0.8])
    cb = matplotlib.colorbar.ColorbarBase(ax2, cmap=cmap, norm=norm, spacing='proportional', boundaries=bounds, format='%1i')


    ax2.set_ylabel("Green indicates the i'th gradient step, from dark to light green", size=15)  
    return 0

def plot_classification_boundary(X, Y, Z, dict_of_plotting_parameters={}):
    if "width" in dict_of_plotting_parameters:
        width = dict_of_plotting_parameters["width"].getNumber()
    else:
        width = 8
    if "height" in dict_of_plotting_parameters:
        height  = dict_of_plotting_parameters["height"].getNumber()
    else:
        height = 6
    if "fontsize_scale" in dict_of_plotting_parameters:
        fontsize_scale = dict_of_plotting_parameters["fontsize_scale"].getNumber()
    else:
        fontsize_scale = 1
    if "xlabel" in dict_of_plotting_parameters:
        plt.xlabel(dict_of_plotting_parameters["xlabel"].getString(),
            fontsize=20 * fontsize_scale)
    if "ylabel" in dict_of_plotting_parameters:
        plt.ylabel(dict_of_plotting_parameters["ylabel"].getString(),
            fontsize=20 * fontsize_scale)
    if "xlim" in dict_of_plotting_parameters:
        plt.xlim([lim.getNumber() for lim in dict_of_plotting_parameters["xlim"].getArray()])
    if "ylim" in dict_of_plotting_parameters:
        plt.ylim([lim.getNumber() for lim in dict_of_plotting_parameters["ylim"].getArray()])

    if "sigma_blur" in dict_of_plotting_parameters:
        sigma_blur = dict_of_plotting_parameters["sigma_blur"].getNumber()
    else:
        sigma_blur = 5

    if "boundaries" in dict_of_plotting_parameters:
        boundaries  = dict_of_plotting_parameters["boundaries"].getArray()
    else:
        boundaries = [0.45, 0.5, 0.55] 

    if "boundary_labels" in dict_of_plotting_parameters:
        boundary_labels = dict_of_plotting_parameters["boundary_labels"].getBool()
    else:
        boundary_labels = True 

    try:
        axes
    except:
        ax = plt.gca()
        fig = plt.gcf()
    else:
        if not axes:
            fig, ax = plt.subplots(1,1, figsize=(width,height))
        else:
            ax = plt.gca()
            fig = plt.gcf()

    Z2 = ndimage.gaussian_filter(Z, sigma=sigma_blur, order=0)
    CS = plt.contour(X, Y, Z2, boundaries,colors="k")
    CS.collections[0].set_linestyle("dashed")
    CS.collections[2].set_linestyle("dashed")
    CS.collections[0].set_linewidth(0.8)
    CS.collections[2].set_linewidth(0.8)

    if boundary_labels: 
        plt.clabel(CS, fontsize=15 * fontsize_scale, fmt = '%.2f')


def __venture_start__(ripl):
    # NOTE: these are all currently inference SPs

    ripl.bind_foreign_inference_sp("scatter_plot",
            deterministic_typed(scatter_plot,
                [ 
                t.ArrayUnboxedType(t.NumberType()), 
                t.ArrayUnboxedType(t.NumberType()),
                t.HomogeneousDictType(t.StringType(), t.AnyType())
                ],
                t.NilType(),
                min_req_args=2)
            )
    ripl.bind_foreign_inference_sp("line_plot",
            deterministic_typed(line_plot,
                [ 
                t.ArrayUnboxedType(t.NumberType()), 
                t.ArrayUnboxedType(t.NumberType()),
                t.HomogeneousDictType(t.StringType(), t.AnyType())
                ],
                t.NumberType(),
                min_req_args=2)
            )

    ripl.bind_foreign_inference_sp("density_contour_plot",
            deterministic_typed(kde_plot,
                [ 
                t.ArrayUnboxedType(t.NumberType()), 
                t.ArrayUnboxedType(t.NumberType()), 
                t.HomogeneousDictType(t.StringType(), t.AnyType())
                ],
                t.NilType(),
                min_req_args=2)
            )

    ripl.bind_foreign_inference_sp("trajectory_plot",
            deterministic_typed(trajectory_plot,
                [ 
                t.ArrayUnboxedType(t.NumberType()), 
                t.ArrayUnboxedType(t.NumberType()), 
                t.HomogeneousDictType(t.StringType(), t.AnyType())
                ],
                t.NilType(),
                min_req_args=2)
            )
    ripl.bind_foreign_inference_sp("gradient_trajectory_plot",
            deterministic_typed(gradient_trajectory_plot,
                [ 
                t.ArrayUnboxedType(t.NumberType()), 
                t.ArrayUnboxedType(t.NumberType()), 
                t.HomogeneousDictType(t.StringType(), t.AnyType())
                ],
                t.NilType(),
                min_req_args=2)
            )
    ripl.bind_foreign_inference_sp("hist_plot",
            deterministic_typed(hist_plot,
                [ 
                t.ArrayUnboxedType(t.AnyType()), 
                ],
                t.NilType(),
                min_req_args=1)
            )
    ripl.bind_foreign_inference_sp("heatmap",
            deterministic_typed(heatmap,
                [ 
                t.AnyType(t.NumberType()), 
                t.HomogeneousDictType(t.StringType(), t.AnyType())
                ],
                t.NumberType(),
                min_req_args=2)
            )
    ripl.bind_foreign_inference_sp("dist_plot",
            deterministic_typed(dist_plot,
                [ 
                t.ArrayUnboxedType(t.NumberType()), 
                t.HomogeneousDictType(t.StringType(), t.AnyType())
                ],
                t.NilType(),
                min_req_args=1)
            )
    ripl.bind_foreign_inference_sp("contour_plot",
            deterministic_typed(contour_plot,
                [ 
                t.AnyType(t.NumberType()), 
                t.HomogeneousDictType(t.StringType(), t.AnyType())
                ],
                t.NumberType(),
                min_req_args=2)
            )
    ripl.bind_foreign_inference_sp("density_line_plot",
            deterministic_typed(density_line_plot,
                [ 
                t.AnyType(t.NumberType()), 
                t.HomogeneousDictType(t.StringType(), t.AnyType())
                ],
                t.NumberType(),
                min_req_args=2)
            )
    ripl.bind_foreign_inference_sp("title",
            deterministic_typed(make_title,
                [
                t.StringType(),
                t.NumberType(),
                t.NumberType()
                ],
                t.NilType(),
                min_req_args=1)
            )
    ripl.bind_foreign_inference_sp("legend",
            deterministic_typed(legend,
                [ ],
                t.NilType(),
                min_req_args=0)
            )
    ripl.bind_foreign_inference_sp("new_figure",
            deterministic_typed(new_figure,
                [ ],
                t.NilType(),
                min_req_args=0)
            )
    ripl.bind_foreign_inference_sp("simple_contour_plot",
            deterministic_typed(simple_contour_plot,
                [ 
                t.ArrayUnboxedType(t.NumberType()), 
                t.ArrayUnboxedType(t.NumberType()), 
                t.ArrayUnboxedType(t.ArrayUnboxedType(t.NumberType())),
                t.HomogeneousDictType(t.StringType(), t.AnyType())
                ],
                t.NilType(),
                min_req_args=3)
            )
    ripl.bind_foreign_inference_sp("plot_classification_boundary",
            deterministic_typed(plot_classification_boundary,
                [ 
                t.ArrayUnboxedType(t.NumberType()), 
                t.ArrayUnboxedType(t.NumberType()), 
                t.ArrayUnboxedType(t.ArrayUnboxedType(t.NumberType())),
                t.HomogeneousDictType(t.StringType(), t.AnyType())
                ],
                t.NilType(),
                min_req_args=3)
            )
