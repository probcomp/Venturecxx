from IPython.html.widgets import interact
import numpy as np
import pandas as pd
from bokeh import load_notebook
import bokeh.plotting as bk
from bokeh.models import (ColumnDataSource, DataRange1d, Plot, LinearAxis,
                          Grid, GlyphRenderer, Circle, HoverTool, BoxSelectTool)
from bokeh.models.widgets import (VBox, DataTable, TableColumn, StringFormatter,
                                  NumberFormatter, StringEditor, IntEditor,
                                  NumberEditor, SelectEditor)



def wrap_string_in_list(item):
    if isinstance(item, basestring):  # Test six.string_types for py3 compat
        return [item]
    else:
        return item

def predict_to_df(mripl, parameter_list):
    """ Returns a dataframe with one column per parameter,
    one row per Ripl.  Should work with either MRipl or Ripl"""
    from collections import OrderedDict 
    series_dict = OrderedDict()
    param_list = wrap_string_in_list(parameter_list)
    
    for param in param_list:
        series_dict[param] = mripl.predict(param)
                
    try:  # Return dataframe, with special case to handle non-mripl
        return pd.DataFrame(series_dict)
    except ValueError, e: 
        if "must pass an index" in e.message:
            return pd.DataFrame(series_dict, index=[0])
        else:
            raise

def setup_datasource(venture_mripl, parameters):
    """ Create datasource for Bokeh plot. 
    Accepts either venture mripl or ripl.
    """
    # Create datasource class to record parameters 
    param_dsource = ColumnDataSource()
    
    pred_df = predict_to_df(venture_mripl, parameters)
    
    # Index for plotting purposes
    pred_index_list = [0]
    param_dsource.add(data=pred_index_list, name='pred_index')
    zero_list = [0]  # dynamically expanding list of zeros...  hack for 1d scatter
    param_dsource.add(data=zero_list, name='zero_list')

    # Flatten prediction dataframe into column datasource
    # One column for each parameter for each Ripl (one column = one lines)
    for idx, prediction_set in pred_df.iterrows():
        for parameter, value in prediction_set.iteritems():
            value_list = [value]
            param_dsource.add(data=value_list, name=(parameter + '_' + str(idx)))

    return param_dsource

def append_update_to_datasource(venture_mripl, datasource, parameters):
    """Predicts current parameters and appends to datasource in-place
    Returns DataFrame containing latest predictions"""
    
    pred_df = predict_to_df(venture_mripl, parameters)
    
    last_pred_index = datasource.data['pred_index'][-1]
    datasource.data['pred_index'].append(last_pred_index + 1)
    last_zero_item = datasource.data['zero_list'][-1]
    datasource.data['zero_list'].append(last_zero_item + 0.001)
    
    for idx, prediction_set in pred_df.iterrows():
        for parameter, value in prediction_set.iteritems():
            datasource.data[parameter + '_' + str(idx)].append(value)
    
    return pred_df  # Latest predicted values

def single_trace_figure(parameter, param_line_set, xrange_ref=None, yrange_ref=None):
    return
    
