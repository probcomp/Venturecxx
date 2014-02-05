from testconfig import config
from venture.shortcuts import make_lite_church_prime_ripl, make_church_prime_ripl

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
    return make_lite_church_prime_ripl()
  elif config["get_ripl"] == "cxx":
    return make_church_prime_ripl()
  else:
    raise Exception("Unknown backend type %s" % config["get_ripl"])


def collectSamples(ripl,address,num_samples=None,infer=None):
  if num_samples is None:
    num_samples = default_num_samples()
  if infer is None:
    infer = defaultInfer()
  elif infer == "mixes_slowly": # TODO Replace this awful hack with proper adjustment of tests for difficulty
    infer = defaultInfer()
    infer["transitions"] = 4 * int(infer["transitions"])

  predictions = []
  for _ in range(num_samples):
    # Going direct here saved 5 of 35 seconds on some unscientific
    # tests, presumably by avoiding the parser.
    ripl.sivm.core_sivm.engine.infer(infer)
    predictions.append(ripl.report(address))
    if collect_iid_samples(): ripl.sivm.core_sivm.engine.reset()
  return predictions

def defaultInfer():
  numTransitionsPerSample = default_num_transitions_per_sample()
  kernel = config["kernel"]
  scope = config["scope"]
  block = config["block"]

  with_mutation = bool_like_option("with_mutation", True)
  particles = int(config["particles"]) if "particles" in config else None
  return {"transitions":numTransitionsPerSample,
          "kernel":kernel,
          "scope":scope,
          "block":block,
          "with_mutation":with_mutation,
          "particles":particles
          }
