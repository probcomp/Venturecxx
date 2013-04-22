#!/usr/bin/env python
# -*- coding: utf-8 -*- 


from venture.utils import app

def run_venture_console():
  ripl = engine
  while True:
    sys.stdout.write('>>> ')
    current_line = sys.stdin.readline()
    current_line = current_line.strip()
    if current_line[0] == "(":
      current_line = current_line[1:-1]
    if current_line[0] == "[":
      current_line = current_line[1:-1]
    current_line = current_line.split(" ", 1)
    directive_name = current_line[0].lower()
    sys.stdout.write('')
    try:
      if (directive_name == "assume"):
        name_and_expression = current_line[1].split(" ", 1)
        print ripl.assume(name_and_expression[0], parse_lisp(name_and_expression[1]))
      elif (directive_name == "predict"):
        name_and_expression = current_line[1].split(" ", 1)
        print ripl.predict(parse_lisp(current_line[1]))
      elif (directive_name == "observe"):
        expression_and_literal_value = current_line[1].rsplit(" ", 1)
        print ripl.observe(parse_lisp(expression_and_literal_value[0]), expression_and_literal_value[1])
      elif (directive_name == "infer"):
        ripl.infer(int(current_line[1]))
        print "The engine has made number of inference iterations: " + current_line[1]
      elif (directive_name == "forget"):
        ripl.forget(int(current_line[1]))
        print "You have forgotten the directive #" + current_line[1]
      elif (directive_name == "report"):
        print ripl.report_value(int(current_line[1]))
      elif (directive_name == "clear"):
        ripl.clear()
        print "The trace has been cleared."
      else:
        print "Sorry, unknown directive."
    except Exception, err:
      print "Your query has invoked an error: " + str(err)
