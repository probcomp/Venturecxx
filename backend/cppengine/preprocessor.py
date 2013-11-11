def preprocess(venture_input):
  if type(venture_input) != list:
    return LiteralPreprocessor(venture_input)
  elif len(venture_input) == 0:
    return ListPreprocessor(venture_input)
  
  procedure = venture_input[0]
  if procedure in sugars:
    return sugars[procedure](venture_input)
  else:
    return ListPreprocessor(venture_input)

class LiteralPreprocessor:
  def __init__(self, venture_input):
    self.value = venture_input
  
  def desugar(self):
    return self.value
  
  def resugar(self, location):
    if len(location) == 0:
      return location
    raise ResugarError("Invalid location")

class ListPreprocessor:
  def __init__(self, venture_input):
    self.args = map(preprocess, venture_input)
  
  def desugar(self):
    return map(callDesugar, self.args)
  
  def resugar(self, location):
    if len(location) == 0:
      return location
    return [location[0]] + self.args[location[0]-1].resugar(location[1:])

# resugar a dummy lambda expression
def resugarDummyLambda(location, exprPreprocessor):
  if len(location) == 0:
    return location
  
  index = location[0]
  if index == 0: # application of lambda -> body of expression
    return []
  elif index == 1: # 'lambda' -> body of expression
    return []
  elif index == 2: # '()' -> body of expression
    return []
  elif index == 3: # actual expression
    return exprPreprocessor.resugar(location[1:])
  raise ResugarError("Invalid location.")

class IfPreprocessor(ListPreprocessor):
  def __init__(self, venture_input):
    if len(venture_input) != 4:
      raise SyntaxError("'if' should have 3 arguments.")
    
    self.predicate = preprocess(venture_input[1])
    self.consequent = preprocess(venture_input[2])
    self.alternative = preprocess(venture_input[3])
  
  def desugar(self):
    lambda_for_consequent = ["lambda", [], self.consequent.desugar()]
    lambda_for_alternative = ["lambda", [], self.alternative.desugar()]
    
    return [["condition-ERP", self.predicate.desugar(), lambda_for_consequent, lambda_for_alternative]]
  
  def resugar(self, location):
    if len(location) == 0:
      return location
    elif len(location) == 1:
      if location[0] == 0: # outer application -> application of if
        return location
      elif location[0] == 1: # body of (condition-ERP ...) -> body of if
        return []
      raise ResugarError("Invalid location.")
    
    index = location[1]
    if index == 0: # application of (condition-ERP ...) -> application of if
      return location[1:]
    elif index == 1: # 'condition-ERP' -> 'if'
      return location[1:]
    elif index == 2: # predicate
      return [2] + self.predicate.desugar(location[2:])
    elif index == 3: # consequent
      return [3] + resugarDummyLambda(location[2:], self.consequent)
    elif index == 4: # alternative
      return [4] + resugarDummyLambda(location[2:], self.alternative)

class AndPreprocessor:
  def __init__(self, venture_input):
    if len(venture_input) != 3:
      raise SyntaxError("'and' should have 2 arguments.")
    
    venture_input.insert(3, "b<false>")
    self.ifPreprocessor = IfPreprocessor(venture_input)
  
  def desugar(self):
    return self.ifPreprocessor.desugar()
  
  def resugar(self, location):
    location = self.ifPreprocessor.resugar(location)
    if len(location) == 0:
      return location
    
    if location[0] == 4: # 'false' -> 'and'
      location[0] = 1
    
    return location

class OrPreprocessor:
  def __init__(self, venture_input):
    if len(venture_input) != 3:
      raise SyntaxError("'or' should have 2 arguments.")
    
    venture_input.insert(2, "b<true>")
    self.ifPreprocessor = IfPreprocessor(venture_input)
  
  def desugar(self):
    return self.ifPreprocessor.desugar()
  
  def resugar(self, location):
    location = self.ifPreprocessor.resugar(location)
    if len(location) == 0:
      return location
    
    if location[0] == 3: # 'true' -> 'or'
      location[0] = 1
    elif location[0] == 4: # alternative -> second argument of 'or'
      location[0] = 2
    
    return location

class LetPreprocessor:
  def __init__(self, venture_input):
    if len(venture_input) != 3:
      raise SyntaxError("'let' should have 2 arguments.")
    
    bindings = venture_input[1]
    if type(bindings) != list:
      raise SyntaxError("'let' bindings should be a list")
    
    variables = []
    definitions = []
    for assignment in bindings:
      if type(assignment) != list:
        raise SyntaxError("'let' assignment should be a list")
      if len(assignment) != 2:
        raise SyntaxError("'let' assignment should have 2 arguments.")
      variables.append(preprocess(assignment[0]))
      definitions.append(preprocess(assignment[1]))
    
    self.variables = variables
    self.definitions = definitions
    
    self.expression = preprocess(venture_input[2])
  
  def desugar(self):
    variables = map(callDesugar, self.variables)
    expression = self.expression.desugar()
    definitions = map(callDesugar, self.definitions)
    
    return [["lambda", variables, expression]] + definitions
  
  def resugar(self, location):
    if len(location) == 0:
      return location
    
    if location[0] == 0: # outer application -> application of let
      return [0]
    elif location[0] == 1:
      if len(location) == 1: # body of lambda -> body of let
        return []
      
      if location[1] == 0: # application of lambda -> application of let
        return [0]
      elif location[1] == 1: # 'lambda' -> 'let'
        return [1]
      elif location[1] == 2:
        if len(location) == 2: # body of lambda arguments -> body of assignments
          return [2]
        
        # actual location of a variable
        index = location[2]
        return [2, index, 1] + self.variables[index-1].resugar(location[3:])
      
      elif location[1] == 3: # expression
        return [3] + self.expression.resugar(location[2:])
        
    else: # definitions
      index = location[0]-2
      return [2, index+1, 2] + self.definitions[index].resugar(location[1:])

# dictionary of sugars
sugars = {'if' : IfPreprocessor, 'and' : AndPreprocessor, 'or' : OrPreprocessor, 'let' : LetPreprocessor}

# call desugar on a preprocessor
callDesugar = lambda preprocessor: preprocessor.desugar()

class ResugarError(Exception):
  def __init__(self, msg):
    self.msg = msg

def testIf():
  venture_input = ['if', 'a', ['and', 'b', 'c'], ['or', 'd', 'e']]
  preprocessor = preprocess(venture_input)
  print preprocessor.desugar()
  location = [1, 4, 3, 1, 4, 3]
  print preprocessor.resugar(location)

def testLet():
  venture_input = ['let', [['a', 'A'], ['b', 'B']], 'c']
  preprocessor = preprocess(venture_input)
  print preprocessor.desugar()
  location = [3]
  print preprocessor.resugar(location)

if __name__ == '__main__':
  testLet()

