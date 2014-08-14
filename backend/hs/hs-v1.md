Design Notes for HS-V1
======================

From Alexey's point of view.  This document is somewhat stream-of-consciousness.

There is a node graph, intermediated by Addresses

Let there be a TraceView, which holds sufficient information to
execute inference against
- map from Addresses to Nodes
- index of scopes, blocks, random choices
- I seem to need a notion of node ownership, which determines which
  TraceViews need to be updated in order to update a Node
    - Generativity can be enforced by permitting inference to update
      only the one TraceView on which it is operating.
        - Recursive nested TraceViews via LSRs may work
- A "body" has an associated TraceView, a lexical environment, and
  means of extending them by excecuting directives: assume, observe,
  predict.  Maybe a body has a second namespace for the names of the
  directives.
- Executing an infer directive in a body calls for
    - Starting an inherited TraceView that can access everything in
      the lexical environment of the infer by reference for running
      the inference program
    - Passing a reification of the TraceView being operated on to said
      inference program
    - Updating the TraceView store with the returned result (this way,
      inference can only modify its own TraceViews)
- extend-applying a procedure in a TraceView calls for
    - Starting a new inherited TraceView for the body that can access
      everything in the lexical environment of the closure by reference
    - Running the body in it
    - The body should look like an opaque family, possibly with
      requests; where does the body's TraceView get stored?  Anywhere?
- Starting a TraceView inherited from an enclosing TraceView is just
  creating a new empty frame; the lookup procedure can be adjusted
  to return non-modifiable views on nodes if it needs to cross a
  TraceView frame boundary.

Issues:
- Q: Can procedures be exchangeably coupled across TraceViews?
- A: Why not?
- Q: How does a TraceView call a procedure found in an enclosing
     environment?  Splice?  Extend?  Request?
- A: Maybe it can just choose any of the above
- A node in a TraceView can have children in enclosed TraceViews
    - These children can even be deterministic!
    - For extend-apply, this means that the application node must
      depend on all (referenced) nodes from the environment, and
      either absorb or resample based on the feelings of the interior.
        - Actually, the interior cannot have any feelings on this point,
          can it?  That's only splice.  Absorbing is possible only if
          that procedure is supplied separately.
        - Though there may be a hybrid notion of "absorb after changing
          some internal state", but again, the absorb should be the
          weight of the whole compound, not just the part in it that hit.
        - There may also be a hybrid notion of extend where the leak
          prevention is only applied in one direction: the enclosed
          TraceView is transparent to inference on the enclosing one,
          but not vice versa.  When does one rerun enclosed inference
          programs, then?
        - Another possible solution would be to throw away the enclosed
          TraceView after the body returns.  Then that procedure will
          not be able to absorb recursively (which it actually can't
          anyway), and resample only from the beginning (which is
          presumably the right thing anyway).
    - Do the TraceViews used to run inference programs persist after
      the inference program returns?  If not, then inference on the
      enclosing scope can only rerun the inference program, not muck
      with it, so there need not be any child problem.
- What happens when an extend-applied procedure returns a closure?
    - Conservative answer: the environment of that closure is
      read-only, even to inference over that closure's applications
      (auxes are probably orthogonal)
    - If the maker is resampled, a new made SP appears, etc.
- If we are going down the path of syntax, I don't actually need
  extend-apply -- just extend.  Create a new TraceView, keep the
  lexical environment, and take it from there.
- Idea: Do we want quasi-extend and unextend, by analogy to
  quasiquote and unquote?  This feels like a convenience that should
  just macroexpand into particular patterns of let bindings lifted
  out of regular extends, but might nonetheless make Venture v1
  considerably easier to program in.  Or might not.

Ha!  Env in HsVenture doesn't actually need frames, because the
persistence of the map data structure does the right thing anyway!
- Frames get persistence by paying linear time in the depth of
  histories; proper persistent trees just have a log everywhere.

Code review questions
---------------------

- How can I get the randomness monad not to pollute my type signatures
  all over the place?  Do I even want to?
- Can I extend zoom to operate on the Coroutine monad transformer?
  How do I do that?
- What functions should I tag {-# INLINE #-}?  If a third-party
  library has a function I want to tag inline but its author didn't,
  can I monkey-patch it?  How?
- Does all the hair with Uniques make sense, and does it compile away?
- What's the difference between random-fu and statistics?  Which
  should one use under what circumstances?
    - What's with all the Vectors?
