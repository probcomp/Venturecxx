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
            v.observe('(flip_coin {})'.format(i), 'true', label='y{}'.format(i))

        v.infer(10)
        result1 = v.predict('is_tricky')

        trace = v.sivm.core_sivm.engine.trace
        serialized = Serializer().serialize_trace(trace, None)
        newtrace, _ = Serializer().deserialize_trace(serialized)
        v.sivm.core_sivm.engine.trace = newtrace
        result2 = v.predict('is_tricky')

        self.assertTrue(isinstance(serialized, dict))
        self.assertTrue(isinstance(newtrace, type(trace)))
        self.assertEqual(result1, result2)

        for i in range(10):
            v.forget('y{}'.format(i))
        v.infer(10)
        v.predict('is_tricky')

    def test_serialize_ripl(self):
        v1 = make_lite_church_prime_ripl()
        v1.assume('is_tricky', '(flip 0.2)')
        v1.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
        v1.assume('flip_coin', '(mem (lambda (x) (flip theta)))')
        for i in range(10):
            v1.observe('(flip_coin {})'.format(i), 'true', label='y{}'.format(i))

        v1.infer(10)
        result1 = v1.predict('is_tricky')

        v1.save('/tmp/serialized.ripl')

        v2 = make_lite_church_prime_ripl()
        v2.load('/tmp/serialized.ripl')
        result2 = v2.predict('is_tricky')

        self.assertEqual(result1, result2)

        text1 = v1.get_text(1)
        text2 = v2.get_text(1)
        self.assertEqual(text1, text2)

        for i in range(10):
            v2.forget('y{}'.format(i))
        v2.infer(10)
        v2.predict('is_tricky')