def trace_grid(param_dsource, parameters, scatter=False, trace_alpha=0.6, scatter_alpha=0.2):
    """Return bokeh grid of vertical traces for given ripl"""
    from collections import OrderedDict
    # Grab lists of parameters to plot
    param_trace_set = OrderedDict()
    xrange_set = OrderedDict()
    tracefig_set = OrderedDict()
    distfig_set = OrderedDict()
    #Shared y-axis given to each trace plot
    yrange_shared = DataRange1d(sources=[param_dsource.columns()])
    
    for param in parameters:
        #Full set of traces for this parameter (= number of MRipls)
        param_trace_set[param] = sorted([key for key in param_dsource.data.keys() 
                                             if key.startswith(param)])
    
        # Shared datarange to link x-axes between trace and distribution plots
        xrange_set[param] = DataRange1d(sources=[param_dsource.columns()])

        # Create vertical trace plots
        
        tracefig_set[param] = bk.figure(plot_width=150, plot_height=300,
                                        x_range=xrange_set[param], y_range=yrange_shared,
                                        title=param,
                                        tools=['pan','wheel_zoom', 'box_zoom',
                                        'previewsave','resize','reset','box_select'])
        #Draw lines for each trace:
        for this_trace_label in param_trace_set[param]: 
            tracefig_set[param].line(this_trace_label,'pred_index', source=param_dsource,
                                     color="blue", alpha=trace_alpha)

        if scatter:
            # Create scatter/distribution plots
            distfig_set[param] = bk.figure(plot_width=150, plot_height=150,
                                            x_range=xrange_set[param], y_range=(-0.19, 1.19),
                                            tools=['pan','wheel_zoom', 'box_zoom',
                                                   'previewsave','resize','reset','box_select'])
            # Draw points for each trace
            for this_trace_label in param_trace_set[param]: 
                distfig_set[param].scatter(this_trace_label,'zero_list', source=param_dsource,
                                               color="blue", marker='o', alpha=scatter_alpha)


    #Gradient from white --30--> grey --10--> blue
    colors_40 =   ["#FFFFFF","#FBFBFB","#F7F7F7","#F4F4F4","#F0F0F0","#EDEDED","#E9E9E9",
                   "#E5E5E5","#E2E2E2","#DEDEDE","#DBDBDB","#D7D7D7","#D4D4D4","#D0D0D0",
                   "#CCCCCC","#C9C9C9","#C5C5C5","#C2C2C2","#BEBEBE","#BABABA","#B7B7B7",
                   "#B3B3B3","#B0B0B0","#ACACAC","#A9A9A9","#A5A5A5","#A1A1A1","#9E9E9E",
                   "#9A9A9A","#979797","#939393","#909090","#82829A","#7575A4","#6868AE",
                   "#5B5BB8","#4E4EC2","#4141CC","#3434D6","#2727E0","#1A1AEA","#0D0DF4","#0000FF"]
    r_colors_40 = colors_40[::-1]

    if scatter:
        gd = bk.GridPlot(children=[[tracefig_set['w0'], tracefig_set['w1'], tracefig_set['noise']],
                                   [ distfig_set['w0'],  distfig_set['w1'],  distfig_set['noise']]])
    else:
        gd = bk.GridPlot(children=[[tracefig_set['w0'], tracefig_set['w1'], tracefig_set['noise']]])

    return gd

def display_plots(grid):
    """Load JS code into notebook and display"""
    load_notebook(force=True)
    bk.publish_display_data({'text/html':bk.notebook_div(grid)})




def interactive_trace(ven_ripl,
                      inference_program=["(mh default one 1)",
                                         "(mh default one 10)",
                                         "(pgibbs default one 10 3)"],
                      loops=20):
    param_dsource = setup_dsource(ven_ripl)
    gd = trace_grid(param_dsource)
    display_plots(gd)


def infer_and_update(inference_program=["(mh default one 1)",
                                        "(mh default one 10)",
                                        "(pgibbs default one 10 3)"],
                                        loops=20):
    global line_set
    global inter_list
    global slope_list
    global noise_list
    v.start_continuous_inference(program=inference_program)
    for _ in range(loops):
        
        # Update parameters
        x_val_list.extend([x_val_list[-1] + 1])
        inter_list.extend([v.predict('w0')])
        slope_list.extend([v.predict('w1')])
        noise_list.extend([v.predict('noise')])
        param_dsource.push_notebook()
        
        # Update lines of fit
        line_y_0 = grab_predicted_line(v, line_x)
        #Loop through updating new data and shifting back the rest
        for idx, label, line_data in line_set[::-1]: #Reverse order to avoid cascading first update
            if idx==0:
                this_line_data = line_y_0
                line_set[idx] = (idx,label,this_line_data)
            else:
                #Shift line data one positon back
                _, _, this_line_data = line_set[idx - 1]
                line_set[idx] = (idx,label,this_line_data)
            #Update datasource
            fit_dsource.data[label] = this_line_data
        
        fit_dsource.push_notebook()  # Update plot directy through notebook: Very fast
        # session.store_objects(fit_dsource)  # Update notebook via server, takes ~80ms
        #time.sleep(0.01)
    v.stop_continuous_inference()