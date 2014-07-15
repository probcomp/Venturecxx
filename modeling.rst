Modeling Syntax Reference (VenChurch)
=====================================

Introduction
------------

The Venture modeling language is the language in which model
expressions, namely the arguments to the `assume`, `observe`, and
`predict` instructions are written.  The Venture inference language is
the same language, but with a few additional predefined names,
procedures, and special forms.

The VenChurch surface syntax for the Venture modeling language is a
pure-functional dialect of Scheme, which puts it in the Lisp family of
programming languages.  The major differences from Scheme are

- No mutation (only inference can effect mutation, and that only in a
  restricted way)

- A spare set of predefined procedures and special forms

- Predefined procedures for random choices according to various
  distributions.

Special Forms
-------------

The special forms in VenChurch are as follows:

- `(lambda (param ...) body)`: Construct a procedure.

  The formal parameters must be Venture symbols.
  The body must be a Venture expression.
  The semantics are as in Scheme or Church.  Unlike Scheme, the body
  must be a single expression, and creation of variable arity
  procedures is not supported.

- `(if predicate consequent alternate)`: Branch control.

  The predicate, consequent, and alternate must be Venture expressions.

- `(and exp1 exp2)`: Short-circuiting and.

- `(or exp1 exp2)`: Short-circuiting or.

- `(let ((param exp) ...) body)`: Evaluation with local scope.

  Each parameter must be a Venture symbol.
  Each exp must be a Venture expression.
  The body must be a Venture expression.
  The semantics are as Scheme's `let*`: each `exp` is evaluated in turn,
  its result is bound to the `param`, and made available to subsequent
  `exp` s and the `body`.

- `(quote datum)`: Literal data.

  The datum must be a Venture expression.
  As in Scheme, a `quote` form returns a representation of the given
  expression as Venture data structures.

Built-in Procedures
-------------------

