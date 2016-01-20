# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

"""Customizations of the Venture test suite.

The Venture test suite has more structure than a typical "unit test"
suite for a typical software system.  Notably, there is a chunk of
tests of the form "This model should be solved by this inference
method", and another chunk of the form "This model should be solved by
any reasonable inference method."

A problem we have is that testing inference quality tends to be
relatively expensive -- one needs several samples, and typically the
inference methods one is testing need to run for several iterations.
That's two nested loops that hardly add anything from the perspective
of looking for crash bugs; yet, we want to be able to reuse those
tests as crash tests in addition to inference quality tests.

That is the main problem this module solves, as well as the problem
that most models are runnable in any backend.

To write a new test:

- If your test should be generic across backends, use get_ripl or
  get_mripl from this module instead of venture.shortcuts

- If not, please decorate it with @in_backend (or @gen_in_backend)
  to keep Jenkins from running it redundantly

- If your test wants samples from a distribution produced by a single
  inference program over a model with a single (relevant) predict
  statement, try to use collectSamples, collectStateSequence, or
  collectIidSamples rather than calling ripl.infer directly, because
  they are sensitive to whether the test is being run for inference
  quality

  - If your test is agnostic to the inference program, do not pass an
    infer argument to collectSamples

  - If not, please decorate it with @on_inf_prim or @gen_on_inf_prim

- If your test checks properties of distributions, see whether you
  can use @statisticalTest from the stats module

- If your test is known to fail in a particular backend or under other
  particular modes, and you are not currently fixing it, consider
  annotating it with @broken_in, @gen_broken_in, or
  @skipWhenRejectionSampling, @skipWhenInParallel

- If your test is known to fail in other circumstances, and you are
  not fixing it, raise a SkipTest exception from the nose module

"""

from StringIO import StringIO
from inspect import isgeneratorfunction
import sys

from nose import SkipTest
import nose.tools as nose
from testconfig import config

import venture.shortcuts as s
import venture.venturemagics.ip_parallel as ip_parallel
import venture.value.dicts as v

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
def default_num_samples(factor=1):
  if not ignore_inference_quality():
    return int(config["num_samples"]) * factor
  else:
    return 2

def default_num_transitions_per_sample():
  if not ignore_inference_quality():
    return int(config["num_transitions_per_sample"])
  else:
    return 3

disable_get_ripl = False
ct_get_ripl_called = 0

def get_ripl(**kwargs):
  assert not disable_get_ripl, "Trying to get the configured ripl in a test marked as not ripl-agnostic."
  global ct_get_ripl_called
  ct_get_ripl_called += 1
  return s.backend(config["get_ripl"]).make_combined_ripl(**kwargs)

def get_mripl(no_ripls=2,local_mode=None,**kwargs):
   # NB: there is also global "get_mripl_backend" for having special-case backend
   # for mripl
  backend = config["get_ripl"]
  local_mode = config["get_mripl_local_mode"] if local_mode is None else local_mode
  return ip_parallel.MRipl(no_ripls,backend=backend,local_mode=local_mode,**kwargs)


def get_core_sivm():
  return s.backend(config["get_ripl"]).make_core_sivm()


def collectSamples(*args, **kwargs):
  """Repeatedly run inference on a ripl and query a directive, and return the list of values.

  The first argument gives the ripl against which to do this

  The second argument gives the number or label of the directive to
  query (by the ripl 'report' method)

  The inference program is given by the 'infer' keyword argument;
  default to the configured default inference

  The number of samples is given by the 'num_samples' keyword
  argument; default to the configured default number of samples

  There are two natural versions of what this means: The returned
  sample list should be either:

  - IID samples from the distribution that arises from running the
    infer command once (obtained by resetting the ripl between
    sampling)

  - A (dependent) sequence given by running inference repeatedly
    without resetting the ripl and querying between runs

  Which one you get from collectSamples depends on a configuration
  parameter (which defaults to IID).  If you want to force this issue,
  use collectIidSamples or collectStateSequence.

  """
  return _collectData(collect_iid_samples(), *args, **kwargs)

