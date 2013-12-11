from psp import PSP

class MakeCSPOutputPSP(PSP):
  def simulate(self,args):
    (ids,exp,env) = args.operandValues[0:4]
    return SP(CSPRequestPSP(ids,exp,env),ESRRefOutputPSP())

class CSPRequestPSP(PSP):
  def simulate(self,args):
    extendedEnv = Env(self.env,ids,args.operandNodes)
    return ([(args.node,self.exp,extendedEnv)],[])
    
