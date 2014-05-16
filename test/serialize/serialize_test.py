import unittest
from nose import SkipTest

from venture.lite.serialize import Serializer
from venture.shortcuts import make_lite_church_prime_ripl

class TestSerialize(unittest.TestCase):

    def test_serialize(self):
        v = make_lite_church_prime_ripl()
        v.assume('is_tricky', '(flip 0.2)')
        v.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
        v.assume('flip_coin', '(lambda () (flip theta))')
        for i in range(10):
            v.observe('(flip_coin)', 'true', label='y{}'.format(i))

        v.infer(10)
        result1 = v.predict('is_tricky')

        trace = v.sivm.core_sivm.engine.getDistinguishedTrace()
        serialized = Serializer().serialize_trace(trace, None)
        newtrace, _ = Serializer().deserialize_trace(serialized)
        # TODO this is awkward
        # if it were an acceptable thing to do in general, we might have
        # setDistinguishedTrace(newtrace)
        v.sivm.core_sivm.engine.traces[0] = newtrace
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
        v1.assume('flip_coin', '(lambda () (flip theta))')
        for i in range(10):
            v1.observe('(flip_coin)', 'true', label='y{}'.format(i))

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

    def _test_serialize_program(self, execute_program, do_predict):
        v1 = make_lite_church_prime_ripl()
        execute_program(v1)

        v1.infer(10)
        v1.save('/tmp/serialized.ripl')

        v2 = make_lite_church_prime_ripl()
        v2.load('/tmp/serialized.ripl')

        r1 = do_predict(v1)
        r2 = do_predict(v2)
        self.assertEqual(r1, r2)

    def test_serialize_mem(self):
        def execute_program(v):
            v.assume('theta', '(beta 1.0 1.0)')
            v.assume('f', '(mem (lambda (x) (flip theta)))')
            v.predict('(f (flip))')
            for _ in range(10):
                v.observe('(f (flip))', 'true')
        def do_predict(v):
            return v.predict('(f)')

    def test_serialize_aaa(self):
        def execute_program1(v):
            v.assume('f', '(make_beta_bernoulli 10.0 10.0)')
            v.predict('(f)')
            for _ in range(20):
                v.observe('(f)', 'true')
        def execute_program2(v):
            v.assume('a', '(normal 10.0 1.0)')
            v.assume('f', '(make_beta_bernoulli a a)')
            v.predict('(f)')
            for _ in range(20):
                v.observe('(f)', 'true')
        def do_predict(v):
            return v.predict('(f)')
        self._test_serialize_program(execute_program1, do_predict)
        self._test_serialize_program(execute_program2, do_predict)

    def test_serialize_latents(self):
        def execute_program(v):
            v.assume('f','''\
(make_lazy_hmm
 (simplex 0.5 0.5)
 (matrix (array (array 0.7 0.3)
               (array 0.3 0.7)))
 (matrix (array (array 0.9 0.2)
               (array 0.1 0.8))))
''')
            v.observe('(f 1)', 'atom<0>')
            v.observe('(f 2)', 'atom<0>')
            v.observe('(f 3)', 'atom<1>')
            v.observe('(f 4)', 'atom<0>')
            v.observe('(f 5)', 'atom<0>')
        def do_predict(v):
            return v.predict('(f 6)')
        self._test_serialize_program(execute_program, do_predict)
