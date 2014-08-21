def assert_almost_equal(first, second, places=None, msg=None, delta=None):
  '''Like nose assert_almost_equal, but for Venture numbers'''
  if first == second:
      # shortcut
      return
  if delta is not None and places is not None:
      raise TypeError("specify delta or places not both")

  if delta is not None:
      if abs(first - second).getNumber() <= delta:
          return

      standardMsg = '%s != %s within %s delta' % (display_venture_number(first),
                                                  display_venture_number(second),
                                                  repr(delta))
  else:
      if places is None:
          places = 7

      if round(abs(second-first).getNumber(), places) == 0:
          return

      standardMsg = '%s != %s within %r places' % (display_venture_number(first),
                                                   display_venture_number(second),
                                                   places)
  if msg is None: msg = standardMsg
  raise AssertionError(msg)

def display_venture_number(number):
  return repr(number.getNumber())