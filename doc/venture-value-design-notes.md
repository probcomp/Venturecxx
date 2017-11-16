Desiderata informing the design of the Venture value system
-----------------------------------------------------------

Circa late June 2014

- Need a Python-level boxed value representation
  - Currently stack dicts, could be VentureValues
    - By faking the [] operator??
- Bijection between VentureValues and boxed-Python representation
- Type-mediated mapping between VentureValues and the representation
  that a Lite SP implementation sees
  - Needs to be type-mediated because the mapping from VentureValues
    to their "natural" Python representations is not globally
    injective.
    - because of booleans, exactness, contracts, linked lists, and
      boxed vs unboxed aggregates (maybe SP could say whether it wants
      a Python list or a numpy array or what-all)
- Bijection between the Puma internal value representation and
  boxed-Python value representation
  - Possibly through stack dicts
- Presumably Puma also has a type-mediated bijection between
  VentureValues and the SP-facing representation (though the types may
  be implicit)
- Boxed-Python representation serializable to strings and network
  - (stack dicts currently aren't b/c of some VentureValues)
- Would be nice to be able to convert native Python data structures
  (e.g., lists and numpy arrays) into the boxed-Python rep and
  VentureValues in O(1).
- Seems good to require every SP to be able to translate its aux
  to a VentureValue and back
  - Ideally, to a VentureValue that was an element of a known Abelian group...

Types we have some evidence that we want in Venture:
- Floating point numbers
- Integers
- Atoms?
- Booleans
- Symbols
- Pairs (general tuples?)
- Boxed heterogeneous linked lists
  - Nil?
- Boxed heterogeneous random-access linear containers (arrays?)
- For each known-size thing, unboxed homogeneous random-access linear containers
- Unboxed homogeneous 2D matrices (of just numbers, or all known-size things)?
- General unboxed homogeneous tensors?
- Backing policy for unboxed stuff: always numpy/Eigen? always native?
  always minimize format conversions?
  - Note that Python has two different notions of "unboxed": no Venture boxing
    and then also no Python boxing.  Only numpy offers the latter.
- Boxed dictionaries
- Could imagine unboxed homogeneous dictionaries (by key, by value, or both)
- Environments
- SPs
- SPRefs
- Foreign Blob (no conversions of any kind, assumed useful only for
  custom SPs, should be able to optionally implement methods like hash)
  - Do we really need a default wrapper at all, or should we just
    provide a very clear interface to extending Venture values?
  - Daniel wanted this for the captcha work (image data)
- May want several user-space representations of probability values,
  for situations like the logistic regression example.  May want a
  suite of generic SPs that operate on them usefully.
  - binomial, bernoulli take one
  - categorical takes a vector of them
  - plus, times, etc operate on them
  - maybe as distinguished from negate, and, disjoint or, so that
    plus and times always operate on the underlying representation
    but don't always mean the logical analogues
  - Vikash suggests that it may be appropriate to have things like a
    beta distribution that dispatches on the representation of the
    incoming pseudo-counts and returns an appropriately-represented
    probability
  - Vikash approved the boxes; suggested that sooner or later we may
    wish to expose versions of bernoulli, etc that accept an unboxed
    representation (essentially fuse the box into the dispatch)
- Do we want values "with contracts"?  Inference would be called upon
  not to violate them; may also be able to use some of the structure.
  - Positive or non-negative
  - Between 0 and 1
  - uniform exhibits general bounds
  - sigma in normal is constrained non-zero
  - "Simplex", which is allegedly an unboxed array of direct-space(!)
    probabilities that are assumed exclusive from one another
  - "Symmetric matrix" (HMC wants to know about this!)
  - SP contracts in the normal way
    - Randomized testing loves structured SP contracts
      - Could invite the contract itself to simulate!
  - The "output promise" contract of simulate seems like it serves
    double duty as one of the "input requirement" contracts for that
    SP's logDensity function.
    - But violations could manifest as 0-density values rather than
      errors.

- Will eventually want user-defined product values (records); possibly
  user-defined sum types; possibly user-defined contracts (possibly
  per-variable, or only on procedures) (choice of violation semantics:
  either fail the program or reject the transition).

Type structure we have evidence of having a use for:
- AD wants a cotangent space structure on VentureValues.  It is not
  necessarily the case that the type of a cotangent vector on a thing
  is the same as the type of the thing itself (discrete items, contracts)
  - But I must be able to move an element of the base space by an
    element of the cotangent space.
  - It seems that Meanfield wants this too
  - If I do this with a separate type hierarchy, I can add asserts
    that check that gradient things always produce elements of
    (corresponding!)  cotangent spaces.
  - HMC's momenta live in the (tagent or cotangent?) space; HMC's
    gradient lives in the cotangent space; but must be able to push
    the momenta.  This certainly works out in the Euclidean case; it
    may be that Riemannian HMC is just about the curved case.
- Slice sampling wants a "real number" structure on the values it
  operates on.
  - currently given by the source SP (in Puma with the "isContinuous"
    flag), but possibly modifiable by (dependent!) contracts
- Enumerative Gibbs wants an "enumerable" structure on the values it
  operates on
  - currently given by the source SP; possibly modifiable by
    (dependent!) contracts
  - currently only discrete, but could imagine value of playing
    quadrature games for continuous 1D values
- HMC wants a "sample me some momenta" structure
  - May be able to get this from the source SP as well
