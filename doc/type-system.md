Venture Type System
===================

Basic
-----

Venture has the following distinct basic types:
- Floating point numbers (64-bit precision)
- Integers [TODO in Puma]
- Atoms
- Booleans
- Symbols
- Probabilities (represented in direct space, as floating point
  numbers between 0 and 1) [TODO in Puma]
- ForeignBlobs for carrying arbitrary user-supplied data that is
  opaque to Venture [MAYBE add to Puma]

General Containers
------------------

Venture has the following heterogeneous container types:
- Pairs
- Nil, which is the empty list
- Lists  (a list is either Nil or a Pair whose cdr is a List)
- Improper lists (an "improper list", in Lisp culture, is a chain of
    Pairs that one wishes to treat as a list but whose last cdr is not
    Nil.  One can form these in Venture with no ill effect)
- Arrays
- Dictionaries  (any Venture value may be used as a key; some exotic
    choices may lead to silent mistakes)
- 1st class environments
- Procedures

All elements of heterogeneous container types are stored boxed in
Venture boxes (and, in Lite, also as Python types).

All Venture types are immutable.
- Except that environments and (compound) procedures can be mutated by
  inference
- If you think you want a container whose elements can be mutated
  by inference without copying the container, make a container of
  (possibly memmed) thunks.

The difference between lists and arrays is:
- lists have O(1) functional add-to-front and O(k) lookup
- arrays offer O(1) lookup but cannot be updated (except by
  copying)

Unboxed Containers
------------------

Venture has the following homogeneous unboxed container types:
- Arrays of arbitrary Venture values stored unboxed [TODO in Puma]
- Arrays of floating point numbers, called Vector
- Arrays of probabilities, called Simplex
- Matrices of floating point numbers
- Symmetric matrices of floating point numbers (which are not
  actually represented differently from general matrices)

[TODO] In Lite, the ArrayUnboxed representation tries to store the
underlying objects in numpy arrays when possible, to avoid Python's
boxes as well as Venture's.

Contracts
---------

Contracts, that is, invariants that are not baked in to the
representation of a value, arise early and often in Venture.  For
example, both of the parameters to the gamma distribution must be
positive reals, as is the result.

Generally such invariants are represented only in the type annotations
of procedures (or implicitly in Puma).  However, a couple things that
might appear to be such are represented as distinct Venture types that
happen to have the same representation as a "broader" type:
- Probabilities (in direct space), which look like numbers in [0,1]
- Symmetric matrices, which look like matrices

The rule of thumb in the design for choosing which invariants to treat
as implicit contracts and which to turn into explicit types is this:
If something might want to dispatch on the presence or absence of a
contract, then tag.  Otherwise, push it into the type.

[TODO] It might be useful to memoize checking contracts (or
normalizing representations) if any of them are expensive.  I'm
looking at you, Simplex.

Coersions
---------

The following Venture types are implicitly coerced to one another when
needed.  If a coersion fails, an error is raised.

- Unboxed X to boxed X by boxing [TODO in Puma]
- Boxed X to unboxed X by type checking and unboxing (may fail) [TODO in Puma]
- Proper linked lists to arrays
- Integers to floating point numbers [TODO in Puma]
- Probabilities to floating point numbers by injection
- Floating point numbers to direct-space probabilities by range
  checking (may fail) [MAYBE remove]
- Symmetric matrices to general matrices by injection [TODO in Puma]
- Matrices to symmetric matrices by checking symmetry (may fail) [TODO in Puma]

Some Venture SPs also implement explicit coersions.

Representations
---------------

Implementers and extenders of Venture need to know about 6 different
representations that Venture uses for its values.

- The normative representation is instances of (subclasses of) the
  VentureValue class defined in the Lite backend.

- The common Python utilities shared by Lite and Puma (called the
  "stack") have a representation of Venture values called "stack
  dicts".  The defining feature of this representation is that it is
  meant to be serializable for all types that it is reasonable to
  serialize (to wit, everything that does not contain an environment).

  - There is a 1-to-1 mapping between VentureValues and stack dicts,
    implemented by VentureValue.asStackDict() and
    VentureValue.fromStackDict(sd)

  - [TODO] To the extent possible, this mapping is O(b), where b is
    the number of VentureValue boxes involved in the VentureValue
    representation.  In other words, I would hope that unboxed arrays
    and matrices can be converted to and from stack dicts in time
    independent of the size of their data arrays.

- SPs written for Lite can choose, through their type annotations, to
  see their inputs and outputs as "natural" Python objects.

  - Any given VentureType defines a 1-to-1 mapping between all the
    VentureValues of that type and a natural representation in Python.
    What that representation is is type-dependent.

    - [TODO] Ideally, the conversion would be O(b), where b is the
      number of VentureValues boxes involved in the representation.
      Note that a parametrically polymorphic SP can declare its
      desired "natural representation" to be the same VentureValue
      boxes, obviating the need to convert them.

  - Not all sets of Venture values can be given a type in this sense,
    because Venture makes type distinctions that Python does not (or
    at least that Python obscures).

  - N.B.: A VentureType may convert to Python some Venture values that
    are not of that type.  This is effectively an implicit coercion
    mechanism.

