import time
import numpy as np
import scipy.io as scio
import IPython.core.display as di

from sympy.parsing.sympy_parser import parse_expr
from sympy import  *

import venture.lite.types as vt
from venture.lite.sp_help import deterministic_typed


max_number_same = 6
LIN, SE, WN, PER, C = symbols(("LIN","SE","WN","PER","C"))
# number of parameters for lin,per,se,wn,cp,c,lin+c,rq
label_parameter_count ={0:'1',1:'3',2:'2',3:'1',4:'2',5:'1',6:'2',7:'3'}

def load_csv(path):
    return np.loadtxt(path)

def load_table(path):
    return np.loadtxt(path).tolist()

def get_data_xs(path, normalize=True):
    contents = scio.loadmat(path)
    data_xs = contents["X"]
    data_xs = np.reshape(data_xs ,data_xs.shape[0]).tolist()
    if normalize:
        data_xs = data_xs - np.min(data_xs)
    return data_xs

def get_data_ys(path, normalize=True):
    contents = scio.loadmat(path)
    data_ys = contents["y"]
    data_ys  = np.reshape(data_ys ,data_ys.shape[0])
    if normalize:
        data_ys  = data_ys  - np.mean(data_ys )
    return data_ys.tolist()

def get_classification_data(path, label_index, keep_labels=None):
    data = np.loadtxt(path, delimiter=",")
    data =np.vstack({tuple(row) for row in data}) #removing duplicate rows
    # Only keep the rows whose label is in keep_labels. 
    if keep_labels is not None:
        data = data[np.in1d(data[:,label_index], keep_labels)]
        data =np.vstack({tuple(row) for row in data}) # again - now removing
        # duplicate rows wrt only the kept colums
    data = np.delete(data, label_index, axis=1)
    return data

def get_classification_labels(path, label_index, keep_labels=None):
    data = np.loadtxt(path, delimiter=",")
    data =np.vstack({tuple(row) for row in data}) #removing duplicate rows
    # Only keep the rows whose label is in keep_labels. 
    if keep_labels is not None:
        data = data[np.in1d(data[:,label_index], keep_labels)]
        data =np.vstack({tuple(row) for row in data}) # again - now removing
        # duplicate rows wrt only the kept colums
    return data[:,label_index]

def simplify_string(eq_str):
    eq_str = eq_str.replace("x", "*")
    expr = parse_expr(eq_str).expand()
    for i in range(max_number_same, 0, -1):
        expr = expr.subs({
            SE**i:SE,
            WN*SE:WN,
            WN**i:WN,
            C**i:C,
            WN*PER:WN,
            WN*LIN*LIN:LIN*WN,
            C*WN:WN,
            C+WN:WN,
            LIN*WN+WN:LIN*WN,  #what justification do I have for this???
            C*C:C,
            C+C:C,
        })
    return str(expr)

def render_ast_as_source_string_without_parameters(ast, summarize=False):
    if ast[0].getString() == "LIN":
      return "LIN"
    elif ast[0].getString() == "SE":
      return "SE"
    elif ast[0].getString() == "PER":
      return "PER"
    elif ast[0].getString() == "C":
      return "C"
    elif ast[0].getString()  == "WN":
      return "WN"
    elif ast[0].getString() == "+":
      return r"(" \
          + render_ast_as_source_string_without_parameters(ast[1]) + " + " \
          + render_ast_as_source_string_without_parameters(ast[2]) + ")"
    elif ast[0].getString() == "*":
      return r"(" \
          + render_ast_as_source_string_without_parameters(ast[1]) + " * " \
          + render_ast_as_source_string_without_parameters(ast[2]) + ")"
    else:
      raise ValueError("incorrectly formatted ast: (%r)" % (ast,)) 



