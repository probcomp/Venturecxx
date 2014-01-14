class Engine:
  def __init__(self,jfunc_maker):
    self.jfunc_maker = jfunc_maker
    jfuncs = jfunc_maker()
    self.assume = jfuncs[0]
    self.predict = jfuncs[1]
    self.observe = jfuncs[2]
    self.report_value = jfuncs[3]
    self.infer = jfuncs[4]

  def reboot(self):
    jfuncs = self.jfunc_maker()
    self.assume = jfuncs[0]
    self.predict = jfuncs[1]
    self.observe = jfuncs[2]
    self.report_value = jfuncs[3]
    self.infer = jfuncs[4]

  def continuous_inference_status(self): return {"running" : False}
