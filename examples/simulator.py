import operator
import functools
#
from venture.venturemagics.ip_parallel import MRipl


class Simulator(object):
    # where to run diagnostics?
    def __init__(self, program, observe_strs_list, sample_strs_list,
            N_mripls, backend, infer_args):
        self.observe_strs_list = observe_strs_list
        self.sample_strs_list = sample_strs_list
        self.mripl = MRipl(N_mripls, backend=backend)
        self.next_i = 0
        self.infer_args = infer_args
        self.program = program
        #
        self.mripl.execute_program(self.program)
        pass

    def step(self, infer_args=None):
        infer_args = first_non_none(infer_args, self.infer_args)
        observe_strs, sample_strs = self._get_next_observe_and_sample_str()
        self._observe(observe_strs)
        self._infer(infer_args)
        samples = self._sample(sample_strs)
        return samples

    def _get_next_observe_and_sample_str(self):
        observe_str = self.observe_strs_list[self.next_i]
        sample_str = self.sample_strs_list[self.next_i]
        self.next_i += 1
        return observe_str, sample_str

    def _observe(self, observe_strs):
        print 'observing: %s' % observe_strs
        _observe_datum = functools.partial(observe_datum, self.mripl)
        return map(_observe_datum, observe_strs)

    def _infer(self, infer_args):
        if not isinstance(infer_args, (list, tuple)):
            infer_args = [infer_args]
            pass
        def _do_infer(infer_arg):
            print "infering: %s" % infer_arg
            ret_val = self.mripl.infer(infer_arg)
            print "done infering: %s" % infer_arg
            return ret_val
        return map(_do_infer, infer_args)

    def _sample(self, sample_strs):
        munge_sample = lambda sample: reduce(operator.add, zip(*sample))
        print 'sampling: %s' % sample_strs
        raw_samples = map(self.mripl.sample, sample_strs)
        samples = map(munge_sample, raw_samples)
        return samples

    def plot(self):
        print "Plotting not implemented"
        pass


def printif(boolean, to_print):
    if boolean:
        print to_print
        pass
    return

def observe_datum(ripl, (observe_str, value), verbose=False):
    print_str = "ripl.observe(%s, %s)" % (observe_str, value)
    printif(verbose, print_str)
    return ripl.observe(observe_str, value)

def first_non_none(*args):
    my_or = lambda x, y: x if x is not None else y
    return reduce(my_or, args)
