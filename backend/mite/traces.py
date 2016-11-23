from collections import OrderedDict
import copy
import random

import numpy as np

from venture.lite.env import EnvironmentType
from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureError
from venture.lite.value import SPRef
from venture.untraced.node import Node
import venture.lite.exp as e
import venture.lite.types as t

from venture.mite.evaluator import Evaluator
from venture.mite.evaluator import Regenerator
from venture.mite.evaluator import Restorer
from venture.mite.scaffold import DefaultAllScaffold
from venture.mite.scaffold import Scaffold
from venture.mite.scaffold import single_site_scaffold
from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.sps.compound import CompoundSP
from venture.mite.state import TraceConstructorSP
from venture.mite.state import register_trace_type
from venture.mite.state import trace_action
from venture.mite.state import trace_property
import venture.mite.address as addresses


class ITrace(object):
  # external trace interface exposed to VentureScript

  def __init__(self):
    self.global_env = None

  def copy(self):
    raise NotImplementedError

  def next_base_address(self):
    raise NotImplementedError

  def eval_request(self, address, expression, environment):
    raise NotImplementedError

  def bind_global(self, symbol, address):
    raise NotImplementedError

  def register_observation(self, address, value):
    raise NotImplementedError

  def get_observations(self):
    raise NotImplementedError

  def value_at(self, address):
    raise NotImplementedError

  def extract(self, subproblem):
    raise NotImplementedError

  def regen(self, subproblem, trace_fragment):
    raise NotImplementedError

  def restore(self, subproblem, trace_fragment):
    raise NotImplementedError

  def weight_bound(self, subproblem):
    raise NotImplementedError

_trace_id = 0

class AbstractTrace(ITrace):
  # common implementation of trace interface
  # defines internal interface for concrete trace representations

  def __init__(self, seed):
    super(AbstractTrace, self).__init__()
    prng = random.Random(seed)
    global _trace_id
    self.trace_id = _trace_id
    _trace_id += 1
    self.np_prng = np.random.RandomState(prng.randint(1, 2**31 - 1))
    self.py_prng = random.Random(prng.randint(1, 2**31 - 1))
    self.directive_counter = 0
    self.global_env = VentureEnvironment(self.builtin_environment())
    self.observations = {}

  def builtin_environment(self):
    from venture.mite.builtin import builtInSPs
    from venture.mite.builtin import builtInValues
    builtin_env = VentureEnvironment()
    for name, value in builtInValues().iteritems():
      addr = addresses.builtin(name)
      self.register_constant(addr, value)
      builtin_env.addBinding(name, Node(addr, value))
    for name, sp in builtInSPs().iteritems():
      if isinstance(sp, tuple):
        # assume compound definition
        # TODO define a namedtuple?
        (params, body) = sp
        sp = CompoundSP(params, body, builtin_env)
      addr = addresses.builtin(name)
      self.register_constant(addr, sp)
      value = self.register_made_sp(addr, sp)
      builtin_env.addBinding(name, Node(addr, value))
    return builtin_env

  def copy(self):
    new_trace = copy.deepcopy(self)
    new_trace.reseed(self)
    return new_trace

  def reseed(self, other):
    prng = other.py_prng
    self.np_prng = np.random.RandomState(prng.randint(1, 2**31 - 1))
    self.py_prng = random.Random(prng.randint(1, 2**31 - 1))

  def next_base_address(self):
    self.directive_counter += 1
    return addresses.directive(self.directive_counter, self.trace_id)

  def predict_next_base_address(self):
    return self.directive_counter + 1

  def eval_request(self, addr, exp, env):
    weight, value = Evaluator(self).eval_request(addr, exp, env)
    assert weight == 0
    return value

  def bind_global(self, symbol, addr):
    value = self.value_at(addr)
    self.global_env.addBinding(symbol, Node(addr, value))

  def select(self, _selector):
    return DefaultAllScaffold()

  def pyselect(self, code, ctx=None):
    selector = eval(code, vars(addresses), ctx)
    return Scaffold(selector)

  def single_site_subproblem(self, address, kernel=None):
    scaffold = single_site_scaffold(self, address, kernel)
    if scaffold.kernels:
      return scaffold
    else:
      self.print_stack(address)
      assert scaffold.kernels, "Scaffold construction around %s found no kernels in trace %s" % (address, self.trace_id)

  def _sites(self):
    def is_random_application(addr, exp):
      if not e.isApplication(exp):
        return False
      sp_ref = self.value_at(addresses.subexpression(0, addr))
      sp = self.deref_sp(sp_ref).value
      return not sp.is_deterministic()
    return [a for (a, exp, _) in self.all_contexts() if is_random_application(a, exp)]

  def random_site(self):
    """Return a uniformly random address among the random choices in this trace."""
    return self.py_prng.choice(self._sites())

  def num_sites(self):
    return len(self._sites())

  def register_observation(self, addr, value):
    self.observations[addr] = value

  def get_observations(self):
    return self.observations

  def invoke_metaprogram_of_sp(self, sp_ref, key, input_values):
    sp_node = self.deref_sp(sp_ref)
    sp = sp_node.value
    return sp.run_in_helper_trace(key, input_values)

  # remainder of the interface, to be implemented by subclasses

  def register_request(self, addr, exp, env):
    raise NotImplementedError

  def register_constant(self, addr, value):
    raise NotImplementedError

  def register_lookup(self, addr, node):
    raise NotImplementedError

  def register_application(self, addr, arity, value):
    raise NotImplementedError

  def register_made_sp(self, addr, value):
    raise NotImplementedError

  def deref_sp(self, sp_ref):
    raise NotImplementedError

  def value_at(self, addr):
    raise NotImplementedError


