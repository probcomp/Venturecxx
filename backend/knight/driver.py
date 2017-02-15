import argparse

from typing import Tuple # Pylint doesn't understand type comments pylint: disable=unused-import
from typing import cast

from venture.parser.venture_script.parse import VentureScriptParser
from venture.sivm.core_sivm import _modify_expression
from venture.sivm.macro_system import desugar_expression
import venture.lite.value as vv # Pylint doesn't understand type comments pylint: disable=unused-import

from venture.knight.regen import regen
from venture.knight.sp import init_env
from venture.knight.trace import Trace
from venture.knight.types import Def
from venture.knight.types import Exp # pylint: disable=unused-import
from venture.knight.types import Seq
from venture.knight.types import stack_dict_to_exp

def top_eval(form):
  # type: (str) -> Tuple[float, vv.VentureValue]
  stack_dict = cast(object, _modify_expression(desugar_expression(VentureScriptParser.instance().parse_expression(form))))
  return regen(stack_dict_to_exp(stack_dict), init_env(), Trace(), Trace())

def instr_to_exp(instr):
  # type: (object) -> Exp
  assert isinstance(instr, dict)
  assert 'instruction' in instr
  tp = instr['instruction']
  assert isinstance(tp, basestring)
  if tp == 'evaluate':
    assert 'expression' in instr
    expr = instr['expression']
    stack_dict = cast(object, _modify_expression(desugar_expression(expr)))
    return stack_dict_to_exp(stack_dict)
  elif tp == 'define':
    assert 'expression' in instr
    expr = instr['expression']
    stack_dict = cast(object, _modify_expression(desugar_expression(expr)))
    assert 'symbol' in instr
    sym = instr['symbol']
    assert isinstance(sym, dict)
    assert 'value' in sym
    return Def(sym['value'], stack_dict_to_exp(stack_dict))
  else:
    assert False

def toplevel(forms):
  # type: (str) -> Tuple[float, vv.VentureValue]
  instrs = VentureScriptParser.instance().parse_instructions(forms)
  exp = Seq(map(instr_to_exp, instrs))
  return regen(exp, init_env(), Trace(), Trace())

def doit(args):
  # type: (argparse.Namespace) -> None
  forms = ""
  if args.file:
    for fname in args.file:
      with open(fname) as f:
        forms += ""
        forms += f.read()
  if args.eval:
    forms += " ".join(args.eval)
  print toplevel(forms)

def main():
  # type: () -> None
  parser = argparse.ArgumentParser()
  parser.add_argument('-e', '--eval', action='append', help="execute the given expression")
  parser.add_argument('-f', '--file', action='append', help="execute the given file")
  args = parser.parse_args()
  doit(args)

if __name__ == '__main__':
  main()