You can see what built-in procedures Venture supports by running
``script/list-sps`` in the distribution.  The output of that script is
replicated here for convenience (please pardon the formatting)::

    + :: <SP <number> ... -> <number>>
    + returns the sum of all its arguments
      Deterministic

    - :: <SP <number> <number> -> <number>>
    - returns the difference between its first and second arguments
      Deterministic

    * :: <SP <number> ... -> <number>>
    * returns the product of all its arguments
      Deterministic

    / :: <SP <number> <number> -> <number>>
    / returns the quotient of its first argument by its second
      Deterministic

    eq :: <SP <object> <object> -> <bool>>
    eq compares its two arguments for equality
      Deterministic

    > :: <SP <object> <object> -> <bool>>
    > returns true if its first argument compares greater than its second
      Deterministic

    >= :: <SP <object> <object> -> <bool>>
    >= returns true if its first argument compares greater than or equal
    to its second
      Deterministic

    < :: <SP <object> <object> -> <bool>>
    < returns true if its first argument compares less than its second
      Deterministic

    <= :: <SP <object> <object> -> <bool>>
    <= returns true if its first argument compares less than or equal to
    its second
      Deterministic

    real :: <SP <atom> -> <number>>
    real returns the identity of its argument atom as a number
      Deterministic

    atom_eq :: <SP <atom> <atom> -> <bool>>
    atom_eq tests its two arguments, which must be atoms, for equality
      Deterministic

    probability :: <SP <probability> -> <probability>>
    probability converts its argument to a probability (in direct space)
      Deterministic

    sin :: <SP <number> -> <number>>
    Returns the sin of its argument
      Deterministic

    cos :: <SP <number> -> <number>>
    Returns the cos of its argument
      Deterministic

    tan :: <SP <number> -> <number>>
    Returns the tan of its argument
      Deterministic

    hypot :: <SP <number> <number> -> <number>>
    Returns the hypot of its arguments
      Deterministic

    exp :: <SP <number> -> <number>>
    Returns the exp of its argument
      Deterministic

    log :: <SP <number> -> <number>>
    Returns the log of its argument
      Deterministic

    pow :: <SP <number> <number> -> <number>>
    pow returns its first argument raised to the power of its second
    argument
      Deterministic

    sqrt :: <SP <number> -> <number>>
    Returns the sqrt of its argument
      Deterministic

    not :: <SP <bool> -> <bool>>
    not returns the logical negation of its argument
      Deterministic

    is_symbol :: <SP <object> -> <bool>>
    is_symbol returns true iff its argument is a <symbol>
      Deterministic

    is_atom :: <SP <object> -> <bool>>
    is_atom returns true iff its argument is a <atom>
      Deterministic

    list :: <SP <object> ... -> <list>>
    list returns the list of its arguments
      Deterministic

    pair :: <SP <object> <object> -> <pair>>
    pair returns the pair whose first component is the first argument and
    whose second component is the second argument
      Deterministic

    is_pair :: <SP <object> -> <bool>>
    is_pair returns true iff its argument is a <pair>
      Deterministic

    first :: <SP <pair> -> <object>>
    first returns the first component of its argument pair
      Deterministic

    rest :: <SP <pair> -> <object>>
    rest returns the second component of its argument pair
      Deterministic

    second :: <SP <pair <object> <pair>> -> <object>>
    second returns the first component of the second component of its
    argument
      Deterministic

    array :: <SP <object> ... -> <array>>
    array returns an array initialized with its arguments
      Deterministic

    vector :: <SP <number> ... -> <array <number>>>
    vector returns an unboxed numeric array initialized with its arguments
      Deterministic

    is_array :: <SP <object> -> <bool>>
    is_array returns true iff its argument is a <array>
      Deterministic

    dict :: <SP <list k> <list v> -> <dict k v>>
    dict returns the dictionary mapping the given keys to their respective
    given values.  It is an error if the given lists are not the same
    length.
      Deterministic

    is_dict :: <SP <object> -> <bool>>
    is_dict returns true iff its argument is a <dict>
      Deterministic

    matrix :: <SP <list <list <number>>> -> <matrix>>
    matrix returns a matrix formed from the given list of rows.  It is an
    error if the given list is not rectangular.
      Deterministic

    is_matrix :: <SP <object> -> <bool>>
    is_matrix returns true iff its argument is a <matrix>
      Deterministic

    simplex :: <SP <probability> ... -> <simplex>>
    simplex returns the simplex point given by its argument coordinates.
      Deterministic

    is_simplex :: <SP <object> -> <bool>>
    is_simplex returns true iff its argument is a <simplex>
      Deterministic

    lookup :: <SP <mapping k v> k -> v>
    lookup looks the given key up in the given mapping and returns the
    result.  It is an error if the key is not in the mapping.  Lists and
    arrays are viewed as mappings from indices to the corresponding
    elements.  Environments are viewed as mappings from symbols to their
    values.
      Deterministic

    contains :: <SP <mapping k v> k -> <bool>>
    contains reports whether the given key appears in the given mapping or
    not.
      Deterministic

    size :: <SP <mapping k v> -> <number>>
    size returns the number of elements in the given collection (lists and
    arrays work too)
      Deterministic

    branch :: <SP <bool> <exp> <exp> -> <object>>
    branch evaluates either exp1 or exp2 in the current environment and
    returns the result.  Is itself deterministic, but the chosen
    expression may involve a stochastic computation.
      Deterministic

    biplex :: <SP <bool> <object> <object> -> <object>>
    biplex returns either its second or third argument.
      Deterministic

    make_csp :: <SP <array <symbol>> <exp> -> a compound SP>
    make_csp
      Used internally in the implementation of compound procedures.
      Deterministic

    get_current_environment :: <SP  -> <environment>>
    get_current_environment returns the lexical environment of its
    invocation site
      Deterministic

    get_empty_environment :: <SP  -> <environment>>
    get_empty_environment returns the empty environment
      Deterministic

    is_environment :: <SP <object> -> <bool>>
    is_environment returns true iff its argument is a <environment>
      Deterministic

    extend_environment :: <SP <environment> <symbol> <object> -> <environment>>
    extend_environment returns an extension of the given environment where
    the given symbol is bound to the given object
      Deterministic

    eval :: <SP <exp> <environment> -> <object>>
    eval evaluates the given expression in the given environment and
    returns the result.  Is itself deterministic, but the given expression
    may involve a stochasitc computation.
      Deterministic

    mem :: <SP <SP a ... -> b> -> <SP a ... -> b>>
    mem returns the stochastically memoized version of the input SP.
      Deterministic

    scope_include :: <SP <scope> <block> <object> -> <object>>
    scope_include returns its third argument unchanged at runtime, but
    tags the subexpression creating the object as being within the given
    scope and block.
      Deterministic

    scope_exclude :: <SP <scope> <object> -> <object>>
    scope_exclude returns its second argument unchanged at runtime, but
    tags the subexpression creating the object as being outside the given
    scope.
      Deterministic

    binomial :: <SP <count> <probability> -> <count>>
      (binomial n p) simulates flipping n Bernoulli trials independently
    with probability p and returns the total number of successes.
      Stochastic

    flip :: <SP  -> <bool>>
    flip :: <SP <probability> -> <bool>>
      (flip p) returns true with probability p and false otherwise.  If
    omitted, p is taken to be 0.5.
      Stochastic

    bernoulli :: <SP  -> <number>>
    bernoulli :: <SP <probability> -> <number>>
      (bernoulli p) returns true with probability p and false otherwise.
    If omitted, p is taken to be 0.5.
      Stochastic

    categorical :: <SP <simplex> -> <object>>
    categorical :: <SP <simplex> <array> -> <object>>
      (categorical weights objects) samples a categorical with the given
    weights.  In the one argument case, returns the index of the chosen
    option as an atom; in the two argument case returns the item at that
    index in the second argument.  It is an error if the two arguments
    have different length.
      Stochastic

    uniform_discrete :: <SP <number> <number> -> <number>>
      (uniform_discrete start end) samples a uniform discrete on the
    (start, start + 1, ..., end - 1)
      Stochastic

    poisson :: <SP <positive> -> <count>>
      (poisson lambda) samples a poisson with rate lambda
      Stochastic

    normal :: <SP <number> <number> -> <number>>
      (normal mu sigma) samples a normal distribution with mean mu and
    standard deviation sigma.
      Stochastic, variationable

    uniform_continuous :: <SP <number> <number> -> <number>>
      (uniform_continuous low high) -> samples a uniform real number
    between low and high.
      Stochastic

    beta :: <SP <positive> <positive> -> <probability>>
      (beta alpha beta) returns a sample from a beta distribution with
    shape parameters alpha and beta.
      Stochastic

    gamma :: <SP <positive> <positive> -> <positive>>
      (gamma alpha beta) returns a sample from a gamma distribution with
    shape parameter alpha and rate parameter beta.
      Stochastic

    student_t :: <SP <positive> -> <number>>
    student_t :: <SP <positive> <number> -> <number>>
    student_t :: <SP <positive> <number> <number> -> <number>>
      (student_t nu loc shape) returns a sample from Student's t
    distribution with nu degrees of freedom, with optional location and
    scale parameters.
      Stochastic

    inv_gamma :: <SP <positive> <positive> -> <positive>>
    (inv_gamma alpha beta) returns a sample from an inverse gamma
    distribution with shape parameter alpha and scale parameter beta
      Stochastic

    multivariate_normal :: <SP <array <number>> <symmetricmatrix> -> <array <number>>>
      (multivariate_normal mean covariance) samples a vector according to
    the given multivariate Gaussian distribution.  It is an error if the
    dimensionalities of the arguments do not line up.
      Stochastic

    inv_wishart :: <SP <symmetricmatrix> <positive> -> <symmetricmatrix>>
      (inv_wishart scale_matrix degree_of_freedeom) samples a positive
    definite matrix according to the given inverse wishart distribution
      Stochastic

    wishart :: <SP <symmetricmatrix> <positive> -> <symmetricmatrix>>
      (wishart scale_matrix degree_of_freedeom) samples a positive
    definite matrix according to the given inverse wishart distribution
      Stochastic

    make_beta_bernoulli :: <SP <positive> <positive> -> <SP  -> <bool>>>
      (make_beta_bernoulli alpha beta) returns a collapsed beta bernoulli
    sampler with pseudocounts alpha (for true) and beta (for false).
    While this procedure itself is deterministic, the returned sampler is
    stochastic.
      Deterministic, children can absorb at applications

    make_uc_beta_bernoulli :: <SP <positive> <positive> -> <SP  -> <bool>>>
      (make_uc_beta_bernoulli alpha beta) returns an uncollapsed beta
    bernoulli sampler with pseudocounts alpha (for true) and beta (for
    false).
      Stochastic, children can absorb at applications

    dirichlet :: <SP <array <positive>> -> <simplex>>
      (dirichlet alphas) samples a simplex point according to the given
    Dirichlet distribution.
      Stochastic

    symmetric_dirichlet :: <SP <positive> <count> -> <simplex>>
      (symmetric_dirichlet alpha n) samples a simplex point according to
    the symmetric Dirichlet distribution on n dimensions with
    concentration parameter alpha.
      Stochastic

    make_dir_mult :: <SP <array <positive>> -> <SP  -> <object>>>
    make_dir_mult :: <SP <array <positive>> <array> -> <SP  -> <object>>>
      (make_dir_mult alphas objects) returns a sampler for a collapsed
    Dirichlet multinomial model.  If the objects argument is given, the
    sampler will return one of those objects on each call; if not, it will
    return one of n <atom>s where n is the length of the list of alphas.
    It is an error if the list of objects is supplied and has different
    length from the list of alphas.  While this procedure itself is
    deterministic, the returned sampler is stochastic.
      Deterministic, children can absorb at applications

    make_uc_dir_mult :: <SP <array <positive>> -> <SP  -> <object>>>
    make_uc_dir_mult :: <SP <array <positive>> <array> -> <SP  -> <object>>>
      make_uc_dir_mult is an uncollapsed variant of make_dir_mult.
      Stochastic, children can absorb at applications

    make_sym_dir_mult :: <SP <positive> <count> -> <SP  -> <object>>>
    make_sym_dir_mult :: <SP <positive> <count> <array> -> <SP  -> <object>>>
      make_sym_dir_mult is a symmetric variant of make_dir_mult.
      Deterministic, children can absorb at applications

    make_uc_sym_dir_mult :: <SP <positive> <count> -> <SP  -> <object>>>
    make_uc_sym_dir_mult :: <SP <positive> <count> <array> -> <SP  -> <object>>>
      make_uc_sym_dir_mult is an uncollapsed symmetric variant of
    make_dir_mult.
      Stochastic, children can absorb at applications

    make_crp :: <SP <number> -> <SP  -> <atom>>>
    make_crp :: <SP <number> <number> -> <SP  -> <atom>>>
    (make_crp alpha) -> <SP () <number>>
      Chinese Restaurant Process with hyperparameter alpha.  Returns a
    sampler for the table number.
      Deterministic, children can absorb at applications

    make_cmvn :: <SP <array <number>> <number> <number> <matrix> -> <SP  -> <matrix>>>
    (make_cmvn m0 k0 v0 S0) -> <SP () <float array>>
      Collapsed multivariate normal with hyperparameters m0,k0,v0,S0,
    where parameters are named as in (Murphy, section 4.6.3.3, page 134).
      Deterministic, children can absorb at applications

    make_lazy_hmm :: <SP <simplex> <matrix> <matrix> -> <SP <number> -> <number>>>
      Discrete-state HMM of unbounded length with discrete observations.
    The inputs are the probability distribution of the first state, the
    transition matrix, and the observation matrix.  It is an error if the
    dimensionalities do not line up.  Returns observations from the HMM
    encoded as a stochastic procedure that takes the time step and samples
    a new observation at that time step.
      Deterministic
