Deep Freezing
-------------

May 25, 2015.

It is tempting to be able to freeze the results of memoized
procedures, for example to be able to write a particle filter for a
model where the transition function is in memmed style (rather than as
a programmatically controlled series of assume commands).

It is tempting to approach this by allowing freeze to go deep in
general -- namely, to define it to operate on the top random choice of
the target directive rather than the top node of the directive
(whether it be a random choice or no).
- The implementation would be 
  node = self.getOutermostNonReferenceNode(self.families[id])

Unfortunately, this doesn't work, because the static representation
maintained by engine.trace.Trace gets out of sync with the resulting
actual trace.  This phenomenon is, in fact, inevitable, because the
result of a general deep freeze does not admit a static representation
at all -- one might freeze the body of a compound SP at one use site
but not others; and one might find oneself freezing conditionally on
the data flow of first-class compound procedures.

Now, it is theoretically possible to define a somewhat more restricted
class of freezeable nodes, as follows:
- Toplevel directives are freezable
- Applications of freezable memoized procedures to constant arguments
  are freezable

Implementing this calls for an additional representational element for
memoized procedures, namely an external list of the values at which
they have been frozen.
- When reconstructing traces, these frozen values must be taken into
  account before any uses of said procedures (e.g., to forestall
  undesired recursion).
  - Said account must not actually call the procedure, as that would
    defeat the purpose; it must directly add a binding to the mem
    table (and take into account that this binding did not come from
    a materialized invocation of the memmed SP).
- In order to actually get correct particle filter asymptotics out of
  this method, it is necessary to be able to forget such freezings,
  effectively unfreezing those applications.

As an alternative, it should be possible to use a general redefine to
get the desired particle filter behavior for memmed recursions:
  [reassume state (mem (lambda (timestep)
    (if (< timestep ,now)
        ,current-value
        (transition (state (- timestep 1))))))]
Not sure whether this is actually clearer than writing the program in
programmatic-assumes style in the first place.
