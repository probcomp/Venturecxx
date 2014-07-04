from venture.test.config import get_ripl

def testForgetContinuousInference1():
  ripl = get_ripl()
  for i in range(10):
    pid = "pid%d" % i
    ripl.predict("(flip)",label=pid)
    ripl.forget(pid)

def testForgetContinuousInference2():
  ripl = get_ripl()
  for i in range(10):
    pid = "pid%d" % i
    ripl.predict("(flip)",label=pid)

  for i in range(10):
    pid = "pid%d" % i
    ripl.forget(pid)

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
            
