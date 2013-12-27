# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
from libtrace import Trace
import pdb
from venture.exception import VentureException

# Thin wrapper around cxx Trace
# TODO: merge with CoreSivmCxx?

class SIVM:

    def __init__(self):
        self.directiveCounter = 0
        self.directives = {}
        self.trace = Trace()

    def nextBaseAddr(self):
        self.directiveCounter += 1
        return self.directiveCounter

    def desugarLambda(self,datum):
      if type(datum) is list and type(datum[0]) is dict and datum[0]["value"] == "lambda":
        ids = [{"type" : "symbol","value" : "quote"}] + [datum[1]]
        body = [{"type" : "symbol","value" : "quote"}] + [self.desugarLambda(datum[2])]
        return [{"type" : "symbol", "value" : "make_csp"},ids,body]
      elif type(datum) is list: return [self.desugarLambda(d) for d in datum]
      else: return datum

    def assume(self,id,datum):
        baseAddr = self.nextBaseAddr()

        exp = self.desugarLambda(datum)
#        print exp
        self.trace.eval(baseAddr,exp);
        self.trace.bindInGlobalEnv(id,baseAddr)

        self.directives[self.directiveCounter] = ["assume",id,datum]

        return (self.directiveCounter,self.trace.extractValue(baseAddr))
        
    def predict(self,datum):
        baseAddr = self.nextBaseAddr()
        self.trace.eval(baseAddr,self.desugarLambda(datum))

        self.directives[self.directiveCounter] = ["predict",datum]

        return (self.directiveCounter,self.trace.extractValue(baseAddr))

    def observe(self,datum,val):
        baseAddr = self.nextBaseAddr()
        self.trace.eval(baseAddr,self.desugarLambda(datum))
        logDensity = self.trace.observe(baseAddr,val)

        # TODO check for -infinity? Throw an exception?
        if logDensity == float("-inf"):
            raise VentureException("invalid_constraint", "Observe failed to constrain", expression=datum, value=val)
        self.directives[self.directiveCounter] = ["observe",datum,val]

        return self.directiveCounter

    def forget(self,directiveId):
        if directiveId not in self.directives:
            raise VentureException("invalid_argument", "Cannot forget a non-existent directive id", argument="directive_id", directive_id=directiveId)
        directive = self.directives[directiveId]
        if directive[0] == "assume":
            raise VentureException("invalid_argument", "Cannot forget an ASSUME directive", argument="directive_id", directive_id=directiveId)
        if directive[0] == "observe": self.trace.unobserve(directiveId)
        self.trace.uneval(directiveId)
        del self.directives[directiveId]
    
    def report_value(self,directiveId):
        if directiveId not in self.directives:
            raise VentureException("invalid_argument", "Cannot report a non-existent directive id", argument=directiveId)
        return self.trace.extractValue(directiveId)

    def clear(self):
        del self.trace
        self.directiveCounter = 0
        self.directives = {}
        self.trace = Trace()

    # This could be parameterized to call different inference programs.
    def infer(self,params=None):
        if params is None:
            params = {}

        if 'transitions' not in params:
            params['transitions'] = 1
        else:
            # FIXME: Kludge. If removed, test_infer (in python/test/ripl_test.py) fails, and if params are printed, you'll see a float for the number of transitions
            params['transitions'] = int(params['transitions'])

        if 'kernel' not in params:
            params['kernel'] = 'mh'
        if 'use_global_scaffold' not in params:
            params['use_global_scaffold'] = False

        if len(params.keys()) > 3:
            raise Exception("Invalid parameter dictionary passed to infer: " + str(params))

        #print "params: " + str(params)

        self.trace.infer(params)

    def logscore(self): return self.trace.getGlobalLogScore()

    def get_entropy_info(self):
      return { 'unconstrained_random_choices' : self.trace.numRandomChoices() }

    def get_seed(self):
        return self.trace.get_seed()

    def set_seed(self, seed):
        self.trace.set_seed(seed)
    
    def continuous_inference_status(self):
        return self.trace.continuous_inference_status()
    
    def start_continuous_inference(self, params):
        self.trace.start_continuous_inference(params)
    
    def stop_continuous_inference(self):
        self.trace.stop_continuous_inference()
    
    # TODO: Add methods to inspect/manipulate the trace for debugging and profiling
    
