
disable_REST_server_server = True





def read(s):
    "Read a Scheme expression from a string."
    return read_from(tokenize(s))

parse = read

def tokenize(s):
    "Convert a string into a list of tokens."
    return s.replace('(',' ( ').replace(')',' ) ').split()

def read_from(tokens):
    "Read an expression from a sequence of tokens."
    if len(tokens) == 0:
        raise SyntaxError('unexpected EOF while reading')
    token = tokens.pop(0)
    if '(' == token:
        L = []
        while tokens[0] != ')':
            L.append(read_from(tokens))
        tokens.pop(0) # pop off ')'
        return L
    elif ')' == token:
        raise SyntaxError('unexpected )')
    else:
        return atom(token)

def atom(token):
    "Numbers become numbers; every other token is a symbol."
    try: return int(token)
    except ValueError:
        try: return float(token)
        except ValueError:
            return Symbol(token)
            
Symbol = str
          
          
        


          
import sys
sys.path.append("C:\\Python2.7.3\\DLLs")

print sys.path

import socket
socket._socket

print "Hello"

import venture.lisp_parser
import venture.sugars_processor

import venture_engine

# distribution_dictionary = {}
# attempts = 0.0
# while True:
  # venture_engine.clear()
  # venture_engine.assume("draw-type", parse("(CRP/make 1.0)"))
  # venture_engine.assume("obs", parse("(mem (lambda (type) (symmetric-dirichlet-multinomial/make 0.01 3)))"))
  # (_, last_value) = venture_engine.predict(parse("(= ((obs (draw-type))) ((obs (draw-type))))"))
  # print last_value
  # distribution_dictionary[str(last_value)] = distribution_dictionary.get(str(last_value), 0) + 1
  # attempts = attempts + 1.0
  # distribution_as_100 = [(str(x) + " = " + str(distribution_dictionary[x] / attempts)) for x in distribution_dictionary]
  # print str(attempts) + ': ' + str(distribution_as_100)
  # print "*"
  # if attempts == 10000:
    # sys.exit()

# venture_engine.assume("a", parse("(uniform-continuous r[0.0] r[1.0])"))
# venture_engine.observe(parse("(normal a r[0.01])"), "r[0.7]")

# while True:
  # print venture_engine.report_value(1)
  # venture_engine.infer(1)

# venture_engine.assume("a", parse("(mem (lambda (x) (normal r[0.0] r[5.0])))"))
# print venture_engine.predict(parse("(a 3)"))
# print venture_engine.predict(parse("(a 3)"))
# venture_engine.infer(1)
# print venture_engine.report_value(2)
# print venture_engine.report_value(3)

ripl = venture_engine
import venture.utils
venture.utils.load_to_RIPL(
  ripl,
  open('C:/Temp/serialized_model.lisp').read())
# venture.utils.load_to_RIPL(
  # ripl,
  # """
  # [ASSUME a (flip)]
  # [ASSUME b (mem (lambda () (+ a c)))]
  # [ASSUME c a]
  # [PREDICT (b)]
  # """
# )
# venture.utils.load_to_RIPL(
  # ripl,
  # """
  # [ASSUME a (flip)]
  # [ASSUME b (mem (lambda (x) (if a (flip) (flip))))]
  # [PREDICT (b a)]
  # """
# )
# for i in range(1000):
  # print "Starting to calculate the logscore"
  # ripl.logscore()
  # print "Stopping to calculate the logscore"
  # print "Starting to perform one inference iteration"
  # ripl.infer(1)
  # print "Stopping to perform one inference iteration"
# ripl.infer(1000)

# sys.path.append("C:/pcp/20November2012/VentureAlphaOld/SourceCode/Venture/src")
# ripl.assume("test1", "(load-python-function str[testing_python_functions] str[test1] false)")
# ripl.assume("test2", "(load-python-function str[testing_python_functions] str[test2] true)")
# print ripl.predict("(test1)")
# print ripl.predict("(test2 151)")

# Just for compatibility
class lisp_parser_Class:
  def parse(__self__, what_to_parse):
    return parse(what_to_parse)

lisp_parser = lisp_parser_Class()
    
MyRIPL = venture_engine

