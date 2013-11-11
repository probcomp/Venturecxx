def sample(ripl, expression):
  (directive_id, value) = ripl.predict(expression)
  ripl.forget(directive_id)
  return value

def force(ripl, expression, literal_value):
  directive_id = ripl.observe(expression, literal_value)
  ripl.forget(directive_id)
  return True

def load_to_RIPL(ripl, generative_model_string): # Jay Baxter, March 04 2013
    import re
    """Convert a Church generative model string into a sequence of Venture directives."""
    lines = re.findall(r'\[(.*?)\]', generative_model_string, re.DOTALL)
    directives_ids = []
    for line in lines:
        arguments = line.split(" ", 1)
        directive_name = arguments[0].lower()
        if (directive_name == "assume"):
          name_and_expression = arguments[1].split(" ", 1)
          (directive_id, _) = ripl.assume(name_and_expression[0], name_and_expression[1])
          directives_ids += [directive_id]
        elif (directive_name == "predict"):
          name_and_expression = arguments[1].split(" ", 1)
          (directive_id, _) = ripl.predict(arguments[1])
          directives_ids += [directive_id]
        elif (directive_name == "observe"):
          expression_and_literal_value = arguments[1].rsplit(" ", 1)
          directive_id = ripl.observe(expression_and_literal_value[0], expression_and_literal_value[1])
          directives_ids += [directive_id]
        elif (directive_name == "infer"):
          ripl.infer(int(arguments[1]))
        elif (directive_name == "forget"):
          ripl.forget(int(arguments[1]))
        elif (directive_name == "report"):
          ripl.report_value(int(arguments[1]))
        elif (directive_name == "clear"):
          ripl.clear()
        else:
          raise Exception("Unknown directive")
    return {"directive_ids": directives_ids}

def get_log_probability(ripl, expression, literal_value):
  before_logscore = ripl.logscore()
  directive_id = ripl.observe(expression, literal_value)
  new_logscore = ripl.logscore()
  logscore = new_logscore - before_logscore
  ripl.forget(directive_id)
  return logscore