class ResultTrace(object):
  """Common interface and implementation of recording results of evaluation."""

  def __init__(self, seed):
    self.results = OrderedDict()
    super(ResultTrace, self).__init__(seed)

  def record_result(self, addr, value):
    if value is not None:
      # XXX This check is here to allow RequesterConstraintKernel to
      # return no value, as indeed its effect must not update the
      # value at the address, since it concerns itself with only the
      # first stage.
      self.results[addr] = value

  def forget_result(self, addr):
    del self.results[addr]

  def has_value_at(self, addr):
    if addr in self.results:
      return True
    candidate = addresses.interpret_address_in_trace(addr, self.trace_id, None)
    return candidate in self.results

  def value_at(self, addr):
    try:
      return self.results[addr]
    except KeyError:
      candidate = addresses.interpret_address_in_trace(addr, self.trace_id, None)
      if candidate in self.results:
        return self.results[candidate]
      else:
        print "Unable to locate value at", addr, "or", candidate, "in", self
        self.print_stack(candidate)
        raise

class BlankTrace(ResultTrace, AbstractTrace):
  """Record only the final results of requested expressions.

  This corresponds to "untraced" evaluation, and supports forward
  evaluation and rejection sampling only.

  """

  def __init__(self, seed):
    super(BlankTrace, self).__init__(seed)

  def extract(self, _subproblem):
    raise VentureError("Cannot extract from a BlankTrace.")

  def regen(self, _subproblem, _trace_fragment):
    raise VentureError("Cannot regen in a BlankTrace.")

  def restore(self, _subproblem, _trace_fragment):
    raise VentureError("Cannot restore in a BlankTrace.")

  def weight_bound(self, _subproblem):
    raise VentureError("Cannot compute weight bounds in a BlankTrace.")

  def register_request(self, addr, exp, env): pass

  def register_constant(self, addr, value):
    self.maybe_record_result(addr, value)

  def register_lookup(self, addr, node):
    self.maybe_record_result(addr, node.value)

  def register_application(self, addr, arity, value):
    self.maybe_record_result(addr, value)

  def maybe_record_result(self, addr, value):
    if isinstance(addr, addresses.DirectiveAddress):
      self.record_result(addr, value)
    elif isinstance(addr, addresses.RequestAddress):
      # record the result of a request, in case the value at the same
      # id is requested again (like mem).
      # XXX except we don't want to have to store the result of every
      # compound procedure call, so...
      # heuristic: if the request id is an address, assume it's unique
      # and won't be requested again
      if not isinstance(addr.request_id, addresses.Address):
        self.record_result(addr, value)

  def register_made_sp(self, addr, sp):
    ret = SPRef(Node(addr, sp))
    if addr in self.results:
      assert self.results[addr] is sp
      self.record_result(addr, ret)
    return ret

  def deref_sp(self, sp_ref):
    return sp_ref.makerNode