"""
MyRIPL.assume("clusters", lisp_parser.parse("(CRP/make (gamma 1.0 1.0))")) # (gamma 1.0 1.0)
MyRIPL.assume("get-cluster-id", lisp_parser.parse("(mem (lambda (object-id) (clusters)))"))
MyRIPL.assume("cluster-base-element", lisp_parser.parse("(mem (lambda (cluster-id x y) (beta-binomial/make (list (gamma 1.0) (gamma 1.0)))))"))
MyRIPL.assume("offset", lisp_parser.parse("(mem (lambda (object-id dimension) (- (uniform-discrete 0 6) 3)))"))
# MyRIPL.assume("offset", lisp_parser.parse("(lambda (object-id dimension) 0)"))

import pickle
data = pickle.load(open("C:/HWD/digits2_1.txt", "r"))
number_of_digits = 10
width = 10
height = 10

objects_clusters_ids = {}

for object in range(number_of_digits):
  (objects_clusters_ids[object], _) = MyRIPL.assume("cluster-for-object-" + str(object), lisp_parser.parse("(get-cluster-id " + str(object) + ")"))
  for x in range(width):
    for y in range(height):
      pixel = data[object * (width + 1) + x + y * ((width + 1) * number_of_digits)][0]
      if pixel == 255:
        observing_value = 0
      elif pixel == 0:
        observing_value = 1
      else:
        print (1.0 / 0.0)
      for_observe = "((cluster-base-element cluster-for-object-" + str(object) + " (+ " + str(x) + " (offset " + str(object) + " 1)) (+ " + str(y) + " (offset " + str(object) + " 2))))"
      print for_observe + " = " + str(observing_value)
      MyRIPL.observe(lisp_parser.parse(for_observe), observing_value)
      # print MyRIPL.predict(lisp_parser.parse(for_observe))
      
# exit()
  
while True:
  MyRIPL.infer(1000)
  clusters = {}
  for object in range(number_of_digits):
    cluster_id = MyRIPL.report_value(objects_clusters_ids[object])
    if not(cluster_id in clusters):
      clusters[cluster_id] = []
    clusters[cluster_id] += [object]
  for cluster in clusters:
    print "Cluster " + str(cluster) + ": " + str(clusters[cluster])
  print MyRIPL.logscore()
  print "***"
  
if 1 == 2:
  MyRIPL.assume("noise", lisp_parser.parse("(* (gamma 1.0 1.0) 50.0)")) # 
  MyRIPL.assume("clusters", lisp_parser.parse("(CRP/make (gamma 1.0 1.0))")) # (gamma 1.0 1.0)
  MyRIPL.assume("get-cluster-id", lisp_parser.parse("(mem (lambda (object-id) (clusters)))"))
  MyRIPL.assume("cluster-elements", lisp_parser.parse("(mem (lambda (cluster-id) (new-set)))"))
  MyRIPL.assume("cluster-base-element", lisp_parser.parse("(mem (lambda (cluster-id) (sample-from-set (cluster-elements cluster-id))))"))

  # objects = [10000, 10001, 10002, 10003, 20000, 20001, 20002, 20003]
  objects = []
  for digit in range(1, 2 + 1):
    for instances in range(3):
      objects += [(10000 * digit) + instances]
  # objects = [10000, 10001]
  # objects = [10000]

  objects_clusters_ids = {}

  for object in objects:
    (objects_clusters_ids[object], _) = MyRIPL.assume("cluster-for-object-" + str(object), lisp_parser.parse("(get-cluster-id " + str(object) + ")"))
    if (object % 10000 < 1):
      MyRIPL.observe(lisp_parser.parse("(get-cluster-id " + str(object) + ")"), "a[" + str(object / 10000) + "]")
    MyRIPL.predict(lisp_parser.parse("(add-to-set (cluster-elements (get-cluster-id " + str(object) + ")) " + str(object) + ")"))
    # 0.05 -- appr. 5 degrees
    MyRIPL.observe(lisp_parser.parse("(compare-images " + str(object) + " (cluster-base-element (get-cluster-id " + str(object) + ")) (normal 0.0 2.0) (normal 0.0 2.0) (normal 0.0 0.05) noise)"), True)

  while True:
    MyRIPL.infer(1000)
    clusters = {}
    for object in objects:
      cluster_id = MyRIPL.report_value(objects_clusters_ids[object])
      if not(cluster_id in clusters):
        clusters[cluster_id] = []
      clusters[cluster_id] += [object]
    for cluster in clusters:
      print "Cluster " + str(cluster) + ": " + str(clusters[cluster])
    print "***"
"""
    
# MyRIPL.clear()
# MyRIPL.assume("fast-calc-joint-prob", 1)
# MyRIPL.predict(lisp_parser.parse("((CRP/make (gamma 1.0 1.0)))"))
# MyRIPL.infer(1000)

