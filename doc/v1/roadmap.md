Venture v1 development milestones (as seen by Alexey):
- directives inside procedures (1st version: make a new trace -- "extend" rather than "splice")
- "mu": attach log densities to procedures by some method (there are a few generic methods)
- reflection on log density methods (presumably by combinator) (maybe also special mu-apply)
- do we want a special apply for apply-extend rather than apply-splice
    - Can do it with a combinator
    - apply-extend of a mu uses the log density to absorb; apply-splice absorbs inside the body
- At some point, will need AAA compounds
    - AAA does not appear to be good enough.  The relevant type of Gaussian Processes
      appears to be SP <hypers> <SP () <SP <test_index> <value>>>; for this to play
      sufficient statistics games, the maker wants to be able to track applications
      not of the made procedure, but of its outputs.
        - Might be hackable: if either simulate or incorporate of the nullary made SP
          registers the maker's aux with its output, the incorporate of that could
          maintain the maker's statistics.
    - It seems, in general, that AAA is the phenomenon that, when it
      comes to evaluating densities, a procedural value is exactly as
      good as the list of its applications.
    - Note: current AAA actually comes in three forms:
        - efficiently absorbing changes to a broadly used parameter
          (uncollapsed and not actually used anywhere; interface would be
          (make_coin weight) :: SP () -> Bool which absorbs changes to the
          weight at make_coin)
        - also Gibbs sampling that parameter if the prior is conjugate
          (this is make_uc_beta_bernoulli)
        - or collapsing the parameter out entirely if the prior is
          conjugate, and efficiently absorbing changes to the
          hyperparameters (this is make_beta_bernoulli)