class ICompleteTrace(ITrace):
  """A kind of trace that maintains the full execution history (somehow).

  This is as opposed to BlankTrace, which only retains the results of toplevel
  evaluations."""

  ## low level operations for manual inference programming

  def find_symbol(self, env, symbol):
    """Look up the address of the given symbol's binding expression."""
    raise NotImplementedError

  def set_value_at(self, addr, value):
    """Low-level set the value at a given address.  May leave the trace in
    an inconsistent state."""
    raise NotImplementedError

  def apply_sp(self, addr, sp_ref, input_values):
    """Compute the result of applying the given SP (by reference) to the
    given inputs at the given address."""
    raise NotImplementedError

  def log_density_of_sp(self, sp_ref, output, input_values):
    """Compute the log density of the given SP (by reference) at the given output and inputs."""
    raise NotImplementedError

  def proposal_kernel(self, addr, sp_ref):
    """Produce a proposal kernel for the given SP (by reference) at the given address."""
    raise NotImplementedError

  def constraint_kernel(self, addr, sp_ref, val):
    """Produce a constraint kernel for the given SP (by reference) at the
    given address to produce the given value."""
    raise NotImplementedError

class AbstractCompleteTrace(ICompleteTrace):

  def __init__(self, seed):
    super(AbstractCompleteTrace, self).__init__(seed)

  def register_made_sp(self, addr, sp):
    assert self.results[addr] is sp
    ret = SPRef(Node(addr, sp))
    self.record_result(addr, ret)
    return ret

  def unregister_made_sp(self, addr):
    ref = self.value_at(addr)
    node = self.deref_sp(ref)
    sp = node.value
    self.record_result(addr, sp)
    return sp

  def deref_sp(self, sp_ref):
    return sp_ref.makerNode

  def find_symbol(self, env, symbol):
    node = env.findSymbol(symbol)
    return node.address

  def set_value_at(self, addr, value):
    # low level operation. may leave the trace in an inconsistent state
    self.record_result(addr, value)

  def apply_sp(self, addr, sp_ref, input_values):
    # TODO for now this auto-derefs the SP; is this what we want, or
    # should we just expose deref_sp separately?
    sp_node = self.deref_sp(sp_ref)
    inputs = []
    for index, val in enumerate(input_values):
      subaddr = addresses.subexpression(index + 1, addr)
      inputs.append(Node(subaddr, val))
    (weight, output) = Evaluator(self).apply_sp(addr, sp_node, inputs)
    assert weight == 0
    return output

  def log_density_of_sp(self, sp_ref, output, input_values):
    sp_node = self.deref_sp(sp_ref)
    sp = sp_node.value
    return sp.log_density(output, input_values)

  def proposal_kernel(self, addr, sp_ref):
    # XXX for now just store the dicts, with extra attributes
    # TODO make it easier to construct trace handles.
    return {'addr': addr, 'sp_ref': sp_ref, 'type': 'proposal'}

  def constraint_kernel(self, addr, sp_ref, val):
    return {'addr': addr, 'sp_ref': sp_ref,
            'type': 'constraint', 'val': val}


