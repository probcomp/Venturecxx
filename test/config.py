import nose.tools as nose
from nose import SkipTest
from testconfig import config
from inspect import isgeneratorfunction

import venture.shortcuts as s
import venture.venturemagics.ip_parallel as ip_parallel

def yes_like(thing):
  if isinstance(thing, str):
    return thing.lower() in ["y", "yes", "t", "true"]
  elif thing: return True
  else: return False

def no_like(thing):
  if isinstance(thing, str):
    return thing.lower() in ["n", "no", "f", "false"]
  elif not thing: return True
  else: return False

def bool_like_option(name, default):
  thing = config[name]
  if yes_like(thing): return True
  elif no_like(thing): return False
  else:
    print "Option %s valued %s not clearly truthy or falsy, treating as %s" % (name, thing, default)
    return default

def ignore_inference_quality():
  return bool_like_option("ignore_inference_quality", False)

def collect_iid_samples():
  return bool_like_option("should_reset", True)

# These sorts of contortions are necessary because nose's parser of
# configuration files doesn't seem to deal with supplying the same
# option repeatedly, as the nose-testconfig plugin calls for.
def default_num_samples():
  if not ignore_inference_quality():
    return int(config["num_samples"])
  else:
    return 2

def default_num_transitions_per_sample():
  if not ignore_inference_quality():
    return int(config["num_transitions_per_sample"])
  else:
    return 3

disable_get_ripl = False
ct_get_ripl_called = 0

def get_ripl():
  assert not disable_get_ripl, "Trying to get the configured ripl in a test marked as not ripl-agnostic."
  global ct_get_ripl_called
  ct_get_ripl_called += 1
  return s.backend(config["get_ripl"]).make_church_prime_ripl()

def get_mripl(no_ripls=2,local_mode=None,**kwargs):
   # NB: there is also global "get_mripl_backend" for having special-case backend
   # for mripl
  backend = config["get_ripl"]
  local_mode = config["get_mripl_local_mode"] if local_mode is None else local_mode
  return ip_parallel.MRipl(no_ripls,backend=backend,local_mode=local_mode,**kwargs)


def get_core_sivm():
  return s.backend(config["get_ripl"]).make_core_sivm()


def collectSamples(*args, **kwargs):
  return _collectData(collect_iid_samples(), *args, **kwargs)

def collectStateSequence(*args, **kwargs):
  return _collectData(False, *args, **kwargs)

def collectIidSamples(*args, **kwargs):
  return _collectData(True, *args, **kwargs)

def _collectData(iid,ripl,address,num_samples=None,infer=None):
  if num_samples is None:
    num_samples = default_num_samples()
  if infer is None:
    infer = defaultInfer()
  elif infer == "mixes_slowly":
    # TODO Replace this awful hack with proper adjustment of tests for difficulty
    infer = defaultInfer()
    if infer is not "(rejection default all 1)":
      infer = "(cycle (%s) 4)" % infer

  predictions = []
  for _ in range(num_samples):
    # TODO Consider going direct here to avoid the parser
    ripl.infer(infer)
    predictions.append(ripl.report(address))
    if iid: ripl.sivm.core_sivm.engine.reinit_inference_problem()
  return predictions

disable_default_infer = False

def defaultInfer():
  # TODO adjust the number of transitions to be at most the default_num_transitions_per_sample
  assert not disable_default_infer, "Trying to access the default inference program in a test marked not inference-agnostic."
  return config["infer"]

######################################################################
### Test decorators                                                ###
######################################################################

