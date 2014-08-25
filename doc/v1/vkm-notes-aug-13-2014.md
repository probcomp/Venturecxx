Lightly error corrected and edited by Alexey, 8/14/2014

Hi Alexey,

I spent a couple hours revising our notes from yesterday and following
the consequences. There are a few *** and ??? s but I don't think
they're critical.

Can you look this over and tell me what you think --- about the
design, but also how it might inform next steps on an implementation?

Vikash

------

1. CORE TYPES:

- trace: parent, plus { address -> value }

- environment: parent, plus { symbol -> address }

- exp: list of symbols, traces, environments, "constants", exps

- procedure: formal-args (exp), body (exp), environment ref

- stochastic procedure: simulator proc, density proc, trace (***
  probably not, just marking; see discussion below)

- address: opaque

nb: NULL is a valid (empty) trace, environment, expression,
stochastic procedure and address.

nb: traces must make random choices, and record their results. traces
must store all *top-level* evals performed in them, in order, plus an
RNG seed and current state. (it might also be helpful for them to
store a link to the parent trace that generated each "top-level" eval;
this is the usual parent in case of extend.) if a trace just stores
its RNG seed and current state, then it must recompute everything to
return values. if it also stores a randomdb, it can look values up. if
it also stores a PET it can also efficiently find parents and
dependents. in some sense, inference could act over any of these
representations: a single unif[0,1]; separate random variables but no
dependencies, hence resimulation is required, yielding polynomial
slowdown but still "representing structure in the model and inference
problem" sufficient for inference to exploit it at least for the P vs
EXP distinction; and dependency tracking.

2. CORE FORMS & PRIMITIVES

  (eval <exp> <env> <trace> <addr>) => <val>

       - specializes to extend-eval and splice-eval; defaults to splice

       - addresses can be opaque

       - semantics: "eval the exp in the env, traced by the trace at
         addr".  If there is already a value at addr, just return it.

  (get-current-trace) => returns the trace in which the g-c-t proc was applied

  (peek <trace> <addr>) => return the value there, or sentinel if absent

  (poke <trace> <addr> <val>) => write a value into a trace (possibly
  with auxiliary data if tracking dependencies, etc).

  (extend-trace <trace>) => returns a new trace from which you can
  read the parent but not write to it. useful for hypotheticals.


  (get-current-environment) => returns the environment

  (bind! <env> <symbol> <addr>)

  (unbind! <env> <symbol>)

  (lookup <env> <symbol>)

  (extend-environment <optional: parent>)


  (lambda <formal-args> <body>) => generates a procedure, as usual

  (get-environment <proc>) => closed over environment

  (get-body <proc>) => body src as expression

  (get-formal-args <proc>) => formal args as expression


  (mu <simulator> <optional: density-evaluator (can be NULL for unknown)> <optional: trace; defaults to the symbol "current" ***>) => stochastic-procedure (which is a procedure, with application delegated to the simulator)

  (get-density <SP>) => proc

  (get-simulator <SP>) => proc

  (get-trace <SP>) => trace, or symbol "current" if the SP always
  applies itself in the caller's trace

  nb: there is a case analysis to consider:

    - if density is NULL and trace is NULL (ie guaranteed fresh
      randomness), the proc must be treated as likelihood free. The
      nodes in the PET can be tagged during evaluation with a NULL
      trace to help detect this. if density

    - if trace is the symbol "current", inference can either treat it
      as likelihood free or it can trace its internals (as with CSPs
      in cur Venture) and permit absorbing inside. ??? should we use
      tags to let users control this choice at the procedure level?

    - if density is provided, the procedure can additionally absorb
      around its whole application, in the *calling* trace (which need
      not be the trace in which the body is evaluated)

  *** if we choose to support other concrete values for trace, we can
      use traces as proper mutable storage, and may truly recover the
      behavior of latents and exchangeable coupling. there are also
      cases I haven't successfully thought through, such as what if
      the trace value changes (does everything need to be rerun?
      etc). It could be that this should be a spring POPL paper on a
      V1 extension.

  ??? requests (and dependent requests? a sublanguage?), exchangeable
  coupling, latents


3. ADDITIONAL PRIMITIVES FOR INFERENCE

- additional primitives for omegadb style inference:

  (mutate-trace! <trace> <addr> ...) => modifies the trace

  nb. could bake in undo-ability or let users write it


- particle style inference:

  (fork-trace <trace>) => returns a copy-on-write version of the input trace

  (commit-trace! <forked-trace>) => applies all its modifications to its source

4. HANDLING MODELING AND INFERENCE

This substrate is sufficient to implement (as macros) an interaction
system that imposes "discourse structure" on programs, and
simultaneously/as a side effect separates information about the goal
of a computation from information about the strategy by which the goal
will be accomplished:

  (assume <name> <exp>): 

    (let ((env (get-current-environment))
          (addr (fresh-address)))
      (eval <exp> env (get-current-trace) addr (get-current-read-traces))
      (bind! env <name> addr)
      ... save the directive ID and value ...)

  (observe <exp> <val>):

    (let ((env (get-current-environment))
          (obs_key ( ... get observe directive ID ... ))
          (addr (fresh-address))
          (val-addr (fresh-address)))
      (eval <exp> env (get-current-trace) addr)
      (bind! env obs_key addr)
      (eval '(quote val) env (get-current-trace) val-addr)
      (bind! env ( ... derive value key from obs_key ...) val-addr))


  (predict <exp>): same as observe but w/o saving the observed val


  (infer <prog> <optional: infer_trace; default: NULL>): 

  (eval
   `(<prog> ',(get-current-trace))
   (get-current-environment)
   ;; by default, using the NULL trace here, the inference program is
   ;; transient, and any random choices must be accounted for
   ;; elsewhere (e.g. in densities or in treating the enclosing
   ;; procedure as likelihood-free).
   infer_trace
   (fresh-address))

nb: if the trace is NULL, and no density is provided, then any
enclosing procedure must be likelihood-free.

nb: the trace in which inference takes place could get passed in as an
argument to an enclosing procedure, so that some (other) model can
make use of it. it would be interesting if you say (infer
(get-current-trace)) --- or even worse, (infer (if (flip)
(get-current-trace) (extend-trace NULL))) --- you will see some
strange behavior. In this situation an infinite loop feels
"right". But if you abide by certain conventions, you should get
results that behave like sensible arguments.

5. TAGS

Wrote this out as a sanity check, but this is probably safe to
ignore. Traces can track tags to define exportable names, etc, as
follows:

- tags are arbitrary values; addresses might only refer to random choices

- the base tag is "top", and may be maintained specially (so that deep
  tag structures don't impose runtime costs)

- { <tag> -> set of addresses } for those addresses where <tag> is the
  most specific tag

- { <tag> -> set of subtags } so that all subtags can be found

(with-tag <tag-exp> <target-exp>) => evaluates <target-exp> in the
current trace, adding the value of <tag-exp> to the tag structure at
the appropriate point

then the following procedure is sufficient to build a path language
(e.g. /*/foo/*/bar or perhaps even *gulp* structural regular
expressions):

(get-addresses <trace> <tag>)

(get-subtags <trace> <tag> (lambda (subtag) <body of predicate that filters subtags>))

??? worth adding a (barrier ...) to allow a module writer to
encapsulate? or otherwise stick permissions on tags?

6. DEFERRED ITEMS: a thread pool; most likely proper 'trace' closures;
relationship between traces and continuations.
