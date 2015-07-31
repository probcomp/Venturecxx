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

  :rtype: <inference action>

  Repeatedly apply the given action, suppressing the returned values.
""",
"""(lambda (f iter)
  (if (<= iter 0)
      pass
      (do f (iterate f (- iter 1)))))"""],

["repeat",
"""\
.. function:: repeat(iterations : int, f : <inference action>)

  :rtype: <inference action>

  Repeatedly apply the given action, suppressing the returned values.
  This is the same as `iterate`, except for taking its arguments
  in the opposite order, as a convenience.
""",
"""(lambda (iter f) (iterate f iter))"""],

["sequence", """\
.. function:: sequence(ks : list<inference action returning a>)

  :rtype: <inference action returning list<a>>

  Apply the given list of actions in sequence, returning the values.
  This is Haskell's sequence.
""",
"""(lambda (ks)
  (if (is_pair ks)
      (do (v <- (first ks))
          (vs <- (sequence (rest ks)))
          (return (pair v vs)))
      (return nil)))"""],

["sequence_", """\
.. function:: sequence(ks : list<inference action>)

  :rtype: <inference action>

  Apply the given list of actions in sequence, discarding the values.
  This is Haskell's sequence\\_.
""",
"""(lambda (ks)
  (if (is_pair ks)
      (do (first ks)
          (sequence_ (rest ks)))
      pass))"""],

["mapM", """\
.. function:: mapM(act : proc(a) -> <inference action returning b>, objs : list<a>)

  :rtype: <inference action returning list<b>>

  Apply the given action function to each given object and perform
  those actions in order.  Return a list of the resulting values.  The
  nomenclature is borrowed from Haskell.
""",
 """(lambda (act objs)
  (sequence (to_list (mapv act (to_array objs)))))"""],

["imapM", """\
.. function:: imapM(act : proc(int, a) -> <inference action returning b>, objs : list<a>)

  :rtype: <inference action returning list<b>>

  Apply the given action function to each given object and its index
  in the list and perform those actions in order.  Return a list of
  the resulting values.
""",
 """(lambda (act objs)
  (sequence (to_list (imapv act (to_array objs)))))"""],

["for_each", """\
.. function:: for_each(objs : list<a>, act : proc(a) -> <inference action>)

  :rtype: <inference action>

  Apply the given action function to each given object and perform
  those actions in order.  Discard the results.
""",
 """(lambda (objs act)
  (sequence_ (to_list (mapv act (to_array objs)))))"""],

["for_each_indexed", """\
.. function:: for_each_indexed(objs : list<a>, act : proc(int, a) -> <inference action>)

  :rtype: <inference action>

  Apply the given action function to each given object and its index
  in the list and perform those actions in order.  Discard the
  results.
""",
 """(lambda (objs act)
  (sequence_ (to_list (imapv act (to_array objs)))))"""],

# pass :: State a ()  pass = return ()
["pass", """\
.. _pass:
.. object:: pass <inference action>

  An inference action that does nothing and returns nil.  Useful in
  the same sorts of situations as Python's ``pass`` statement.
""",
"(inference_action (lambda (t) (pair nil t)))"],

# bind :: State s a -> (a -> State s b) -> State s b
["bind", """\
.. function:: bind(<inference action returning a>, proc(a) -> <inference action returning b>)

  :rtype: <inference action returning b>

  Chain two inference actions sequentially, passing the value of the
  first into the procedure computing the second.  This is Haskell's
  ``bind``, specialized to inference actions.
""",
"""(lambda (act next)
 (inference_action
  (lambda (t)
    (let ((res ((action_func act) t)))
      ((action_func (next (first res))) (rest res))))))"""],

# bind_ :: State s b -> State s a -> State s a
# drop the value of type b but perform both actions
["bind_", """\
.. function:: bind_(<inference action>, proc() -> <inference action returning a>)

  :rtype: <inference action returning a>

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
 (inference_action
  (lambda (t)
    (let ((res ((action_func act) t)))
      ((action_func (next)) (rest res))))))"""],

# action :: b -> State a b
["action", """\
.. function:: action(<object>)

  :rtype: <inference action returning <object>>

  Wrap an object, usually a non-inference function like plotf,
  as an inference action, so it can be used inside a do(...) block.
""",
"""(lambda (val)
 (inference_action
  (lambda (t) (pair val t))))"""],

# return :: b -> State a b
["return", """\
.. function:: return(<object>)

  :rtype: <inference action returning <object>>

  An inference action that does nothing and just returns the argument
  passed to `return`.
""",
"""action"""],

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
.. _global_likelihood:
.. object:: global_likelihood <inference action returning <number>>

  An inference action that computes and returns the global likelihood
  (in log space).  Cost: O(size of trace).
""",
"(likelihood_at (quote default) (quote all))"],

["global_posterior", """\
.. _global_posterior:
.. object:: global_posterior <inference action returning <number>>

  An inference action that computes and returns the global posterior
  (in log space).  Cost: O(size of trace).
""",
"(posterior_at (quote default) (quote all))"],

["posterior", """\
.. _posterior:
.. object:: posterior <inference action>

  An inference action that sets each particle to an independent sample
  from the full posterior (with respect to currently incorporated
  observations).

  This is implemented by global rejection sampling (generalized to
  continuous equality constraints), so may take a while for problems
  where the posterior is far from the prior in KL divergence.

""",
"(rejection default all 1)"],