class SourceTracing(object):
  """Traces source code of the execution."""

  def __init__(self, seed):
    self.requests = OrderedDict()
    self.toplevel_addresses = []
    super(SourceTracing, self).__init__(seed)

  def register_request(self, addr, exp, env):
    if addr in self.requests:
      (old_exp, old_env) = self.requests[addr]
      print "Multiply registering request at", addr
      print "Old request", old_exp, old_env
      print "New request", exp, env
      self.print_stack(addr)
      old_env.printEnv()
      env.printEnv()
      assert False, "Multiply registering request"
    if isinstance(addr, addresses.DirectiveAddress):
      self.toplevel_addresses.append(addr)
    self.requests[addr] = (exp, env)

  def unregister_request(self, addr):
    assert not isinstance(addr, addresses.DirectiveAddress)
    del self.requests[addr]

  def all_contexts(self):
    """A generator that yields every (addr, exp, env) triple traced by this trace, in execution order, _except requests_."""
    for (addr, (exp, env)) in self.requests.iteritems():
      for context in self._traverse(addr, exp, env):
        yield context

  def _traverse(self, addr, exp, env):
    if e.isApplication(exp):
      for index, subexp in enumerate(e.subexpressions(exp)):
        subaddr = addresses.subexpression(index, addr)
        for context in self._traverse(subaddr, subexp, env):
          yield context
    yield (addr, exp, env)

  # Note: This also admits a context_at(self, addr) function that will
  # return the exp-env corresponding to a given address.  The way to
  # implement it is to unroll layers of SubexpressionAddress from the
  # argument until finding something present in self.requests, and
  # then roll the above traversal forward guided by said
  # SubexpressionAddress indexes.

  def print_frame(self, addr, stream=None):
    (root, branch) = addresses.split_subexpression(addr)
    (exp, _env) = self.requests[root]
    import venture.parser.church_prime.parse as parser
    p = parser.ChurchPrimeParser.instance()
    string = p.unparse_expression(exp)
    ind = p.expression_index_to_text_index(string, branch)
    from venture.exception import underline
    if stream is not None:
      print >>stream, string
      print >>stream, underline(ind)
    else:
      print string
      print underline(ind)

  def print_stack(self, addr, stream=None):
    (root, _branch) = addresses.split_subexpression(addr)
    if isinstance(root, addresses.RequestAddress) and \
       isinstance(root.request_id, addresses.Address):
      # Assume this was a compound procedure and the request id is the
      # call site
      self.print_stack(root.request_id, stream=stream)
    # XXX TODO do something with `mem` RequestAddresses
    self.print_frame(addr, stream=stream)

class FlatTrace(SourceTracing, AbstractCompleteTrace, ResultTrace, AbstractTrace):
  """Maintain a flat lookup table of random choices, keyed by address.

  This corresponds to the "random database" implementation approach
  from Wingate et al (2011).

  """

  def register_constant(self, addr, value):
    self.record_result(addr, value)

  def register_lookup(self, addr, node):
    assert node.value is self.results[node.address]
    self.record_result(addr, node.value)

  def register_application(self, addr, arity, value):
    self.record_result(addr, value)

  def extract_kernel(self, kernel, output, input_values):
    addr = kernel['addr']
    sp_ref = kernel['sp_ref']
    subproblem = Scaffold({addr: kernel})
    sp_node = self.deref_sp(sp_ref)
    inputs = []
    for index, val in enumerate(input_values):
      subaddr = addresses.subexpression(index + 1, addr)
      inputs.append(Node(subaddr, val))
    ctx = Regenerator(self, subproblem)
    weight = ctx.unapply_sp(addr, output, sp_node, inputs)
    fragment = ctx.fragment
    return (weight, fragment)

  def regen_kernel(self, kernel, input_values, trace_fragment=None):
    addr = kernel['addr']
    sp_ref = kernel['sp_ref']
    subproblem = Scaffold({addr: kernel})
    sp_node = self.deref_sp(sp_ref)
    inputs = []
    for index, val in enumerate(input_values):
      subaddr = addresses.subexpression(index + 1, addr)
      inputs.append(Node(subaddr, val))
    ctx = Regenerator(self, subproblem, trace_fragment)
    (weight, output) = ctx.apply_sp(addr, sp_node, inputs)
    return (weight, output)

  def restore_kernel(self, kernel, input_values, trace_fragment):
    addr = kernel['addr']
    sp_ref = kernel['sp_ref']
    subproblem = Scaffold({addr: kernel})
    sp_node = self.deref_sp(sp_ref)
    inputs = []
    for index, val in enumerate(input_values):
      subaddr = addresses.subexpression(index + 1, addr)
      inputs.append(Node(subaddr, val))
    ctx = Restorer(self, subproblem, trace_fragment)
    (weight, output) = ctx.apply_sp(addr, sp_node, inputs)
    assert weight == 0
    return output

  ## support for regen/extract

  def unregister_constant(self, addr):
    self.forget_result(addr)

  def unregister_lookup(self, addr):
    self.forget_result(addr)

  def unregister_application(self, addr):
    self.forget_result(addr)

  def extract(self, subproblem):
    x = Regenerator(self, subproblem)
    weight = 0
    for addr in reversed(self.toplevel_addresses):
      (exp, env) = self.requests[addr]
      weight += x.uneval_family(addr, exp, env)
    return (weight, x.fragment)

  def regen(self, subproblem, trace_fragment):
    x = Regenerator(self, subproblem, trace_fragment)
    weight = 0
    for addr in self.toplevel_addresses:
      (exp, env) = self.requests[addr]
      w, _ = x.eval_family(addr, exp, env)
      weight += w
    return weight

  def restore(self, subproblem, trace_fragment):
    x = Restorer(self, subproblem, trace_fragment)
    for addr in self.toplevel_addresses:
      (exp, env) = self.requests[addr]
      x.eval_family(addr, exp, env)

  def weight_bound(self, subproblem):
    from venture.mite.evaluator import WeightBounder
    x = WeightBounder(self, subproblem)
    weight = 0
    for addr in reversed(self.toplevel_addresses):
      (exp, env) = self.requests[addr]
      weight += x.uneval_family(addr, exp, env)
    for addr in self.toplevel_addresses:
      (exp, env) = self.requests[addr]
      w, _ = x.eval_family(addr, exp, env)
      weight += w
    return weight


