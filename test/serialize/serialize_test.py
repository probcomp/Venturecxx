import unittest

from venture.lite.serialize import Serializer
from venture.shortcuts import make_lite_church_prime_ripl

class TestSerialize(unittest.TestCase):

    def test_serialize(self):
        v = make_lite_church_prime_ripl()
        v.assume('is_tricky', '(flip 0.2)')
        v.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
        v.assume('flip_coin', '(mem (lambda (x) (flip theta)))')
        for i in range(10):
            v.observe('(flip_coin {})'.format(i), 'true')

        v.infer(10)
        result1 = v.predict('is_tricky')

        trace = v.sivm.core_sivm.engine.trace
        serialized = Serializer().serialize_trace(trace)
        newtrace = Serializer().deserialize_trace(serialized)
        v.sivm.core_sivm.engine.trace = newtrace
        result2 = v.predict('is_tricky')

        self.assertTrue(isinstance(serialized, dict))
        self.assertTrue(isinstance(newtrace, type(trace)))
        self.assertEqual(result1, result2)

        for i in range(10, 20):
            v.observe('(flip_coin {})'.format(i), 'false')
        v.infer(10)
        v.predict('is_tricky')
