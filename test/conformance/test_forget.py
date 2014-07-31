from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("none")
def testForgetSmoke1():
  ripl = get_ripl()
  for i in range(10):
    pid = "pid%d" % i
    ripl.predict("(flip)",label=pid)
    ripl.forget(pid)

@on_inf_prim("none")
def testForgetSmoke2():
  ripl = get_ripl()
  for i in range(10):
    pid = "pid%d" % i
    ripl.predict("(flip)",label=pid)

  for i in range(10):
    pid = "pid%d" % i
    ripl.forget(pid)

@on_inf_prim("mh")
def testForgetContinuousInference3():
  ripl = get_ripl()
  for i in range(10):
    pid = "pid%d" % i
    ripl.predict("(flip)",label=pid)
    ripl.infer(5)
    
  for i in reversed(range(10)):
    pid = "pid%d" % i
    ripl.forget(pid)
    ripl.infer(5)

@on_inf_prim("mh")
def testForgetContinuousInference4():
  ripl = get_ripl()
  for i in range(10):
    pid = "pid%d" % i
    ripl.observe("(flip)","true",label=pid)
    ripl.infer(5)
    
  for i in range(10):
    pid = "pid%d" % i
    ripl.forget(pid)
    ripl.infer(5)

  for i in range(10,20):
    pid = "pid%d" % i
    ripl.observe("(flip)","true",label=pid)
    ripl.infer(5)
    
  for i in reversed(range(10,20)):
    pid = "pid%d" % i
    ripl.forget(pid)
    ripl.infer(5)
            
