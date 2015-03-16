from venture.exception import VentureException
from macro_system import Macro, Syntax, isSym, getSym, expand

def traverse(exp):
  if isinstance(exp, list):
    for i, e in enumerate(exp):
      for j, f in traverse(e):
        yield [i] + j, f
  else: yield [], exp

def bind(pattern, exp):
  if isinstance(pattern, list):
    bindings = {}
    for i, p in enumerate(pattern):
      bindings.update(bind(p, exp[i]))
    return bindings
  return {pattern: exp}

def sub(bindings, template):
  if isinstance(template, list):
    return [sub(bindings, t) for t in template]
  if isSym(template) and template in bindings:
    return bindings[template]
  return template

def verify(pattern, exp, context):
  """Verifies that the given expression matches the pattern in form."""
  if isinstance(pattern, list):
    if not isinstance(exp, list):
      raise VentureException('parse',
        'Invalid expression in %s -- expected list!' % (context,),
        expression_index=[])
    if len(exp) != len(pattern):
      raise VentureException('parse',
        'Invalid expression in %s -- expected length %d' %
          (context, len(pattern)),
        expression_index=[])
    for index, (p, e) in enumerate(zip(pattern, exp)):
      try:
        verify(p, e, context)
      except VentureException as err:
        err.data['expression_index'].insert(0, index)
        raise

class SyntaxRule(Macro):
  """A poor man's version of Scheme's syntax-rules pattern language for defining macros.

Does not support:
- literal tokens in patterns
- multiple alternate pattern-template pairs for the same macro
- pattern repetition notation (the ellipses "..." that novice
  syntax-rules users find so wonderfully confusing)
- hygiene (operates on expressions with symbols, which are eventually
  interpreted in the macro use site environment)

What's left?
- Patterns are (nested) lists of symbols.
  - pattern[0] must be a symbol and is taken to be the name of the
    macro
  - all other pattern symbols bind the corresponding code fragments at
    the use site
- Templates are nested lists of symbols.
- The output is the template, except that symbols bound in the pattern
  are replaced by those code fragments from the use site (symbols that
  are not bound are inserted as is).

  """
  def __init__(self, pattern, template, desc=None):
    self.name = pattern[0]
    self.pattern = pattern
    self.template = template
    self.desc = desc
    
    patternIndeces = {sym: index for index, sym in traverse(pattern) if isSym(sym)}
    templateIndeces = {sym: index for index, sym in traverse(template) if isSym(sym)}
    
    self.desugar = lambda index: replace(pattern, templateIndeces, index)
    self.resugar = lambda index: replace(template, patternIndeces, index)
    
  def applies(self, exp):
    return isinstance(exp, list) and len(exp) > 0 and getSym(exp[0]) == self.name
  
  def expand(self, exp):
    verify(self.pattern, exp, self.pattern[0])
    try:
      bindings = bind(self.pattern, exp)
      subbed = sub(bindings, self.template)
      expanded = expand(subbed)
      return SubSyntax(expanded, self.desugar, self.resugar)
    except VentureException as e:
      e.data['expression_index'] = self.resugar(e.data['expression_index'])
      raise

def replace(exp, indexMap, index):
  i = 0
  while isinstance(exp, list):
    if i == len(index):
      return []
    exp = exp[index[i]]
    i += 1
  
  if isSym(exp) and exp in indexMap:
    return indexMap[exp] + index[i:]
  
  return []

class SubSyntax(Syntax):
  def __init__(self, syntax, desugar, resugar):
    self.syntax = syntax
    self.desugar = desugar
    self.resugar = resugar
  def desugared(self):
    return self.syntax.desugared()
  def desugar_index(self, index):
    index = self.desugar(index)
    return self.syntax.desugar_index(index)
  def resugar_index(self, index):
    index = self.syntax.resugar_index(index)
    return self.resugar(index)

