from nose import SkipTest
from testconfig import config
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

def get_ripl():
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

def defaultInfer():
  # TODO adjust the number of transitions to be at most the default_num_transitions_per_sample
  return config["infer"]

def defaultKernel():
  raise SkipTest("TODO: Do a better job of selecting when to run some test")
  return defaultInfer()["kernel"]