["join_datasets", """\
.. function:: join_datasets(datasets : list<dataset>)

  :rtype: <inference action returning <dataset>>

  Merge all the given datasets into one.
""",
"""\
(lambda (datasets)
  (let ((d (empty)))
    (do (for_each datasets
          (curry into d))
        (return d))))"""],

["accumulate_dataset", """\
.. function:: accumulate_dataset(iterations : int, a : <inference action returning <dataset>>)

  :rtype: <inference action returning <dataset>>

  Run the given inference action the given number of times,
  accumulating all the returned datasets into one.

  For example::

      accumulate_dataset(1000,
        do(default_markov_chain(10),
           collect(x)))

  will return a dataset consisting of the values of ``x`` that occur at
  10-step intervals in the history of a 10000-step default Markov
  chain on the current model.
""",
"""\
(lambda (count action)
  (let ((d (empty)))
    (do (repeat count
          (do (frame <- action)
              (into d frame)))
        (return d))))"""],

["reset_to_prior", """\
.. _reset_to_prior:
.. object:: reset_to_prior <inference action>

  Reset all particles to the prior.  Also reset their weights to the likelihood.

  This is equivalent to ``likelihood_weight()``.""",
"(likelihood_weight)"],

["run", """\
.. function:: run(<inference action returning a>)

  :rtype: a

  Run the given inference action and return its value.
""",
"""\
(lambda (action)
  (let ((result ((action_func action) __the_inferrer__)))
    (first result)))"""],

["autorun", """\
.. function:: autorun(<object>)

  :rtype: <object>

   If the argument is an inference action, run it and return the result.  Otherwise, return the argument.""",
"""\
(lambda (thing)
  (if (is_inference_action thing)
      (run thing)
      thing))"""],

["default_markov_chain", """\
.. function:: default_markov_chain(transitions : int)

  :rtype: <inference action>

  Take the requested number of steps of the default Markov chain.

  The default Markov chain is single-site resimulation M-H.

    default_markov_chain(k)

  is equivalent to

    mh(default, one, k)

  See `mh`.

""",
"(lambda (k) (mh default one k))"],

["regeneration_local_proposal", """\
.. function:: regeneration_local_proposal(<list>)

  :rtype: proc(<subproblem>) -> <inference action returning <result>>

  Propose the given values for the given subproblem.  Changes the
  underlying model to represent the proposed state, and returns a
  proposal result (see `mh_correct`).

""",
"""\
(lambda (values)
  (lambda (subproblem)
    (do (rho_weight_and_rho_db <- (detach_for_proposal subproblem))
        (xi_weight <- (regen_with_proposal subproblem values))
        (let ((rho_weight (first rho_weight_and_rho_db))
              (rho_db (rest rho_weight_and_rho_db)))
          (return
           (list (- xi_weight rho_weight)
                 pass                    ; accept
                 (do (detach subproblem) ; reject
                     (restore subproblem rho_db))))))))"""],

["mh_correct", """\
.. function:: mh_correct(<inference action returning <result>>)

  :rtype: <inference action>

  Run the given proposal, and accept or reject it according to the
  Metropolis-Hastings acceptance ratio returned in its result.

  The action must return a list of three items:

  - The local acceptance ratio (in log space)
  - An action to run to accept the proposal
  - An action to run to reject the proposal
""",
"""\
(lambda (proposal)
  (do (result <- proposal)
      (let ((weight (first result))
            (accept (second result))
            (reject (second (rest result))))
        (if (< (log (uniform_continuous 0 1)) weight)
            accept
            reject))))"""],

["symmetric_local_proposal", """\
.. function:: symmetric_local_proposal(proc(<value>) -> <value>)

  :rtype: proc(<subproblem>) -> <inference action returning <result>>

  Propose using the given kernel for the given subproblem.  Changes the
  underlying model to represent the proposed state, and returns a
  proposal result (see `mh_correct`).

  The kernel function must be symmetric, but need not be assessable.

""",
"""\
(lambda (kernel)
  (lambda (subproblem)
    (do (values <- (get_current_values subproblem))
        (let ((new_values (mapv kernel values)))
          ((regeneration_local_proposal new_values) subproblem)))))"""],

["on_subproblem", """\
.. function:: on_subproblem(scope: object, block: object, proposal: proc(<subproblem>) -> <inference action returning <result>>)

  :rtype: <inference action returning <result>>

  Select the subproblem indicated by the given scope and block, and
  apply the given proposal procedure to that subproblem.  Returns
  a proposal result (see `mh_correct`).

  The given proposal function must accept a subproblem and produce an
  action that returns a proposal result.  The result returned by
  `on_subproblem` consists of modifying the acceptance ratio to
  account for any change in the probability of selecting the same
  subproblem from the given scope and block.

""",
"""\
(lambda (scope block proposal)
  (do (subproblem <- (select scope block))
      (let ((rhoWeight 0 ; (assess subproblem select scope block)
                       ))
        (do (result <- (proposal subproblem))
            (let ((xiWeight 0 ; (assess subproblem select scope block)
                            )
                  (new_weight (+ xiWeight (first result) (- 0 rhoWeight))))
              (return (pair new_weight (rest result))))))))"""]

]