# MyRIPL.clear()
# MyRIPL.assume("fib", lisp_parser.parse("(mem (lambda (n) (if (int< n 2) n (int+ (if (flip) 1 0) (fib (int- n 1)) (fib (int- n 2))))))"))
# print "Value" + str(MyRIPL.predict(lisp_parser.parse("(fib 5)")))
# print MyRIPL.logscore()

# MyRIPL.assume("bb", lisp_parser.parse("(dirichlet-multinomial/make (list 0.5 0.5 0.5))"))
# (last_directive, _) = MyRIPL.predict(lisp_parser.parse("(= (bb) (bb))"))
# MyRIPL.infer(50)
# MyRIPL.draw_graph_to_file()

# MyRIPL.clear()
# MyRIPL.assume("draw-type", lisp_parser.parse("(CRP/make 1.0)"))
# MyRIPL.assume("obs", lisp_parser.parse("(mem (lambda (type) (symmetric-dirichlet-multinomial/make 0.01 3)))"))
# (last_directive, _) = MyRIPL.predict(lisp_parser.parse("(= ((obs (draw-type))) ((obs (draw-type))))"))
# while True:
  # print MyRIPL.report_value(3)
  # MyRIPL.infer(1)

# MyRIPL.assume("bb", lisp_parser.parse("(dirichlet-multinomial/make (list 0.5 0.5 0.5))"))
# (last_directive, _) = MyRIPL.predict(lisp_parser.parse("(= (bb) (bb))"))
# while True:
  # print MyRIPL.report_value(2)
  # MyRIPL.infer(100)

# MyRIPL.clear()
# MyRIPL.assume("uncertainty-factor", lisp_parser.parse("(flip)"))
# MyRIPL.assume("my-function", lisp_parser.parse("(if uncertainty-factor flip (lambda (x) x))"))
# MyRIPL.assume("my-function-mem", lisp_parser.parse("(mem my-function)"))
# (last_directive, _) = MyRIPL.predict(lisp_parser.parse("(if (= (my-function-mem 0.3) 0.3) 0.3 (my-function-mem 0.3))"))

# MyRIPL.assume("draw-type", lisp_parser.parse("(CRP/make 0.5)"))
# MyRIPL.assume("class1", lisp_parser.parse("(draw-type)"))
# MyRIPL.assume("class2", lisp_parser.parse("(draw-type)"))
# MyRIPL.assume("class3", lisp_parser.parse("(draw-type)"))
# MyRIPL.observe(lisp_parser.parse("(noisy-negate (= class1 class2) 0.000001)"), "true")
# (last_directive, _) = MyRIPL.predict(lisp_parser.parse("(= class1 class3)"))

# MyRIPL.assume("proc1", lisp_parser.parse("(flip)"))
# MyRIPL.assume("proc2", lisp_parser.parse("(flip)"))
# MyRIPL.assume("proc", lisp_parser.parse("(mem (lambda (x) (flip 0.5)))"))
# (last_directive, value) = MyRIPL.predict(lisp_parser.parse("(and (proc 1) (proc 1) (proc 1))"))
# (last_directive, _) = MyRIPL.predict(lisp_parser.parse("(and (proc 1) (proc 2) (proc 1) (proc 2))"))
# print value
# MyRIPL.infer(0)
# (last_directive, _) = MyRIPL.predict(lisp_parser.parse("(and proc1 proc2 proc1 proc2)"))
# sys.exit()

# MyRIPL.assume("proc", lisp_parser.parse("(mem (lambda (x) (flip 0.8)))"))
# (last_directive, _) = MyRIPL.predict(lisp_parser.parse("(if (proc (uniform-discrete 1 3)) (if (proc (uniform-discrete 1 3)) (proc (uniform-discrete 1 3)) false) false)"))


# MyRIPL.assume("proc", lisp_parser.parse("(mem (lambda () (flip 0.5)))"))
# (last_directive, _) = MyRIPL.predict(lisp_parser.parse("(if (proc) (proc) false)"))



# MyRIPL.assume("proc", lisp_parser.parse("(mem (lambda (x) (flip 0.5)))"))
# (last_directive, _) = MyRIPL.predict(lisp_parser.parse("(if (proc 1) (if (proc 1) (proc 1) false) false)"))

# import random

# MyRIPL.assume("power-law", lisp_parser.parse("(lambda (prob x) (if (flip prob) x (power-law prob (+ x 1))))"))
# MyRIPL.assume("a", lisp_parser.parse("(power-law 0.3 1)"))
# MyRIPL.predict(lisp_parser.parse("a"))
# (last_directive, _) = MyRIPL.predict(lisp_parser.parse("(< a 5)"))
    
