import socket
import json

def sendItems(s,items):
  for item in items:
    s.sendall(item + "#")

def desugarLambda(datum):
  if type(datum) is list and type(datum[0]) is dict and datum[0]["value"] == "lambda":
    ids = [{"type" : "symbol","value" : "quote"}] + [datum[1]]
    body = [{"type" : "symbol","value" : "quote"}] + [desugarLambda(datum[2])]
    return [{"type" : "symbol", "value" : "make_csp"},ids,body]
  elif type(datum) is list: return [desugarLambda(d) for d in datum]
  else: return datum

class Engine:
  def __init__(self,host="localhost",port=2000):
    # connect to julia
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.s.connect((host, port))

  def execute(self,directive):
    data_out = json.dumps(directive) + "#"
    print "about to execute: ", data_out
    self.s.sendall(data_out)
    retval = self.s.recv(1024)
    print "received: ", retval
    return json.loads(retval)

  def assume(self,sym,exp): return self.execute(["assume",sym,desugarLambda(exp)])
  def predict(self,exp): return self.execute(["predict",desugarLambda(exp)])
  def observe(self,exp,value): return self.execute(["observe",desugarLambda(exp),value])
  def report_value(self,id): return self.execute(["report_value",id])
  def infer(self,params): return self.execute(["infer",params])
  def reset(self): return self.execute(["reset"])

  def continuous_inference_status(self): return {"running" : False}