- The Puma backend represents Venture values as instances of
  (subclasses of) Puma's VentureValue class.

  - [TODO] There is a 1-to-1 mapping between Puma VentureValues and
    stack dicts.

  - This mapping is very unlikely to be O(b) like the one in Lite,
    unless the numpy people and the Eigen people have taken pains to
    store their data in compatible form.

- SPs written for Puma can operate on "natural" C++ representations of
  their inputs and outputs.

  - The types are not explicit like they are in Lite, but appropriate
    methods of the Puma VentureValue class effect the conversions.

    - [TODO] Can this be improved?

    - [TODO] The conversions defined by Puma's implicit type system
      should be 1-to-1 and O(b) like the ones in Lite.

  - [TODO] All Puma and Lite SPs have the same types, effect the same
    implicit conversions, etc.

- Finally, most Venture values can be produced as results of
  "constant-foldable" Venture expressions.  This representation is
  available through the expressionFor method of VentureValue. [MAYBE
  remove]

Injection
---------

Putting a stack dict into an expression (quoted) or the value slot of
an observation should result in that value.  [TODO confirm in Lite;
implement in Puma]

Types
-----

Venture Lite has an explicit notion of VentureType.  A VentureType
defines a conversion between the VentureValue representation of a
value of that type and a "natural" Python representation.

- [TODO] The conversion defined by a given VentureType should be
  1-to-1 and O(b), where b is the number of VentureValue boxes that
  need to be unpacked to effect the conversion.

- Different VentureTypes may convert the same VentureValue to
  different Python values, or the same Python value to different
  VentureValues.

  - Notably, AnyType converts any VentureValue to itself.  This is
    legit because VentureValue is a Python class, and this is useful
    because (parametrically) polymorphic SPs may not need (all of)
    their inputs converted to do their job.

- A VentureType's conversion may accept VentureValues outside of that
  type.  This is a form of implicit coersion.

VentureTypes can be compositional.  For example, HomogeneousArrayType
requires one VentureType as an argument, and defines the conversion
that turns a (boxed) VentureArray all of whose elements happen to
match the argument type into a Python list whose elements have been
unwrapped by the argument type (and back).

A VentureType also corresponds to a human-readable description of the
type, for autogenerating SP documentation; and to a default generator
of values of that type, for randomized testing.
- Actually, the generator is parameterized by a base distribution
  object (the only exant one of which is DefaultRandomVentureValue)
  through the distribution method of the VentureType.

Future
------

Types that Venture may be extended to have in the future:
- Complex numbers
- Floating point numbers of varying precision
- Rational numbers
- Representations of probabilities in different spaces
- Unboxed vectors or matrices of integers, booleans, ? atoms,
  different precision floats, complex numbers, probabilities
- Unboxed homogeneous dictionaries
- Efficiently functionally updatable dictionaries (maybe requiring an
  ordering on the keys)
  - in boxed and unboxed form
- Strings (which look like unboxed vectors of characters)

We may wish to remove the following types Venture currently has:
- Atom
- ForeignBlob

We may also wish to remove the expressionFor representation of Venture
values (or downgrade it to being a debugging tool only).

How to Extend the Venture Type System
-------------------------------------

To add a type to the type system in Lite
- define a subclass of VentureType (conventionally named
  SomethingType)
- define asVentureValue and asPython methods for it, that are
  preferably mutual inverses, implementing the mapping to the
  "natural" Python representation
  - If there are coercions involved, adding a method to the
    VentureValue hierarchy may be appropriate.
- define __contains__ for checking whether a VentureValue is of this
  type
- define name describing the type
- if the type corresponds exactly to a subclass of VentureValue,
  the above are standard (see standard_venture_type).
- either override the distribution method, or define an appropriately
  named method in DefaultRandomVentureValue to be able to generate
  values of this type.
  - Possibly add the new type to the default distribution for AnyType

To then add the type to the type system in Puma
- extend Puma's VentureValue hierarchy with appropriate methods to
  effect conversion to and from this type, preferably to a C++
  representation that is analogous to the "natural" Python one.

To add a representation to the type system
- Add a subclass of VentureValue, overriding all appropriate methods
  - Coersions to "native" Python representations for various types
  - Conversion to and from stack dicts
    - Define a distinct "type" keyword for the stack dict representation
  - Comparison
  - Equality
  - If the new type should respond to size, lookup, and contains,
    define corresponding container methods
  - If relevant, define the real vector space operations for the representation
  - expressionFor if appropriate
- Add a subclass of Puma VentureValue, overriding all appropriate methods
- Presumably define a VentureType corresponding to the new
  representation (see standard_venture_type in value.py)
  - Presumably including an appropriate extention of Puma's
    VentureValue hierarchy
- If appropriate, add the new representation to any existing types
  that should cover it, such as ExpressionType
