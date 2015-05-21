from venture.ripl import utils as u

def __venture_start__(ripl):
  ripl.bind_callback('pretty_print', pretty_print)
  ripl.bind_callback('newline', newline)

def pretty_print(_, s):
  print u.strip_types(s)[0]

def newline(_):
  print
  