def in_backend(backend):
  """Marks this test as testing the given backend.

That is, the test could conceivably expose a bug introduced by changes
confined to that backend.  Only works for non-generator tests---use
gen_in_backend for generators.  Possible values are:

  "lite", "puma" for that backend
  "none" for a backend-independent test (i.e., does not test backends meaningfully)
  "any"  for a backend-agnostic test (i.e., should work the same in any backend)
  "all"  for a test that uses all backends (e.g., comparing them)

Example:
@in_backend("puma")
def testSomethingAboutPuma():
  ripl = make_puma_church_prime_ripl()
  ...

  """
  # TODO Is there a way to reduce the code duplication between the
  # generator and non-generator version of this decorator?
  def wrap(f):
    assert not isgeneratorfunction(f), "Use gen_in_backend for test generator %s" % f.__name__
    @nose.make_decorator(f)
    def wrapped(*args):
      name = config["get_ripl"]
      if backend in ["lite", "puma"] and not name == backend:
        raise SkipTest(f.__name__ + " doesn't test " + name)
      global disable_get_ripl
      old = disable_get_ripl
      disable_get_ripl = False if backend is "any" else True
      try:
        return f(*args)
      finally:
        disable_get_ripl = old
    wrapped.backend = backend
    return wrapped
  return wrap

def gen_in_backend(backend):
  """Marks this test generator as generating tests that test the given backend.

That is, the generated tests could conceivably expose a bug introduced
by changes confined to that backend.  Only works for test
generators---use in_backend for individual tests.  Possible values are:

  "lite", "puma" for that backend
  "none" for backend-independent tests (i.e., does not test backends meaningfully)
  "any"  for backend-agnostic tests (i.e., should work the same in any backend)
  "all"  for tests that use all backends (e.g., comparing them)

Example:
@gen_in_backend("puma")
def testSomeThingsAboutPuma():
  for thing in some(things):
    yield ...

  """
  # TODO Is there a way to reduce the code duplication between the
  # generator and non-generator version of this decorator?
  def wrap(f):
    assert isgeneratorfunction(f), "Use in_backend for non-generator test %s" % f.__name__
    @nose.make_decorator(f)
    def wrapped(*args):
      name = config["get_ripl"]
      if backend in ["lite", "puma"] and name is not backend:
        raise SkipTest(f.__name__ + " doesn't test " + name)
      global disable_get_ripl
      old = disable_get_ripl
      disable_get_ripl = False if backend is "any" else True
      try:
        for t in f(*args): yield t
      finally:
        disable_get_ripl = old
    wrapped.backend = backend
    return wrapped
  return wrap

def broken_in(backend, reason = None):
  """Marks this test as being known to be broken in some backend."""
  def wrap(f):
    assert not isgeneratorfunction(f), "Use gen_broken_in for test generator %s" % f.__name__
    @nose.make_decorator(f)
    def wrapped(*args):
      ripl = config["get_ripl"]
      if ripl == backend:
        msg = " because " + reason if reason is not None else ""
        raise SkipTest(f.__name__ + " doesn't support " + ripl + msg)
      return f(*args)
    return wrapped
  return wrap

def gen_broken_in(backend, reason = None):
  """Marks this test as being known to be broken in some backend."""
  def wrap(f):
    assert isgeneratorfunction(f), "Use broken_in for non-generator test %s" % f.__name__
    @nose.make_decorator(f)
    def wrapped(*args):
      ripl = config["get_ripl"]
      if ripl == backend:
        msg = " because " + reason if reason is not None else ""
        raise SkipTest(f.__name__ + " doesn't support " + ripl + msg)
      for t in f(*args): yield t
    return wrapped
  return wrap

