# A list of lists: name, description, code
prelude = [
  ["cycle", """(lambda (ks iter)
    (iterate (sequence ks) iter))"""],
  # Repeatedly apply the given action, discarding the values
  ["iterate", """(lambda (f iter)
    (if (<= iter 1)
        f
        (lambda (t) (f (rest ((iterate f (- iter 1)) t))))))"""],
  # Apply the given list of actions in sequence, discarding the values.
  # This is Haskell's sequence_
  ["sequence", """(lambda (ks)
    (if (is_pair ks)
        (lambda (t) ((sequence (rest ks)) (rest ((first ks) t))))
        (lambda (t) (pair nil t))))"""],
  ["begin", "sequence"],
  ["mixture", """(lambda (weights kernels transitions)
    (iterate (lambda (t) ((categorical weights kernels) t)) transitions))"""],
  # pass :: State a ()  pass = return ()
  ["pass", "(lambda (t) (pair nil t))"],
  # bind :: State a b -> (b -> State a c) -> State a c
  ["bind", """(lambda (act next)
    (lambda (t)
      (let ((res (act t)))
        ((next (first res)) (rest res)))))"""],
  # bind_ :: State a b -> State a c -> State a c
  # drop the value of type b but perform both actions
  ["bind_", """(lambda (act next)
    (lambda (t)
      (let ((res (act t)))
        ((next) (rest res)))))"""],
  # return :: b -> State a b
  ["return", """(lambda (val) (lambda (t) (pair val t)))"""],
  ["curry", """(lambda (f arg) (lambda (arg2) (f arg arg2)))"""],
  ["curry3", """(lambda (f arg1 arg2) (lambda (arg3) (f arg1 arg2 arg3)))"""],
  ["global_likelihood", "(likelihood_at (quote default) (quote all))"],
  ["global_posterior", "(posterior_at (quote default) (quote all))"],
  ]
