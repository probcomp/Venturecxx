from venture.parser.church_prime.parse import ChurchPrimeParser
from venture.sivm.macro_system import desugar_expression
from venture.sivm.core_sivm import _modify_expression

import venture.lite.exp as e
import venture.lite.types as t
import venture.lite.value as v

import venture.mite
from venture.mite.sp_registry import registerBuiltinSP

with open(venture.mite.__path__[0] + '/prelude.vnt') as f:
  prelude_source = f.read()

parser = ChurchPrimeParser.instance()
instructions, _ = parser.split_program(prelude_source)
for instruction in instructions:
  instr = parser.parse_instruction(instruction)
  assert instr['instruction'] == 'define'
  name = t.Symbol.asPython(v.VentureValue.fromStackDict(instr['symbol']))
  expr = _modify_expression(desugar_expression(instr['expression']))
  expr = t.Exp.asPython(v.VentureValue.fromStackDict(expr))
  assert e.isLambda(expr)
  (params, body) = e.destructLambda(expr)
  registerBuiltinSP(name, (params, body))