def render_ast_as_source_string(ast, summarize = False):
    if ast[0].getString() == "LIN":
      return r"(LIN %f)" % (ast[1][0],) 
    elif ast[0].getString() == "SE":
      return r"(SE %f)" % (ast[1][0],) 
    elif ast[0].getString() == "PER":
      return r"(PER %f %f)" % (ast[1][0], ast[1][1],) 
    elif ast[0].getString() == "C":
      return r"(C  %f)" % (ast[1][0],) 
    elif ast[0].getString()  == "WN":
      return r"(WN %f)" % (ast[1][0],) 
    elif ast[0].getString() == "+":
      return r"(" \
        + render_ast_as_source_string(ast[1]) + " + " \
        + render_ast_as_source_string(ast[2]) + ")"
    elif ast[0].getString() == "*":
      return r"(" \
        + render_ast_as_source_string(ast[1]) + " * " \
        + render_ast_as_source_string(ast[2]) + ")"
    else:
      raise ValueError("incorrectly formatted ast: (%r)" % (ast,)) 

def toggle_cell():
    # This line will hide code by default when the notebook is exported as HTML
    di.display_html('''<script>jQuery(function() {if (jQuery("body.notebook_app").length == 0) { jQuery(".input_area").toggle(); 
        jQuery(".prompt").toggle();}});</script>''', raw=True)

    # This line will add a button to toggle visibility of code blocks, for use with the HTML export version
    di.display_html('''<button onclick="jQuery('.input_area').toggle();
        jQuery('.prompt').toggle();">show/hide cell</button>''', raw=True)

def __venture_start__(ripl):
    ripl.bind_foreign_sp("render_ast_as_source_string",
        deterministic_typed(render_ast_as_source_string,
            [vt.ExpressionType()], 
            vt.StringType(),
            min_req_args=1)
    )
    ripl.bind_foreign_sp("render_ast_as_source_string_without_parameters",
        deterministic_typed(render_ast_as_source_string_without_parameters,
            [vt.ExpressionType()], 
            vt.StringType(),
            min_req_args=1)
    )
    ripl.bind_foreign_sp("simplify_string",
        deterministic_typed(simplify_string,
            [vt.StringType()], 
            vt.StringType(),
            min_req_args=1)
    )
    ripl.bind_foreign_inference_sp("get_data_xs",
        deterministic_typed(get_data_xs,
            [vt.StringType(),
             vt.BoolType() 
            ], 
            vt.ArrayUnboxedType(vt.NumberType()), 
            min_req_args=1)
    )
    ripl.bind_foreign_inference_sp("get_data_ys",
        deterministic_typed(get_data_ys,
            [vt.StringType(),
             vt.BoolType() 
            ], 
            vt.ArrayUnboxedType(vt.NumberType()), 
            min_req_args=1)
    )
    ripl.bind_foreign_inference_sp("get_classification_data",
        deterministic_typed(get_classification_data,
            [
             vt.StringType(),
             vt.IntegerType(),
             vt.ArrayUnboxedType(vt.NumberType())
            ], 
            vt.ArrayUnboxedType(vt.ArrayUnboxedType(vt.NumberType())),
            min_req_args=2)
    )
    ripl.bind_foreign_inference_sp("get_classification_labels",
        deterministic_typed(get_classification_labels,
            [
             vt.StringType(),
             vt.IntegerType(),
             vt.ArrayUnboxedType(vt.NumberType())
            ], 
            vt.ArrayUnboxedType(vt.NumberType()), 
            min_req_args=2)
    )
    ripl.bind_foreign_inference_sp("time",
        deterministic_typed(lambda: time.time(),
            [ ], 
            vt.NumberType() 
            )
    )
    ripl.bind_foreign_inference_sp("load_csv",
        deterministic_typed(load_csv,
            [
             vt.StringType()
            ], 
            vt.ArrayUnboxedType(vt.NumberType()), 
            min_req_args=1)
    )
    ripl.bind_foreign_inference_sp("load_table",
        deterministic_typed(load_csv,
            [
             vt.StringType()
            ], 
            vt.ArrayUnboxedType(vt.ArrayUnboxedType(vt.NumberType())), 
            min_req_args=1)
    )
    ripl.bind_foreign_inference_sp("mean",
        deterministic_typed(lambda x: np.mean(x),
            [vt.ArrayUnboxedType(vt.NumberType()) ], 
            vt.NumberType() 
            )
    )
    ripl.bind_foreign_inference_sp("toggle_cell",
        deterministic_typed(lambda : toggle_cell(),
            [ ], 
            vt.NilType() 
            )
    )
