from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureError
import venture.lite.types as t

from venture.mite.sp import VentureSP
from venture.mite.sp import ApplicationKernel
from venture.mite.sp_registry import registerBuiltinSP
from venture.mite.sps.compound import CompoundSP
from venture.mite.evaluator import Evaluator

def pair(a, b):
  # for constructing request IDs from (application id, index) pairs
  # return t.Pair(t.Blob, t.Int).asVentureValue((a, b))
  return (a, b)

class TailAssessableCompoundSP(VentureSP):
  def __init__(self, params, operator_exp, operand_exps, env):
    super(TailAssessableCompoundSP, self).__init__()
    self.params = params
    self.operator_exp = operator_exp
    self.operand_exps = operand_exps
    self.env = env

  def apply(self, trace_handle, application_id, inputs):
    if len(self.params) != len(inputs):
      raise VentureError("Wrong number of arguments: " \
        "compound takes exactly %d arguments, got %d." \
        % (len(self.params), len(inputs)))
    extendedEnv = VentureEnvironment(self.env, self.params, inputs)

    operator = trace_handle.new_request(
      pair(application_id, 0), self.operator_exp, extendedEnv)
    operator = trace_handle.value_at(operator)

    operands = []
    for index, operand_exp in enumerate(self.operand_exps):
      operand = trace_handle.new_request(
        pair(application_id, index+1), operand_exp, extendedEnv)
      operands.append(trace_handle.value_at(operand))

    result_addr = trace_handle.request_address(application_id)
    output = trace_handle.trace.apply_sp(result_addr, operator, operands)

    return output

  def proposal_kernel(self, trace_handle, application_id):
    return TailAssessableProposalKernel(self, trace_handle, application_id)

  def constrained_kernel(self, trace_handle, application_id, val):
    return TailAssessableConstrainedKernel(self, trace_handle, application_id, val)

class TailAssessableProposalKernel(ApplicationKernel):
  def __init__(self, sp, trace_handle, application_id):
    self.params = sp.params
    self.operator_exp = sp.operator_exp
    self.operand_exps = sp.operand_exps
    self.env = sp.env

    self.trace_handle = trace_handle
    self.application_id = application_id

  def extract(self, output, _inputs):
    trace_handle = self.trace_handle
    application_id = self.application_id

    operator = trace_handle.get_request(pair(application_id, 0))
    operator = trace_handle.value_at(operator)

    operands = []
    for index in range(len(self.operand_exps)):
      operand = trace_handle.get_request(pair(application_id, index+1))
      operands.append(trace_handle.value_at(operand))

    result_addr = trace_handle.request_address(application_id)
    (weight, trace_fragment) = trace_handle.trace.extract_kernel(
      trace_handle.trace.proposal_kernel(result_addr, operator),
      output, operands)

    for index in reversed(range(len(self.operand_exps))):
      trace_handle.free_request(pair(application_id, index+1))

    trace_handle.free_request(pair(application_id, 0))

    return (weight, trace_fragment)

  def regen(self, inputs):
    trace_handle = self.trace_handle
    application_id = self.application_id

    if len(self.params) != len(inputs):
      raise VentureError("Wrong number of arguments: " \
        "compound takes exactly %d arguments, got %d." \
        % (len(self.params), len(inputs)))
    extendedEnv = VentureEnvironment(self.env, self.params, inputs)

    operator = trace_handle.new_request(
      pair(application_id, 0), self.operator_exp, extendedEnv)
    operator = trace_handle.value_at(operator)

    operands = []
    for index, operand_exp in enumerate(self.operand_exps):
      operand = trace_handle.new_request(
        pair(application_id, index+1), operand_exp, extendedEnv)
      operands.append(trace_handle.value_at(operand))

    result_addr = trace_handle.request_address(application_id)
    (weight, output) = trace_handle.trace.regen_kernel(
      trace_handle.trace.proposal_kernel(result_addr, operator),
      operands, None)

    return (weight, output)

  def restore(self, _inputs, trace_fragment):
    trace_handle = self.trace_handle
    application_id = self.application_id

    operator = trace_handle.restore_request(pair(application_id, 0))
    operator = trace_handle.value_at(operator)

    operands = []
    for index in range(len(self.operand_exps)):
      operand = trace_handle.restore_request(pair(application_id, index+1))
      operands.append(trace_handle.value_at(operand))

    result_addr = trace_handle.request_address(application_id)
    output = trace_handle.trace.restore_kernel(
      trace_handle.trace.proposal_kernel(result_addr, operator),
      operands, trace_fragment)

    return output

class TailAssessableConstrainedKernel(ApplicationKernel):
  def __init__(self, sp, trace_handle, application_id, val):
    self.params = sp.params
    self.operator_exp = sp.operator_exp
    self.operand_exps = sp.operand_exps
    self.env = sp.env

    self.trace_handle = trace_handle
    self.application_id = application_id
    self.val = val

  def extract(self, output, _inputs):
    trace_handle = self.trace_handle
    application_id = self.application_id
    val = self.val

    operator = trace_handle.get_request(pair(application_id, 0))
    operator = trace_handle.value_at(operator)

    operands = []
    for index in range(len(self.operand_exps)):
      operand = trace_handle.get_request(pair(application_id, index+1))
      operands.append(trace_handle.value_at(operand))

    result_addr = trace_handle.request_address(application_id)
    (weight, trace_fragment) = trace_handle.trace.extract_kernel(
      trace_handle.trace.constrained_kernel(result_addr, operator, val),
      output, operands)

    return (weight, trace_fragment)

  def regen(self, _inputs):
    trace_handle = self.trace_handle
    application_id = self.application_id
    val = self.val

    operator = trace_handle.get_request(pair(application_id, 0))
    operator = trace_handle.value_at(operator)

    operands = []
    for index in range(len(self.operand_exps)):
      operand = trace_handle.get_request(pair(application_id, index+1))
      operands.append(trace_handle.value_at(operand))

    result_addr = trace_handle.request_address(application_id)
    (weight, output) = trace_handle.trace.regen_kernel(
      trace_handle.trace.constrained_kernel(result_addr, operator, val),
      operands, None)

    return (weight, output)

  def restore(self, _inputs, trace_fragment):
    trace_handle = self.trace_handle
    application_id = self.application_id
    val = self.val

    operator = trace_handle.restore_request(pair(application_id, 0))
    operator = trace_handle.value_at(operator)

    operands = []
    for index in range(len(self.operand_exps)):
      operand = trace_handle.restore_request(pair(application_id, index+1))
      operands.append(trace_handle.value_at(operand))

    result_addr = trace_handle.request_address(application_id)
    output = trace_handle.trace.restore_kernel(
      trace_handle.trace.constrained_kernel(result_addr, operator, val),
      operands, trace_fragment)

    return output

class MakeTailAssessableSP(VentureSP):
  def apply(self, trace_handle, _id, inputs):
    assert len(inputs) == 1
    sp = trace_handle.value_at(
      trace_handle.trace.deref_sp(
        trace_handle.value_at(inputs[0])))
    assert isinstance(sp, CompoundSP)
    return TailAssessableCompoundSP(
      sp.params, sp.exp[0], sp.exp[1:], sp.env)

  def unapply(self, trace_handle, _id, output, inputs):
    pass

  def restore(self, trace_handle, _id, inputs, frag):
    pass

registerBuiltinSP("proc_", MakeTailAssessableSP())
