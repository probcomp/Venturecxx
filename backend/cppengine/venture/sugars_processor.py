
def process_sugars(venture_input):
  if type(venture_input) == list:
    if len(venture_input) == 0:
      return venture_input
    else:
      if venture_input[0] == "if":
        return process_if(venture_input)
      elif venture_input[0] == "or":
        return process_or(venture_input)
      elif venture_input[0] == "and":
        return process_and(venture_input)
      elif venture_input[0] == "let":
        return process_let(venture_input)
      elif venture_input[0] == "let*":
        return process_let_star(venture_input)
      else:
        return venture_input
  else:
    return venture_input

# (if predicate consequent alternative) is sugar for
# ( (condition-ERP predicate (lambda () consequent) (lambda () alternative)) )
def process_if(venture_input):
  #if len(venture_input) == 3:
  #  venture_input[3] = False
    
  if len(venture_input) == 4:
    predicate = venture_input[1]
    consequent = venture_input[2]
    alternative = venture_input[3]
    lambda_for_consequent = ["lambda", [], consequent]
    lambda_for_alternative = ["lambda", [], alternative]
    return [ ["condition-ERP", predicate, lambda_for_consequent, lambda_for_alternative] ]
  else:
    raise SyntaxError("'if' should have 3 arguments.")

def process_and(venture_input):
  if len(venture_input) != 3:
    raise SyntaxError("'and' should have 2 arguments.")
  return process_if(["if", venture_input[1], venture_input[2], False])

def process_or(venture_input):
  if len(venture_input) != 3:
    raise SyntaxError("'or' should have 2 arguments.")
  return process_if(["if", venture_input[1], True, venture_input[2]])

def process_let(venture_input):
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
    variables.append(assignment[0])
    definitions.append(assignment[1])
  
  desugar = [ ["lambda", variables, venture_input[2]] ]
  desugar.extend(definitions)
  return desugar

def process_let_star(venture_input):
  if len(venture_input) != 3:
    raise SyntaxError("'let*' should have 3 arguments.")
  
  bindings = venture_input[1]
  if type(bindings) != list:
    raise SyntaxError("'let*' bindings should be a list")
  
  if len(bindings) == 0:
    return venture_input[2]
  
  assignment = bindings.pop(0)
  if type(assignment) != list:
    raise SyntaxError("'let*' assignment should be a list")
  if len(assignment) != 2:
    raise SyntaxError("'let*' assignment should have 2 arguments.")
  
  return [["lambda", [assignment[0]], process_let_star(venture_input)], assignment[1]]