register_trace_type("_trace", ITrace, {
  "next_base_address": trace_action("next_base_address", [], t.Blob, deterministic=True),
  "global_env": trace_property("global_env", EnvironmentType()),
  "eval_request": trace_action("eval_request", [t.Blob, t.Exp, EnvironmentType()], t.Nil),
  "bind_global": trace_action("bind_global", [t.Symbol, t.Blob], t.Nil, deterministic=True),
  "register_observation": trace_action("register_observation", [t.Blob, t.Object], t.Nil, deterministic=True),
  "value_at": trace_action("value_at", [t.Blob], t.Object, deterministic=True),
  "find_symbol": trace_action("find_symbol", [EnvironmentType(), t.Symbol], t.Blob, deterministic=True),
  "set_value_at": trace_action("set_value_at", [t.Blob, t.Object], t.Nil, deterministic=True),
  "apply_sp": trace_action("apply_sp", [t.Blob, t.Object, t.List(t.Object)], t.Object),
  "log_density_of_sp": trace_action("log_density_of_sp", [t.Object, t.Object, t.List(t.Object)], t.Number),
  "invoke_metaprogram_of_sp": trace_action("invoke_metaprogram_of_sp", [t.Object, t.Symbol, t.List(t.Object)], t.Object),
  "proposal_kernel_of_sp_at": trace_action("proposal_kernel", [t.Blob, t.Object], t.Blob),
  "constraint_kernel_of_sp_at": trace_action("constraint_kernel", [t.Blob, t.Object, t.Object], t.Blob),
  "extract_kernel": trace_action("extract_kernel", [t.Blob, t.Object, t.List(t.Object)], t.Pair(t.Number, t.Blob)),
  "regen_kernel": trace_action("regen_kernel", [t.Blob, t.List(t.Object)], t.Pair(t.Number, t.Object)),
  "restore_kernel": trace_action("restore_kernel", [t.Blob, t.List(t.Object), t.Blob], t.Object),
  "get_observations": trace_action("get_observations", [], t.Dict(t.Blob, t.Object), deterministic=True),
  "clone_trace": trace_action("copy", [], t.Blob, deterministic=True),
  "select": trace_action("select", [t.Object], t.Blob),
  "pyselect": trace_action("pyselect", [t.String], t.Blob),
  "pyselectf": trace_action("pyselect", [t.String, t.Dict(t.Symbol, t.Object)], t.Blob),
  "single_site_subproblem": trace_action("single_site_subproblem", [t.Blob], t.Blob),
  "single_site_subproblem_": trace_action("single_site_subproblem", [t.Blob, t.Blob], t.Blob),
  "_random_site": trace_action("random_site", [], t.Blob),
  "_num_sites": trace_action("num_sites", [], t.Number, deterministic=True),
  "extract": trace_action("extract", [t.Blob], t.Pair(t.Number, t.Blob)),
  "regen": trace_action("regen", [t.Blob, t.Blob], t.Number),
  "restore": trace_action("restore", [t.Blob, t.Blob], t.Nil),
  "weight_bound": trace_action("weight_bound", [t.Blob], t.Number),
})


class VentureTraceConstructorSP(TraceConstructorSP):
  def simulate(self, _inputs, prng):
    seed = prng.py_prng.randint(1, 2**31 - 1)
    return t.Blob.asVentureValue(self.trace_class(seed))

registerBuiltinSP("blank_trace", VentureTraceConstructorSP(BlankTrace))
registerBuiltinSP("flat_trace", VentureTraceConstructorSP(FlatTrace))