def on_inf_prim(primitive):
  """Marks this test as testing the given inference primitive.

That is, the test could conceivably expose a bug introduced by changes
confined to that primitive or supporting SP methods.  Only works for
non-generator tests---use gen_on_inf_prim for generators.  Possible
values are:

  "mh", "func_mh", "gibbs", "emap", "pgibbs", "func_pgibbs",
  "meanfield", "hmc", "map", "nesterov", "rejection", "slice", or
  "slice_doubling", "resample", "peek", "plotf"
         for that inference primitive
  "none" for a primitive-independent test (i.e., does not test inference meaningfully)
  "any"  for a primitive-agnostic test (i.e., should work the same for
         any sound inference program)
  "all"  for a test that uses some complicated inference program

  TODO Do we want to support something more precise than "all" for
  tests with specific inference programs that use several primitives?

Example:
@on_inf_prim("slice")
def testSomethingAboutSlice():
  ...
  ripl.infer("(slice default one 0.5 100 20)")
  ...

Note: any test that is already backend-independent is perforce
inference-independent, since all inference happens in backends.  Such
tests need not be tagged with on_inf_prim, because the selection takes
this into account.

  """
  # TODO Is there a way to reduce the code duplication between the
  # generator and non-generator version of this decorator?
  def wrap(f):
    assert not isgeneratorfunction(f), "Use gen_on_inf_prim for test generator %s" % f.__name__
    @nose.make_decorator(f)
    def wrapped(*args):
      global disable_default_infer
      old = disable_default_infer
      disable_default_infer = False if primitive is "any" else True
      try:
        return f(*args)
      finally:
        disable_default_infer = old
    wrapped.inf_prim = primitive
    return wrapped
  return wrap

def gen_on_inf_prim(primitive):
  """Marks this test generator as generating tests that test the given inference primitive.

That is, a generated test could conceivably expose a bug introduced by
changes confined to that primitive or supporting SP methods.  Only
works for generator tests---use on_inf_prim for non-generators.
Possible values are:

  "mh", "func_mh", "gibbs", "emap", "pgibbs", "func_pgibbs",
  "meanfield", "hmc", "map", "nesterov", "rejection", "slice", or
  "slice_doubling", "resample", "peek", "plotf"
         for that inference primitive
  "none" for primitive-independent tests (i.e., do not test inference meaningfully)
  "any"  for primitive-agnostic tests (i.e., should work the same for
         any sound inference program)
  "all"  for tests that use some complicated inference program

  TODO Do we want to support some way for a generator to tag the
  generated tests with different primitives?  Or is that not worth the
  trouble?

Example:
@gen_on_inf_prim("slice")
def testSomeThingsAboutSlice():
  for thing in some(things):
    yield ...

Note: any test that is already backend-independent is perforce
inference-independent, since all inference happens in backends.  Such
tests need not be tagged with gen_on_inf_prim, because the selection
takes this into account.

  """
  # TODO Is there a way to reduce the code duplication between the
  # generator and non-generator version of this decorator?
  def wrap(f):
    assert isgeneratorfunction(f), "Use on_inf_prim for non-generator test %s" % f.__name__
    @nose.make_decorator(f)
    def wrapped(*args):
      global disable_default_infer
      old = disable_default_infer
      disable_default_infer = False if primitive is "any" else True
      try:
        for t in f(*args): yield t
      finally:
        disable_default_infer = old
    wrapped.inf_prim = primitive
    return wrapped
  return wrap

def skipWhenRejectionSampling(reason):
  """Annotate a test function as being suitable for testing all
general-purpose inference programs except rejection sampling.

  """
  def wrap(f):
    @nose.make_decorator(f)
    def wrapped(*args):
      if not rejectionSampling():
        f(*args)
      else:
        raise SkipTest(reason)
    wrapped.skip_when_rejection_sampling = True # TODO Skip by these tags in all-crashes & co
    return wrapped
  return wrap

def rejectionSampling():
  return config["infer"].startswith("(rejection default all")

def skipWhenInParallel(reason):
  def wrap(f):
    @nose.make_decorator(f)
    def wrapped(*args):
      if not inParallel():
        f(*args)
      else:
        raise SkipTest(reason)
    wrapped.skip_when_in_parallel = True # TODO Skip by these tags in all-crashes & co
    return wrapped
  return wrap

def inParallel():
  for operator in ["gibbs", "pgibbs", "func_pgibbs"]:
    if config["infer"].startswith("(" + operator) and not config["infer"].endswith("false)"):
      return True
  return False
