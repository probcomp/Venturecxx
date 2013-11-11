
disable_REST_server_logger = True

import flask
from flask import request
from flask import make_response

# Why it disables the output for the flask?
if disable_REST_server_logger is True:
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
    
def start_venture_server(specified_port):
  import venture._engine as venture_engine

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

  print "Starting Venture server on the port #" + str(specified_port)
  app.run(port=specified_port, host='0.0.0.0')