# distribution_dictionary = {}
# attempts = 0.0
# while True:
  # print venture_engine.report_value(1)
  # last_value = venture_engine.report_value(last_directive)
  # distribution_dictionary[str(last_value)] = distribution_dictionary.get(str(last_value), 0) + 1
  # attempts = attempts + 1.0
  # distribution_as_100 = [(str(x) + " = " + str(distribution_dictionary[x] / attempts)) for x in distribution_dictionary]
  # print distribution_as_100
  # print "*"
  # venture_engine.infer(100)
  # if attempts == 200000:
    # sys.exit()

# sys.exit()



    
# venture_engine.assume("a", parse("(mem (lambda (x) (+ x x)))"))
# venture_engine.predict(parse("(a (uniform-continuous r[0.0] r[1.0]))"))
# while True:
  # print venture_engine.report_value(2)
  # venture_engine.infer(1)

# venture_engine.assume("order", parse("(uniform-discrete c[0] c[4])"))
# venture_engine.assume("noise", parse("(uniform-continuous r[0.1] r[1.0])"))
# venture_engine.assume("c0", parse("(if (>= order c[0]) (normal r[0.0] r[10.0]) r[0.0])"))
# venture_engine.assume("c1", parse("(if (>= order c[1]) (normal r[0.0] r[1]) r[0.0])"))
# venture_engine.assume("c2", parse("(if (>= order c[2]) (normal r[0.0] r[0.1]) r[0.0])"))
# venture_engine.assume("c3", parse("(if (>= order c[3]) (normal r[0.0] r[0.01]) r[0.0])"))
# venture_engine.assume("c4", parse("(if (>= order c[4]) (normal r[0.0] r[0.001]) r[0.0])"))
# venture_engine.assume("clean-func", parse("(lambda (x) (+ c0 (* c1 (power x r[1.0])) (* c2 (power x r[2.0])) (* c3 (power x r[3.0])) (* c4 (power x r[4.0]))))"))
# venture_engine.predict(parse("(list order c0 c1 c2 c3 c4 noise)"))
# venture_engine.infer(10000)
# for i in range(20):
  # venture_engine.observe(parse("(normal (clean-func (normal r[" + str(i - 10) + "] noise)) noise)"), "r[1.0]")
# while True:
  # print venture_engine.report_value(9)
  # venture_engine.infer(1000)
  
# venture_engine.assume("order", parse("(uniform-discrete 0 4)"))
# venture_engine.assume("noise", parse("(uniform-continuous 0.1 1.0)"))
# venture_engine.assume("c0", parse("(if (>= order c[0]) (normal r[0.0] r[10.0]) r[0.0])"))
# venture_engine.assume("c1", parse("(if (>= order c[1]) (normal r[0.0] r[1]) r[0.0])"))
# venture_engine.assume("c2", parse("(if (>= order c[2]) (normal r[0.0] r[0.1]) r[0.0])"))
# venture_engine.assume("c3", parse("(if (>= order c[3]) (normal r[0.0] r[0.01]) r[0.0])"))
# venture_engine.assume("c4", parse("(if (>= order c[4]) (normal r[0.0] r[0.001]) r[0.0])"))
# venture_engine.assume("clean-func", parse("(lambda (x) (+ c0 (* c1 (power x r[1.0])) (* c2 (power x r[2.0])) (* c3 (power x r[3.0])) (* c4 (power x r[4.0]))))"))
# venture_engine.predict(parse("(list order c0 c1 c2 c3 c4 noise)"))
# for i in range(20):
  # venture_engine.observe(parse("(normal (clean-func (normal " + str(i - 10) + ".0 noise)) noise)"), "1.0")
  # print "(normal (clean-func (normal " + str(i - 10) + ".0 noise)) noise)"
# while True:
  # print venture_engine.report_value(9)
  # venture_engine.infer(1000)
  
# venture_engine.infer(1000);
# venture.forget(8)
# venture.forget(9)

# venture_engine.assume("power-law", parse("(lambda (prob x) (if (flip prob) x (power-law prob (+ x 1))))"))
# venture_engine.assume("a", parse("(power-law 0.3 1)"))
# (last_directive, _) = venture_engine.predict(parse("(< a 5)"))
# venture_engine.infer(1000)

# venture_engine.assume("draw-type", parse("(CRP/make 0.5)"))
# venture_engine.assume("class1", parse("(draw-type)"))
# venture_engine.assume("class2", parse("(draw-type)"))
# venture_engine.assume("class3", parse("(draw-type)"))
# venture_engine.observe(parse("(noisy-negate (= class1 class2) 0.000001)"), "true")
# venture_engine.predict(parse("(= class1 class3)"))
# venture_engine.infer(1000)

