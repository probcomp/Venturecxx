import unittest
from nose import SkipTest
from testconfig import config

from venture.test.stats import statisticalTest, reportKnownDiscrete, reportSameDiscrete
from venture.test.config import get_ripl, collectStateSequence, defaultKernel

from venture.lite.serialize import dump_trace, restore_trace

def test_serialize():
    if config['get_ripl'] == 'puma':
        raise SkipTest("Puma to Lite conversion not yet implemented. Issue: https://app.asana.com/0/13001976276959/12193842156124")
    v = get_ripl()
    v.assume('is_tricky', '(flip 0.2)')
    v.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
    v.assume('flip_coin', '(lambda () (flip theta))')
    v.observe('(flip_coin)', 'true')

    v.infer(1)
    result1 = v.predict('is_tricky')

    engine = v.sivm.core_sivm.engine
    trace = engine.getDistinguishedTrace()
    serialized = dump_trace(trace, engine)
    newtrace = restore_trace(serialized, engine)
    engine.traces = [newtrace]
    result2 = v.predict('is_tricky')

    assert isinstance(serialized, list)
    assert isinstance(newtrace, type(trace))
    assert result1 == result2

def test_serialize_ripl():
    if config['get_ripl'] == 'puma':
        raise SkipTest("Puma to Lite conversion not yet implemented. Issue: https://app.asana.com/0/13001976276959/12193842156124")
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

    assert result1 == result2

    text1 = v1.get_text(1)
    text2 = v2.get_text(1)
    assert text1 == text2

@statisticalTest
def test_serialize_forget():
    if config['get_ripl'] == 'puma':
        raise SkipTest("Puma to Lite conversion not yet implemented. Issue: https://app.asana.com/0/13001976276959/12193842156124")
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
def _test_serialize_program(v, label):
    if config['get_ripl'] == 'puma':
        raise SkipTest("Puma to Lite conversion not yet implemented. Issue: https://app.asana.com/0/13001976276959/12193842156124")
    engine = v.sivm.core_sivm.engine

    trace1 = engine.getDistinguishedTrace()
    serialized = dump_trace(trace1, engine)
    trace2 = restore_trace(serialized, engine)

    engine.traces = [trace1]
    r1 = collectStateSequence(v, label)

    engine.traces = [trace2]
    r2 = collectStateSequence(v, label)

    return reportSameDiscrete(r1, r2)

@statisticalTest
def _test_stop_and_copy(v, label):
    if config['get_ripl'] == 'puma':
        raise SkipTest("Fails due to a mystery bug in Puma stop_and_copy. Issue: https://app.asana.com/0/11127829865276/13039650533872")
    engine = v.sivm.core_sivm.engine

    trace1 = engine.getDistinguishedTrace()
    trace2 = trace1.stop_and_copy(engine)

    engine.traces = [trace1]
    r1 = collectStateSequence(v, label)

    engine.traces = [trace2]
    r2 = collectStateSequence(v, label)

    return reportSameDiscrete(r1, r2)

def test_serialize_mem():
    v = get_ripl()
    v.assume('coin', '(mem (lambda (x) (beta 1.0 1.0)))')
    v.assume('flip_coin', '(lambda (x) (flip (coin x)))')
    for _ in range(10):
        v.observe('(flip_coin 0)', 'true')
    v.predict('(flip_coin 0)', label='pid')
    _test_stop_and_copy(v, 'pid')
    _test_serialize_program(v, 'pid')

def test_serialize_closure():
    v = get_ripl()
    v.assume('make_coin', '(lambda (p) (lambda () (flip p)))')
    v.assume('flip_coin', '(make_coin (beta 1.0 1.0))')
    for _ in range(10):
        v.observe('(flip_coin)', 'true')
    v.predict('(flip_coin)', label='pid')
    _test_stop_and_copy(v, 'pid')
    _test_serialize_program(v, 'pid')

def test_serialize_recursion():
    if config['get_ripl'] == 'puma':
        raise SkipTest("Puma to Lite conversion not yet implemented. Issue: https://app.asana.com/0/13001976276959/12193842156124")
    v = get_ripl()
    v.assume('f', '''
(mem (lambda (x)
  (normal
    (if (= x 0) 0
      (f (- x 1)))
    1)))
''')
    v.predict('(f 20)')
    try:
        # just make sure this doesn't crash
        v.save('/tmp/serialized.ripl')
        v.load('/tmp/serialized.ripl')
    except RuntimeError as e:
        assert 'maximum recursion depth exceeded' not in e.message
        raise

def test_serialize_aaa():
    def check_beta_bernoulli(maker):
        if maker == "make_uc_beta_bernoulli":
            raise SkipTest("Cannot convert BetaBernoulliSP to a stack dictionary. Issue: https://app.asana.com/0/13001976276959/13001976276981")
        if maker == "make_beta_bernoulli" and defaultKernel() == "rejection":
            raise SkipTest("Cannot rejection sample AAA procedure with unbounded log density of ocounts")
        v = get_ripl()
        v.assume('a', '(normal 10.0 1.0)')
        v.assume('f', '({0} a a)'.format(maker))
        v.predict('(f)', label='pid')
        for _ in range(20):
            v.observe('(f)', 'true')
        _test_stop_and_copy(v, 'pid')
        _test_serialize_program(v, 'pid')
    for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
        yield check_beta_bernoulli, maker

    def check_sym_dir_mult(maker):
        if maker == "make_uc_sym_dir_mult":
            raise SkipTest("Cannot convert DirMultSP to a stack dictionary. Issue: https://app.asana.com/0/13001976276959/13001976276981")
        v = get_ripl()
        v.assume('a', '(normal 10.0 1.0)')
        v.assume('f', '({0} a 4)'.format(maker))
        v.predict('(f)', label='pid')
        for _ in range(10):
            v.observe('(f)', 'atom<0>')
            v.observe('(f)', 'atom<1>')
        _test_stop_and_copy(v, 'pid')
        _test_serialize_program(v, 'pid')
    for maker in ["make_sym_dir_mult","make_uc_sym_dir_mult"]:
        yield check_sym_dir_mult, maker

    def check_crp(maker):
        if defaultKernel() == "rejection":
            raise SkipTest("Cannot rejection sample AAA procedure with unbounded log density of counts")
        v = get_ripl()
        v.assume('a', '(gamma 1.0 1.0)')
        v.assume('f', '({0} a)'.format(maker))
        v.predict('(f)', label='pid')
        for _ in range(10):
            v.observe('(f)', 'atom<1>')
            v.observe('(f)', 'atom<2>')
            v.observe('(f)', 'atom<3>')
        _test_stop_and_copy(v, 'pid')
        _test_serialize_program(v, 'pid')
    for maker in ["make_crp"]:
        yield check_crp, maker

    def check_cmvn(maker):
        raise SkipTest("reportSameDiscrete doesn't work with numpy.ndarray")
        v = get_ripl()
        v.assume('m0','(array 5.0 5.0)')
        v.assume('k0','7.0')
        v.assume('v0','11.0')
        v.assume('S0','(matrix (array (array 13.0 0.0) (array 0.0 13.0)))')
        v.assume('f','({0} m0 k0 v0 S0)'.format(maker))
        v.predict('(f)', label='pid')
        _test_stop_and_copy(v, 'pid')
        _test_serialize_program(v, 'pid')
    for maker in ["make_cmvn"]:
        yield check_cmvn, maker

def test_serialize_latents():
    raise SkipTest("Cannot serialize latents")
    v = get_ripl()
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
    _test_stop_and_copy(v, 'pid')
    _test_serialize_program(v, 'pid')