def collectStateSequence(*args, **kwargs):
  """collectSamples but pegged to continuing inference (no resetting)"""
  return _collectData(False, *args, **kwargs)

def collectIidSamples(*args, **kwargs):
  """collectSamples but pegged to IID samples (resetting the ripl)"""
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
      infer = "(repeat 4 (do %s))" % infer

  predictions = []
  for _ in range(num_samples):
    # TODO Consider going direct here to avoid the parser
    ripl.infer(infer)
    predictions.append(ripl.report(address))
    if iid:
      ripl.sivm.core_sivm.engine.reinit_inference_problem()
      ripl.infer(v.app(v.sym("incorporate")))
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

def needs_backend(backend):
  """Marks this test as needing the given backend."""
  def wrap(f):
    assert not isgeneratorfunction(f), \
      "Use gen_needs_backend for test generator %s" % (f.__name__,)
    @nose.make_decorator(f)
    def wrapped(*args):
      try:
        s.backend(backend).make_combined_ripl()
      except Exception as e:
        raise SkipTest(f.__name__ + " needs " + backend)
      return f(*args)
    return wrapped
  return wrap

def gen_needs_backend(backend):
  """Marks this test generator as needing the given backend."""
  def wrap(f):
    assert isgeneratorfunction(f), \
      "Use needs_backend for non-generator test %s" % (f.__name__,)
    @nose.make_decorator(f)
    def wrapped(*args):
      try:
        s.backend(backend).make_combined_ripl()
      except Exception as e:
        raise SkipTest(f.__name__ + " needs " + backend)
      for t in f(*args):
        yield t
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
  "meanfield", "hmc", "grad_ascent", "nesterov", "rejection", "slice", or
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
  "meanfield", "hmc", "grad_ascent", "nesterov", "rejection", "slice", or
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
        return f(*args)
      else:
        raise SkipTest(reason)
    wrapped.skip_when_rejection_sampling = True # TODO Skip by these tags in all-crashes & co
    return wrapped
  return wrap

def rejectionSampling():
  return config["infer"].startswith("(rejection default all")

# TODO Abstract commonalities with the rejection skipper
def skipWhenSubSampling(reason):
  """Annotate a test function as being suitable for testing all
general-purpose inference programs except sub-sampled MH.

  """
  def wrap(f):
    @nose.make_decorator(f)
    def wrapped(*args):
      if not subSampling():
        return f(*args)
      else:
        raise SkipTest(reason)
    wrapped.skip_when_sub_sampling = True # TODO Skip by these tags in all-crashes & co
    return wrapped
  return wrap

def subSampling():
  return config["infer"].startswith("(subsampled_mh")

def skipWhenInParallel(reason):
  def wrap(f):
    @nose.make_decorator(f)
    def wrapped(*args):
      if not inParallel():
        return f(*args)
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

def needs_ggplot(f):
  assert not isgeneratorfunction(f), "Use gen_needs_ggplot for generator test %s" % f.__name__
  @nose.make_decorator(f)
  def wrapped(*args):
    try:
      import ggplot             # pylint: disable=unused-variable
      return f(*args)
    except ImportError:
      raise SkipTest("ggplot not installed on this machine")
  return wrapped

def gen_needs_ggplot(f):
  assert isgeneratorfunction(f), "Use needs_ggplot for non-generator test %s" % f.__name__
  @nose.make_decorator(f)
  def wrapped(*args):
    try:
      import ggplot
      for t in f(*args): yield t
    except ImportError:
      raise SkipTest("ggplot not installed on this machine")
  return wrapped

def capture_output(ripl, program):
  'Capture stdout; return the string headed for stdout and the result of the computation'
  old_stdout = sys.stdout
  captured = StringIO()
  sys.stdout = captured
  res = ripl.execute_program(program)
  sys.stdout = old_stdout
  return res, captured.getvalue()
