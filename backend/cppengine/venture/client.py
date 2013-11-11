import venture.utils

import requests
import pdb # Question from Yura: for what do we need it?
try: # See for details: http://stackoverflow.com/questions/791561/python-2-5-json-module
    import json
except ImportError:
    import simplejson as json 

# Requirement for the engines server side of the REST:
# engines should consider only the URL part before
# the question mark "?". For example, in the request
# "GET /logscore?time=151225" the engine should consider
# only the "GET /logscore".
  
# Another necessary requirement for the engines: engines must add the header
# "Access-Control-Allow-Origin"
# with the value
# "*"
# to all responses, including the error responses! (In order to satisfy some
# browsers needs when the RIPL terminal is located on one domain,
# and the engine itself is located on another domain)
  
# Strong recommendation for all REST clients: to add
# "?time=" + current_time() + "&random_value=" + rand()
# to all requests (or something similar) (to avoid potential caching).
  
class BadRequestStatus(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
            
def CheckStatus(request_object):
    if (request_object.status_code != 200):
      raise BadRequestStatus(str('Bad status code: ' + str(request_object.status_code) + '. Return message from the engine: "' + request_object.content + '"'))
           
class RemoteRIPL():
  """
  uri --- the URI of the REST RIPL server to connect to
  """
  def __init__(self, host, port):
    self.uri = "http://" + host + ":" + str(port)

  def get_seed(self):
    r = requests.get(self.uri + '/get_seed')
    CheckStatus(r)
    random_seed = json.loads(r.content)
    return random_seed

  def set_seed(self, random_seed):
    payload = {"random_seed": json.dumps(random_seed)}
    r = requests.post(self.uri + '/set_seed', data=payload)
    CheckStatus(r)

  def assume(self, name_str, expr_lst):
    payload = {"name_str": json.dumps(name_str),
               "expr_lst": json.dumps(expr_lst)}
    r = requests.post(self.uri + '/assume', data=payload)
    CheckStatus(r)
    return_dict = json.loads(r.content)
    return (return_dict["d_id"], return_dict["val"])

  def observe(self, expr_lst, literal_val):
    payload = {"expr_lst": json.dumps(expr_lst),
               "literal_val": json.dumps(literal_val)}
    r = requests.post(self.uri + '/observe', data=payload)
    CheckStatus(r)
    return json.loads(r.content)["d_id"]

  def predict(self, expr_lst):
    payload = {"expr_lst": json.dumps(expr_lst)}
    r = requests.post(self.uri + '/predict', data=payload)
    CheckStatus(r)
    return_dict = json.loads(r.content)
    return (return_dict["d_id"], return_dict["val"])
  
  def forget(self, directive_id):
    # FIXME: This REST choice interacts badly with proxies. This FIXME is deprecated?
    r = requests.post(self.uri + '/' + str(directive_id), data = {"DELETE": "yes"})
    CheckStatus(r)

  def clear(self):
    # FIXME: This REST choice interacts badly with proxies. This FIXME is deprecated?
    r = requests.post(self.uri + '/', data = {"DELETE": "yes"})
    CheckStatus(r)

  def infer(self, MHiterations, rerun = False, threadsNumber = 1):
    # FIXME: Define and support a proper config
    payload = {"MHiterations": MHiterations,
               "rerun": int(rerun),
               "threadsNumber": threadsNumber}
    r = requests.post(self.uri + "/infer", data=payload)
    CheckStatus(r)
    return_dict = json.loads(r.content)
    return return_dict # Returns the time consumption
                       # (JSON dictionary["time"] = real-value, number of milliseconds)
                       # of the inference in milliseconds.
                       # The value type is real because some engines, perhaps, may provide
                       # the more precise result than just in milliseconds.

  def memory(self):
    r = requests.get(self.uri + '/memory')
    CheckStatus(r)
    return_dict = json.loads(r.content)
    return return_dict # Returns the memory consumption
                       # (JSON dictionary["memory"] = integer)
                       # of the engine in bytes.
    
  def mhstats(self):
    r = requests.get(self.uri + '/mhstats')
    CheckStatus(r)
    return_dict = json.loads(r.content)
    return return_dict # Returns the dictionary with N keys, where each key is an unique
                       # "address" of a node in the trace. Each value is the dictionary
                       # itself with two keys: "made-proposals" = number of made MH proposals,
                       # and "accepted-proposals" = number of accepted MH proposals.
                       # These numbers are being kept after the RIPL.clear(),
                       # i.e. RIPL.clear() clears these counters.
                       #
                       # This statistics logging is by default "off". The user control
                       # the logging by two commands below.
                       #
                       # This also should work for the random DB engines.
    
  def mhstats_on(self):
    r = requests.post(self.uri + '/mhstats/on')
    CheckStatus(r) # Switches "on" the logging of MH proposals
                   # statistics.
                       
  def mhstats_off(self):
    r = requests.post(self.uri + '/mhstats/off')
    CheckStatus(r) # Switches "off" the logging of MH proposals
                   # statistics.
                   # Also clears the statistics.
                       
  def enumerate(self, truncation_config=None):
      raise Exception("not implemented")

  def report_directives(self, directive_type=None):
    if directive_type is not None:
      raise Exception("not implemented")
    r = requests.get(self.uri + '/')
    CheckStatus(r)
    return json.loads(r.content) # FIXME: Describe the format.

  def report_value(self, directive_id):
    r = requests.get(self.uri + '/' + str(directive_id))
    CheckStatus(r)
    contents = json.loads(r.content)
    if "val" in contents:
      return contents["val"] # is deprecated
    else:
      return contents["value"]

  def logscore(self, directive_id=None):
    if directive_id == None:
      # Get the logscore of the whole trace,
      # including the outermost XRP applications.
      r = requests.get(self.uri + '/logscore')
      CheckStatus(r)
      contents = json.loads(r.content)
      return contents['logscore'] # Returns the dictionary with the key 'total_logscore'.
    else:
      # Get the logscore of the outermost
      # XRP of the OBSERVE directive.
      r = requests.get(self.uri + '/logscore/' + str(directive_id))
      CheckStatus(r)
      contents = json.loads(r.content)
      return contents # Returns the dictionary with the key 'directive_logscore'.
      
  def logscore_wo_outermost_XRPs(self):
    # *** DRAFT ***:
    # is_continuous_inference = self.cont_infer_status()[...]
    # if is_continuous_inference:
      # self.stop_cont_infer()
    # total = self.logscore()
    # all_directives = report_directives()
    # for all_directives as directive
      # total += self.logscore(directive.id)
    # if is_continuous_inference:
      # self.start_cont_infer()
    # return total
    raise Exception("not implemented")
      
  def get_entropy_info(self):
    r = requests.get(self.uri + '/get_entropy_info')
    CheckStatus(r)
    contents = json.loads(r.content)
    return contents # Now just returns the dictionary with the key 'unconstrained_random_choices'.
                    # In the future more keys are going to be added.
      
  def start_cont_infer(self, threadsNumber = 1): # Start continuous inference.
    payload = {"threadsNumber": threadsNumber}
    r = requests.post(self.uri + '/start_cont_infer', data=payload)
    CheckStatus(r)
      
  def stop_cont_infer(self): # Stop continuous inference.
    r = requests.post(self.uri + '/stop_cont_infer')
    CheckStatus(r)
      
  def cont_infer_status(self): # Get continuous inference status.
    r = requests.get(self.uri + '/cont_infer_status')
    CheckStatus(r)
    contents = json.loads(r.content)
    return contents

  def load(self, generative_model_string):
    return venture.utils.load_to_RIPL(self, generative_model_string)

  def sample(self, expression):
    return venture.utils.sample(self, expression)

  def force(self, expression, literal_value):
    return venture.utils.force(self, expression, literal_value)

  def get_log_probability(self, expression, literal_value):
    return venture.utils.get_log_probability(self, expression, literal_value)

def directives_to_string(directives): # Change 8: added new utility.
  info = []
  info_element = [] # Better through info_element.append(...)?
  info_element.append("ID")
  info_element.append("EXPRESSION")
  info_element.append("VALUE")
  info.append(info_element)
  print(info)
  while len(directives) > 0:
    directive = directives.pop()
    info_element = [0, 0, 0]
    info_element[0] = str(directive['directive-id'])
    info_element[1] = str(directive['directive-expression'])
    if (directive['directive-type'] == 'DIRECTIVE-ASSUME' or directive['directive-type'] == 'DIRECTIVE-PREDICT'):
      info_element[2] = str(directive['value'])
    else:
      info_element[2] = "-"
    info.append(info_element)

  max_lengths = [0, 0, 0]
  for i in range(len(info)):
    for j in range(3):
      info[i][j] = ' ' + info[i][j]
      limit = 45
      if (j == 2):
        limit = 10
      if (len(info[i][j]) > limit):
        info[i][j] = (info[i][j])[:(limit - 3)] + "..."
      info[i][j] = info[i][j] + ' '
      if (max_lengths[j] < len(info[i][j])):
        max_lengths[j] = len(info[i][j])

  output = ""
  for i in range(len(info)):
    if (i > 0):
      output = output + '\n'
    for j in range(3):
      output = output + info[i][j]
      for z in range(max_lengths[j] - len(info[i][j])):
        output = output + ' '
      output = output + '|'
    output = output
  return output
