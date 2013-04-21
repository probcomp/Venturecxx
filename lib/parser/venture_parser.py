#!/usr/bin/env python
# -*- coding: utf-8 -*- 

__all__ = ['ParseException','BaseParser']

class ParseException(Exception):
  def __init__(self, lineno, col, message):
    self.lineno = lineno
    self.col = col
    self.message = message
  def __str__(self):
    return "ParseException line: {} col: {}. {}".format(
            self.lineno, self.col, self.message)
  def __unicode__(self):
    return self.__str__()
  def __repr__(self):
    return self.__str__()

class BaseParser():
  def process_sugars(venture_input):
    if type(venture_input) == list:
      if len(venture_input) == 0:
        return venture_input
      else:
        # "and" is implemented as in Clojure (FIXME: and is how in Scheme?)
        if venture_input[0] == "and":
          if len(venture_input) == 1:
            return True
          elif len(venture_input) == 2:
            return venture_input[1]
          else:
            current_element = venture_input[1]
            del venture_input[1]
            return process_sugars(["if", current_element, process_sugars(venture_input), False])
        # "or" is implemented almost as in Clojure (FIXME: and is how in Scheme?)
        elif venture_input[0] == "or":
          if len(venture_input) == 1:
            return False
          elif len(venture_input) == 2:
            return venture_input[1]
          else:
            current_element = venture_input[1]
            del venture_input[1]
            return process_sugars(["if", current_element, True, process_sugars(venture_input)])
        # (if predicate consequent alternative) is sugar for
        # ( (condition-ERP predicate (lambda () consequent) (lambda () alternative)) )
        elif venture_input[0] == "if":
          if len(venture_input) == 3:
            venture_input[3] = False
            
          if len(venture_input) == 4:
            predicate = venture_input[1]
            consequent = venture_input[2]
            alternative = venture_input[3]
            lambda_for_consequent = ["lambda", [], consequent]
            lambda_for_alternative = ["lambda", [], alternative]
            return [ ["condition-ERP", predicate, lambda_for_consequent, lambda_for_alternative] ]
          else:
            raise SyntaxError("'if' should have 3 or 4 arguments.")
        else:
          return venture_input
    else:
      return venture_input

  def parse_expression(self, s):
    """
    To be implemented by subclasses
    Returns the expression represented by the string s.
    Output is a nested python-list -- not desugared.
    Throws a ParseException in case of failure.
    """
    raise NotImplemented()

  def process_expression(self, s):
    """
    Parses an expression and desugars it.
    """
    self.process_sugars(self.parse(s))

  def parse_program(self, s):
    """
    To be implemented by subclasses.
    Parses the program in the string s. Output is a
    nested python-list where the outer level corresponds
    to Venture directives. Output is not desugared.
    Throws a ParseException in case of failure.
    """
    raise NotImplemented()

  def execute_program(self, s, engine):
    """
    Parses a program and executes it against the engine.
    Returns a list of return values.
    """
    directives = self.parse_program(s)
    return [engine.execute_directive(x) for x in directives]
