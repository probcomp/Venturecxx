from venture.lite.psp import DeterministicPSP
from venture.lite.sp import SP, VentureSPRecord
from venture.lite.lkernel import SimulationAAALKernel
from venture.lite.env import VentureEnvironment
from venture.lite.request import Request,ESR
from venture.lite.address import emptyAddress
from venture.lite.builtin import no_request
import venture.lite.types as t
from venture.lite.gp import GPSP, GPSPAux
import collections

class MakeGPMSPOutputPSP(DeterministicPSP):
    """"
    This class (except its simulate method) is based on DeterministicAAAMakerPSP.
    """
    def __init__(self):
        # We need to keep the aux ourselves, because proposals to the arguments
        # of this function will cause f_compute and f_emu to be re-created,
        # with initially blank auxs that we need to replace with our stored
        # aux.
        self.shared_aux = GPSPAux(collections.OrderedDict())

    def simulate(self, args):
        f_node = args.operandNodes[0]
        prior_mean_function = args.operandValues()[1]
        prior_covariance_function = args.operandValues()[2]
        f_compute = VentureSPRecord(
                SP(GPMComputerRequestPSP(f_node), GPMComputerOutputPSP()))
        # Prior mean is fixed to zero, because the current GP implementation
        # assumes this
        f_emu = VentureSPRecord(GPSP(prior_mean_function, prior_covariance_function))
        f_emu.spAux = self.shared_aux
        f_compute.spAux = self.shared_aux
        # TODO ways to get_Xseen and get_Yseen? maybe this belongs in the
        # inference side
        return t.pythonListToVentureList([f_compute, f_emu])

    def childrenCanAAA(self): return True
    def getAAALKernel(self): return GPMDeterministicMakerAAALKernel(self)

class GPMDeterministicMakerAAALKernel(SimulationAAALKernel):
    """
    This is based on DeterministicMakerAAALKernel.
    """
    def __init__(self,makerPSP): self.makerPSP = makerPSP
    def simulate(self, _trace, args):
        ## We ain't assuming that the output is an SPRecord.
        ## In fact, it should be a list of two SPRecords.
        ## And their auxs are already attached.
        # spRecord = self.makerPSP.simulate(args)
        # spRecord.spAux = args.madeSPAux
        # return spRecord

        ## So the new version is:
        return self.makerPSP.simulate(args)
    def weight(self, _trace, newValue, _args):
        # Using newValue.spAux here because args.madeSPAux is liable to be
        # None when detaching. This has something to do with when the Args
        # object is constructed relative to other things that happen
        # during detach/regen. TODO: fix it so that this code is less
        # fragile.

        (_f_compute, f_emu) = newValue.asPythonList()
        answer = f_emu.sp.outputPSP.logDensityOfCounts(self.makerPSP.shared_aux)
        # print "gpmem LKernel weight = %s" % answer
        return answer

gpmemSP = no_request(MakeGPMSPOutputPSP())

# TODO treat this as not necessarily random?
class GPMComputerRequestPSP(DeterministicPSP):
    def __init__(self, f_node):
        self.f_node = f_node

    def simulate(self, args):
        id = str(args.operandValues())
        exp = ["gpmemmedSP"] + [["quote",val] for val in args.operandValues()]
        env = VentureEnvironment(None,["gpmemmedSP"],[self.f_node])
        return Request([ESR(id,exp,emptyAddress,env)])

# TODO Perhaps this could subclass ESRRefOutputPSP to correctly handle
# back-propagation?
class GPMComputerOutputPSP(DeterministicPSP):
    def simulate(self,args):
        assert len(args.esrNodes()) ==  1
        return args.esrValues()[0]

    def incorporate(self, value, args):
        # TODO maybe best to just call on someone else's incorporate method
        # instead? idk
        x = args.operandValues()[0].getNumber()
        y = value.getNumber()
        args.spaux().samples[x] = y

    def unincorporate(self, value, args):
        x = args.operandValues()[0].getNumber()
        samples = args.spaux().samples
        if x in samples:
            del samples[x]

