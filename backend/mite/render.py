import json as j
from collections import OrderedDict

import venture.lite.types as t
import venture.lite.value as v
import venture.parser.church_prime.parse as parse

import venture.mite.address as addr

# FlatTrace has self.requests, self.results, self.made_sps (?),
# self.observations, self.global_env

# DependencyGraphTrace additionally has self.nodes and self.children,
# which may be redundant

def jsonable(trace):
  return { "requests" : _jsonable_dict(trace.requests, _jsonable_address, _jsonable_request),
           "results" : _jsonable_dict(trace.results, _jsonable_address, _jsonable_vv),
           "observations" : _jsonable_dict(trace.observations, _jsonable_address, _jsonable_vv),
           "global_env" : _jsonable_environment(trace.global_env) }

def identity(x): return x

def _jsonable_dict(d, key_map, val_map=identity):
  ans = OrderedDict()
  for (k, val) in d.iteritems():
    if isinstance(k, addr.BuiltinAddress):
      continue
    ans[key_map(k)] = val_map(val)
  return ans

def _jsonable_environment(e):
  if e is None:
    return []
  elif e.outerEnv is None:
    # This is the builtin frame of the global environment; skip it since it's standard
    return []
  else:
    return [_jsonable_dict(e.frame, identity, lambda n: _jsonable_address(n.address))] \
      + _jsonable_environment(e.outerEnv)

def _jsonable_request((exp, env)):
  # TODO: Identify the global environment, and perhaps other
  # environment sharing.
  return (_jsonable_exp(exp), _jsonable_environment(env))

def _jsonable_address(address):
  if isinstance(address, addr.DirectiveAddress):
    return "dir(" + str(address.directive_id) + ")"
  elif isinstance(address, addr.SubexpressionAddress):
    return _jsonable_address(address.parent) + "/" + str(address.index)
  elif isinstance(address, addr.RequestAddress):
    return _jsonable_address(address.sp_addr) + ":" + _jsonable_request_id(address.request_id)
  else:
    raise Exception("Unknown address %s of type %s" % (address, type(address)))

def _jsonable_request_id(r_id):
  if isinstance(r_id, addr.Address):
    return _jsonable_address(r_id)
  else:
    return str(r_id)

def _jsonable_exp(exp):
  expr = t.Exp.asVentureValue(exp).asStackDict()
  return parse.ChurchPrimeParser.instance().unparse_expression(expr)

def _jsonable_vv(vv):
  if isinstance(vv, v.VentureNumber):
    return vv.getNumber()
  if isinstance(vv, v.VentureInteger):
    return vv.getNumber()
  if isinstance(vv, v.VentureSymbol):
    return vv.getSymbol()
  if isinstance(vv, v.VentureBool):
    return vv.getBool()
  elif isinstance(vv, v.SPRef):
    return "a procedure"
  elif isinstance(vv, v.VentureArray):
    return [_jsonable_vv(val) for val in vv.getArray()]
  else:
    raise Exception("Oops, missed venture value %s of type %s" % (vv, type(vv)))

def json(trace):
  return j.dumps(jsonable(trace), indent=2)
