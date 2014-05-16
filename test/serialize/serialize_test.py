import unittest
from nose import SkipTest
from testconfig import config

from venture.test.stats import statisticalTest, reportKnownDiscrete, reportSameDiscrete
from venture.test.config import get_ripl, collectStateSequence

from venture.lite.serialize import Serializer

class TestSerialize(unittest.TestCase):

    def test_serialize(self):
        if config['get_ripl'] == 'puma':
            raise SkipTest("Can't serialize Puma traces. Issue: https://app.asana.com/0/9277419963067/12193842156124")
        v = get_ripl()
        v.assume('is_tricky', '(flip 0.2)')
        v.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
        v.assume('flip_coin', '(lambda () (flip theta))')
        v.observe('(flip_coin)', 'true')

        v.infer(1)
        result1 = v.predict('is_tricky')

        trace = v.sivm.core_sivm.engine.getDistinguishedTrace()
        serialized = Serializer().serialize_trace(trace, None)
        newtrace, _ = Serializer().deserialize_trace(serialized)
        v.sivm.core_sivm.engine.traces = [newtrace]
        result2 = v.predict('is_tricky')

        self.assertTrue(isinstance(serialized, dict))
        self.assertTrue(isinstance(newtrace, type(trace)))
        self.assertEqual(result1, result2)

    def test_serialize_ripl(self):
        if config['get_ripl'] == 'puma':
            raise SkipTest("Can't serialize Puma traces. Issue: https://app.asana.com/0/9277419963067/12193842156124")
        v1 = get_ripl()
        v1.assume('is_tricky', '(flip 0.2)')
        v1.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
        v1.assume('flip_coin', '(lambda () (flip theta))')
        v1.observe('(flip_coin)', 'true')

        v1.infer(1)
        result1 = v1.predict('is_tricky')

        v1.save('/tmp/serialized.ripl')

        v2 = get_ripl()
        v2.load('/tmp/serialized.ripl')
        result2 = v2.predict('is_tricky')

        self.assertEqual(result1, result2)

        text1 = v1.get_text(1)
        text2 = v2.get_text(1)
        self.assertEqual(text1, text2)

    @statisticalTest
    def test_serialize_forget(self):
        if config['get_ripl'] == 'puma':
            raise SkipTest("Can't serialize Puma traces. Issue: https://app.asana.com/0/9277419963067/12193842156124")
        v1 = get_ripl()
        v1.assume('is_tricky', '(flip 0.2)')
        v1.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
        v1.assume('flip_coin', '(lambda () (flip theta))')
        for i in range(10):
            v1.observe('(flip_coin)', 'true', label='y{}'.format(i))

        v1.infer(0)
        v1.save('/tmp/serialized.ripl')

        v2 = get_ripl()
        v2.load('/tmp/serialized.ripl')

        for i in range(10):
            v2.forget('y{}'.format(i))

        v2.predict('is_tricky', label='pid')

        samples = collectStateSequence(v2, 'pid')
        ans = [(False, 0.8), (True, 0.2)]
        return reportKnownDiscrete(ans, samples)

    @statisticalTest
    def _test_serialize_program(self, program, label):
        if config['get_ripl'] == 'puma':
            raise SkipTest("Can't serialize Puma traces. Issue: https://app.asana.com/0/9277419963067/12193842156124")
        v1 = get_ripl()
        program(v1)

        v1.infer(0)
        v1.save('/tmp/serialized.ripl')

        v2 = get_ripl()
        v2.load('/tmp/serialized.ripl')

        r1 = collectStateSequence(v1, label)
        r2 = collectStateSequence(v2, label)
        return reportSameDiscrete(r1, r2)

    def test_serialize_mem(self):
        def program(v):
            v.assume('coin', '(mem (lambda (x) (beta 1.0 1.0)))')
            v.assume('flip_coin', '(lambda (x) (flip (coin x)))')
            for i in range(10):
                v.observe('(flip_coin 0)', 'true')
            v.predict('(flip_coin 0)', label='pid')
        self._test_serialize_program(program, 'pid')

    def test_serialize_aaa(self):
        def make_program(maker, hyper):
            def program(v):
                v.assume('a', hyper)
                v.assume('f', '({0} a a)'.format(maker))
                v.predict('(f)', label='pid')
                for _ in range(20):
                    v.observe('(f)', 'true')
            return program
        for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
            for hyper in ['1.0', '(normal 1.0 0.1)']:
                self._test_serialize_program(make_program(maker, hyper), 'pid')

    def test_serialize_latents(self):
        def program(v):
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
            v.predict('(f 6)', label='pid')
        self._test_serialize_program(program, 'pid')
