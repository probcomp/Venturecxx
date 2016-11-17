from venture.parser.church_prime.parse import ChurchPrimeParser
from venture.sivm.core_sivm import _modify_expression
from venture.sivm.macro_system import desugar_expression

import venture.lite.exp as e
import venture.lite.types as t
import venture.lite.value as v

from venture.mite.sp_registry import registerBuiltinSP
import venture.mite

def each_defn(fname):
  with open(fname) as f:
    source = f.read()
  parser = ChurchPrimeParser.instance()
  instructions = parser.parse_instructions(source)
  for instr in instructions:
    assert instr['instruction'] == 'define'
    name = t.Symbol.asPython(v.VentureValue.fromStackDict(instr['symbol']))
    expr_dict = _modify_expression(desugar_expression(instr['expression']))
    expr = t.Exp.asPython(v.VentureValue.fromStackDict(expr_dict))
    yield (name, expr)

def first_prelude():
  for (name, expr) in each_defn(venture.mite.__path__[0] + '/prelude.vnt'):
    assert e.isLambda(expr)
    (params, body) = e.destructLambda(expr)
    registerBuiltinSP(name, (params, body))

first_prelude()
