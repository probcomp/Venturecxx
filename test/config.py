from testconfig import config
import venture.shortcuts as s

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
  if config["get_ripl"] == "lite":
    return s.make_lite_church_prime_ripl()
  elif config["get_ripl"] == "cxx":
    return s.make_cxx_church_prime_ripl()
  elif config["get_ripl"] == "puma":
    return s.make_puma_church_prime_ripl()
  else:
    raise Exception("Unknown backend type %s" % config["get_ripl"])

def get_core_sivm():
  if config["get_ripl"] == "lite":
    return s.make_core_lite_sivm()
  elif config["get_ripl"] == "cxx":
    return s.make_core_cxx_sivm()
  elif config["get_ripl"] == "puma":
    return s.make_core_puma_sivm()
  else:
    raise Exception("Unknown backend type %s" % config["get_ripl"])


def collectSamples(*args, **kwargs):
  return _collectData(collect_iid_samples(), *args, **kwargs)

def collectStateSequence(*args, **kwargs):
  return _collectData(False, *args, **kwargs)

def collectIidSamples(*args, **kwargs):
  return _collectData(True, *args, **kwargs)

def _collectData(iid,ripl,address,num_samples=None,infer=None,infer_merge=None):
  if num_samples is None:
    num_samples = default_num_samples()
  if infer is None:
    infer = defaultInfer()
  elif infer == "mixes_slowly": # TODO Replace this awful hack with proper adjustment of tests for difficulty
    infer = defaultInfer()
    if not infer["kernel"] == "rejection":
      infer["transitions"] = 4 * int(infer["transitions"])

  if infer_merge is not None: infer.update(infer_merge)

  predictions = []
  for _ in range(num_samples):
    # Going direct here saved 5 of 35 seconds on some unscientific
    # tests, presumably by avoiding the parser.
    ripl.sivm.core_sivm.engine.infer(infer)
    predictions.append(ripl.report(address))
    if iid: ripl.sivm.core_sivm.engine.reset()
  return predictions

def defaultInfer():
  from venture.ripl.utils import parse, expToDict
  candidate = expToDict(parse(config["infer"]))
  candidate["transitions"] = min(default_num_transitions_per_sample(), int(candidate["transitions"]))
  return candidate

def defaultKernel():
  return defaultInfer()["kernel"]