# for i in range(100):
  # venture_engine.infer(1)
  # print "   " + str(venture_engine.report_value(2)) + " " + str(venture_engine.report_value(3)) #+ " " + str(venture_engine.report_value(4))

# print "Ready"
# sys.exit()

import flask
from flask import request
from flask import make_response

# Why it disables the output for the flask?
if disable_REST_server_server is True:
  import logging
  flask_log = logging.getLogger("werkzeug")
  flask_log.setLevel(logging.DEBUG) # For some reason WARNING and ERROR! still prints requests to the console.

try: # See for details: http://stackoverflow.com/questions/791561/python-2-5-json-module
    import json
except ImportError:
    import simplejson as json 

# Not necessary?: import util

def get_response(string):
    resp = make_response(string)
    #resp.status_code = 201
    #resp.data = json.dumps(directives)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
    
global app
app = flask.Flask(__name__)

@app.route('/assume', methods=['POST'])
def assume():
  name_str = json.loads(request.form["name_str"])
  expr_lst = json.loads(request.form["expr_lst"])
  # print expr_lst
  (directive_id, value) = venture_engine.assume(name_str, expr_lst)
  return get_response(json.dumps({"d_id": directive_id,
                                  "val": value}))
             
@app.route('/predict', methods=['POST'])
def predict():
  expr_lst = json.loads(request.form["expr_lst"])
  (directive_id, value) = venture_engine.predict(expr_lst)
  return get_response(json.dumps({"d_id": directive_id, "val": value}))
        
@app.route('/observe', methods=['POST'])
def observe():
  expr_lst = json.loads(request.form["expr_lst"])
  literal_val = json.loads(request.form["literal_val"])
  directive_id = venture_engine.observe(expr_lst, literal_val)
  return get_response(json.dumps({"d_id": directive_id}))

@app.route('/start_cont_infer', methods=['POST'])
def start_cont_infer():
  venture_engine.start_continuous_inference();
  return get_response(json.dumps({"started": True}))

@app.route('/stop_cont_infer', methods=['POST'])
def stop_cont_infer():
  venture_engine.stop_continuous_inference();
  return get_response(json.dumps({"stopped": True}))
  
@app.route('/cont_infer_status', methods=['GET'])
def cont_infer_status(): # print "Necessary to add additional information!"
  if venture_engine.continuous_inference_status():
    return get_response(json.dumps({"status": "on"}))
  else:
    return get_response(json.dumps({"status": "off"}))
  
@app.route('/', methods=['POST']) # Check for DELETE!
def clear():
  venture_engine.clear();
  return get_response(json.dumps({"cleared": True}))
  
@app.route('/<int:directive_id>', methods=['GET'])
def report_value(directive_id):
  current_value = venture_engine.report_value(directive_id);
  return get_response(json.dumps({"val": current_value}))
  
@app.route('/logscore', methods=['GET'])
def logscore():
  current_value = venture_engine.logscore();
  return get_response(json.dumps({"logscore": current_value}))
  
@app.route('/', methods=['GET'])
def report_directives():
  directives = venture_engine.report_directives();
  return get_response(json.dumps(directives))
  
@app.route('/<int:directive_id>', methods=['POST'])
def forget(directive_id): # Check for DELETE!
  venture_engine.forget(directive_id)
  return get_response(json.dumps({"okay": True}))

@app.route('/infer', methods=['POST'])
def infer():
    MHiterations = json.loads(request.form["MHiterations"])
    t = venture_engine.infer(MHiterations)
    return get_response(json.dumps({"time": -1}))

@app.errorhandler(Exception)
def special_exception_handler(error):
  print "Error: " + str(error)
  return get_response("Your query has invoked an error:\n" + str(error)), 500

@app.route('/get_seed', methods=['GET'])
def get_seed():
  random_seed = venture_engine.get_seed()
  return get_response(json.dumps(random_seed))

@app.route('/set_seed', methods=['POST'])
def set_seed():
  venture_engine.set_seed(int(request.form['random_seed'])) # FIXME: Why it is not an integer by default?
  return get_response(json.dumps({"okay": True}))

@app.route('/get_entropy_info', methods=['GET'])
def get_entropy_info():
  entropy_info = venture_engine.get_entropy_info()
  return get_response(json.dumps(entropy_info))

# try:
app.config['DEBUG'] = False
app.config['TESTING'] = False
# app.config['SERVER_NAME'] = "ec2-174-129-93-113.compute-1.amazonaws.com"
# app.run(port=81, host='0.0.0.0')
