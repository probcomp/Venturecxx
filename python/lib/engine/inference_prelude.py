# Copyright (c) 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

# A list of lists: name, description, code
prelude = [
["iterate",
"""\
.. function:: iterate(f : <inference action>, iterations : int)

  :rtype: proc(<foreignblob>) -> <pair () <foreignblob>>

  Repeatedly apply the given action, suppressing the returned vaues.
""",
"""(lambda (f iter)
  (if (<= iter 0)
      pass
      (lambda (t) (f (rest ((iterate f (- iter 1)) t))))))"""],

["repeat",
"""\
.. function:: repeat(iterations : int, f : <inference action returning a>)

  :rtype: proc(<foreignblob>) -> <pair a <foreignblob>>

  Repeatedly apply the given action, returning the last value.
  This is the same as ``iterate``, except for taking its arguments
  in the opposite order, as a convenience.
""",
"""(lambda (iter f) (iterate f iter))"""],

["sequence", """\
.. function:: sequence(ks : list<inference action>)

  :rtype: proc(<foreignblob>) -> <pair () <foreignblob>>

  Apply the given list of actions in sequence, discarding the values.
  This is Haskell's sequence\\_.
""",
"""(lambda (ks)
  (if (is_pair ks)
      (lambda (t) ((sequence (rest ks)) (rest ((first ks) t))))
      (lambda (t) (pair nil t))))"""],

["mapM", """\
.. function:: mapM(act : proc(a) -> <inference action returning b>, objs : list<a>)

  :rtype: proc(<foreignblob>) -> <pair list<b> <foreignblob>>

  Apply the given action function to each given object and perform
  those actions in order.  Return a list of the resulting values.  The
  nomenclature is borrowed from Haskell.
""",
 """(lambda (act objs)
  (if (is_pair objs)
      (do (v <- (act (first objs)))
          (vs <- (mapM act (rest objs)))
          (return (pair v vs)))
      (return nil)))"""],

["for_each_indexed", """\
.. function:: for_each_indexed(act : proc(int, a) -> <inference action>, objs : list<a>)

  :rtype: proc(<foreignblob>) -> <pair () <foreignblob>>

  Apply the given action function to each given object and its index
  in the list and perform those actions in order.  Discard the
  results.  The nomenclature is borrowed from Scheme.
""",
 """(lambda (act objs)
  (sequence (to_list (imapv act (to_array objs)))))"""],

# pass :: State a ()  pass = return ()
["pass", """\
.. function:: pass(<foreignblob>)

  :rtype: <pair () <foreignblob>>

  An inference action that does nothing and returns nil.  Useful in
  the same sorts of situations as Python's ``pass`` statement.
""",
"(lambda (t) (pair nil t))"],

# bind :: State s a -> (a -> State s b) -> State s b
["bind", """\
.. function:: bind(<inference action returning a>, proc(a) -> <inference action returning b>)

  :rtype: proc(<foreignblob>) -> <pair b <foreignblob>>

  Chain two inference actions sequentially, passing the value of the
  first into the procedure computing the second.  This is Haskell's
  ``bind``, specialized to inference actions.
""",
"""(lambda (act next)
  (lambda (t)
    (let ((res (act t)))
      ((next (first res)) (rest res)))))"""],

# bind_ :: State s b -> State s a -> State s a
# drop the value of type b but perform both actions
["bind_", """\
.. function:: bind_(<inference action>, proc() -> <inference action returning a>)

  :rtype: proc(<foreignblob>) -> <pair a <foreignblob>>

  Chain two inference actions sequentially, ignoring the value of the
  first.  This is Haskell's ``>>`` operator, specialized to inference
  actions.

  Note that the second argument is a thunk that computes an inference
  action.  This is important, because it defers computing the action
  to take until it is actually time to take it, preventing infinite
  loops in, e.g., unrolling the future action spaces of recursive
  procedures.
""",
"""(lambda (act next)
  (lambda (t)
    (let ((res (act t)))
      ((next) (rest res)))))"""],

# return :: b -> State a b
["return", """\
.. function:: return(<object>)

  :rtype: proc(<foreignblob>) -> <pair <object> <foreignblob>>

  An inference action that does nothing and just returns the argument
  passed to ``return``.
""",
"""(lambda (val) (lambda (t) (pair val t)))"""],

["curry", """\
.. function:: curry(proc(<a>, <b>) -> <c>, <a>)

  :rtype: proc(<b>) -> <c>

  Curry a two-argument function into two one-argument stages.
  Supports the idiom (bind (collect ...) (curry plotf (quote spec))).
""",
"""(lambda (f arg) (lambda (arg2) (f arg arg2)))"""],

["curry3", """\
.. function:: curry3(proc(<a>, <b>, <c>) -> <d>, <a>, <b>)

  :rtype: proc(<c>) -> <d>

  Curry a three-argument function into a two-argument stage and a
  one-argument stage.  Supports the idiom (bind (collect ...) (curry
  plotf_to_file (quote name) (quote spec))).
""",
"""(lambda (f arg1 arg2) (lambda (arg3) (f arg1 arg2 arg3)))"""],

["global_likelihood", """\
.. function:: global_likelihood(<foreignblob>)

  :rtype: <pair <number> <foreignblob>>

  An inference action that computes and returns the global likelihood
  (in log space).  Cost: O(size of trace).
""",
"(likelihood_at (quote default) (quote all))"],

["global_posterior", """\
.. function:: global_posterior(<foreignblob>)

  :rtype: <pair <number> <foreignblob>>

  An inference action that computes and returns the global posterior
  (in log space).  Cost: O(size of trace).
""",
"(posterior_at (quote default) (quote all))"],
]
