from nose import SkipTest
from nose.tools import eq_
from testconfig import config

from venture.test.stats import statisticalTest, reportKnownDiscrete, reportSameDiscrete
from venture.test.config import get_ripl, collectStateSequence, on_inf_prim, default_num_transitions_per_sample, gen_on_inf_prim
from venture.lite import builtin
from venture.lite.builtin import binaryNum

@statisticalTest
def _test_serialize_program(v, label, action):
    engine = v.sivm.core_sivm.engine

    if action == 'serialize':
        trace1 = engine.getDistinguishedTrace()
        serialized = trace1.dump()
        trace2 = engine.model.restore_trace(serialized)
        assert isinstance(serialized, tuple)
        assert len(serialized) == 2
        assert isinstance(serialized[0], list)
        assert all(isinstance(x, dict) for x in serialized[0])
        assert isinstance(serialized[1], dict) # Mapping directive ids to directives
        for (key,val) in serialized[1].iteritems():
            assert isinstance(key, int)
            assert isinstance(val, list)
        assert isinstance(trace2, type(trace1))
        assert isinstance(trace2.trace, type(trace1.trace))
    elif action == 'copy':
        trace1 = engine.getDistinguishedTrace()
        trace2 = engine.model.copy_trace(trace1)
        assert isinstance(trace2, type(trace1))
        assert isinstance(trace2.trace, type(trace1.trace))
    elif action == 'convert_puma':
        trace1 = engine.getDistinguishedTrace()
        engine = engine.to_puma()
        trace2 = engine.getDistinguishedTrace()
        assert 'venture.puma' in trace2.trace.__module__
    elif action == 'convert_lite':
        trace1 = engine.getDistinguishedTrace()
        engine = engine.to_lite()
        trace2 = engine.getDistinguishedTrace()
        assert 'venture.lite' in trace2.trace.__module__
    else:
        assert False

    infer = "(mh default one %s)" % default_num_transitions_per_sample()
    engine.model.create_trace_pool([trace2])
    r2 = collectStateSequence(v, label, infer=infer)

    engine.model.create_trace_pool([trace1])
    r1 = collectStateSequence(v, label, infer=infer)

    return reportSameDiscrete(r1, r2)

@gen_on_inf_prim("mh") # Easy to generalize but little testing value
def test_serialize_basic():
    def check(action):
        v = get_ripl()
        v.assume('is_tricky', '(flip 0.2)')
        v.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
        v.assume('flip_coin', '(lambda () (flip theta))')
        v.observe('(flip_coin)', 'true')
        v.predict('is_tricky', label='pid')
        _test_serialize_program(v, 'pid', action)
    for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
        yield check, action

@gen_on_inf_prim("mh") # Easy to generalize but little testing value
def test_serialize_mem():
    def check(action):
        v = get_ripl()
        v.assume('coin', '(mem (lambda (x) (beta 1.0 1.0)))')
        v.assume('flip_coin', '(lambda (x) (flip (coin x)))')
        for _ in range(10):
            v.observe('(flip_coin 0)', 'true')
        v.predict('(flip_coin 0)', label='pid')
        _test_serialize_program(v, 'pid', action)
    for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
        yield check, action

@gen_on_inf_prim("mh") # Easy to generalize but little testing value
def test_serialize_closure():
    def check(action):
        v = get_ripl()
        v.assume('make_coin', '(lambda (p) (lambda () (flip p)))')
        v.assume('flip_coin', '(make_coin (beta 1.0 1.0))')
        for _ in range(10):
            v.observe('(flip_coin)', 'true')
        v.predict('(flip_coin)', label='pid')
        _test_serialize_program(v, 'pid', action)
    for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
        yield check, action

@gen_on_inf_prim("mh") # Easy to generalize but little testing value
def test_serialize_aaa():
    def check_beta_bernoulli(maker, action):
        if maker == "make_uc_beta_bernoulli" and action in ['serialize', 'convert_lite', 'convert_puma']:
            raise SkipTest("Cannot convert BetaBernoulliSP to a stack dictionary. Issue: https://app.asana.com/0/9277420529946/16149214487233")
        elif action == 'copy' and config['get_ripl'] == 'puma':
            raise SkipTest("Fails due to a mystery bug in Puma stop_and_copy. Issue: https://app.asana.com/0/11127829865276/13039650533872")
        v = get_ripl()
        v.assume('a', '(normal 10.0 1.0)')
        v.assume('f', '({0} a a)'.format(maker))
        v.predict('(f)', label='pid')
        for _ in range(20):
            v.observe('(f)', 'true')
        _test_serialize_program(v, 'pid', action)
    for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
        for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
            yield check_beta_bernoulli, maker, action

    def check_crp(maker, action):
        if action == 'copy' and config['get_ripl'] == 'puma':
            raise SkipTest("Fails due to a mystery bug in Puma stop_and_copy. Issue: https://app.asana.com/0/11127829865276/13039650533872")
        v = get_ripl()
        v.assume('a', '(gamma 1.0 1.0)')
        v.assume('f', '({0} a)'.format(maker))
        v.predict('(f)', label='pid')
        for _ in range(10):
            v.observe('(f)', 'atom<1>')
            v.observe('(f)', 'atom<2>')
            v.observe('(f)', 'atom<3>')
        _test_serialize_program(v, 'pid', action)
    for maker in ["make_crp"]:
        for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
            yield check_crp, maker, action

    def check_cmvn(maker, action):
        raise SkipTest("reportSameDiscrete doesn't work with numpy.ndarray")
        v = get_ripl()
        v.assume('m0','(array 5.0 5.0)')
        v.assume('k0','7.0')
        v.assume('v0','11.0')
        v.assume('S0','(matrix (array (array 13.0 0.0) (array 0.0 13.0)))')
        v.assume('f','({0} m0 k0 v0 S0)'.format(maker))
        v.predict('(f)', label='pid')
        _test_serialize_program(v, 'pid', action)
    for maker in ["make_cmvn"]:
        for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
            yield check_cmvn, maker, action

@gen_on_inf_prim("mh") # Easy to generalize but little testing value
def test_serialize_latents():
    def check(action):
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
        _test_serialize_program(v, 'pid', action)
    for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
        yield check, action

@on_inf_prim("mh")
def test_serialize_ripl():
    v1 = get_ripl()
    v1.assume('is_tricky', '(flip 0.2)')
    v1.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
    v1.assume('flip_coin', '(lambda () (flip theta))')
    v1.observe('(flip_coin)', 'true')

    v1.infer(1)
    result1 = v1.predict('theta', label='theta_prediction')

    v1.save('/tmp/serialized.ripl')

    v2 = get_ripl()
    v2.load('/tmp/serialized.ripl')
    result2 = v2.report('theta_prediction')
    result3 = v2.predict('theta')

    assert result1 == result2 and result1 == result3

    text1 = v1.get_text(1)
    text2 = v2.get_text(1)
    assert text1 == text2

@on_inf_prim("mh") # Easy to generalize but little testing value
@statisticalTest
def test_serialize_forget():
    v1 = get_ripl()
    v1.assume('is_tricky', '(flip 0.2)')
    v1.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
    v1.assume('flip_coin', '(lambda () (flip theta))')
    for i in range(10):
        v1.observe('(flip_coin)', 'true', label='y{}'.format(i))

    v1.infer("(incorporate)")
    v1.save('/tmp/serialized.ripl')

    v2 = get_ripl()
    v2.load('/tmp/serialized.ripl')

    for i in range(10):
        v2.forget('y{}'.format(i))

    v2.predict('is_tricky', label='pid')

    infer = "(mh default one %s)" % default_num_transitions_per_sample()
    samples = collectStateSequence(v2, 'pid', infer=infer)
    ans = [(False, 0.8), (True, 0.2)]
    return reportKnownDiscrete(ans, samples)

@on_inf_prim("none")
def test_serialize_recursion():
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

@on_inf_prim("none")
def test_serialize_repeatedly():
    v = get_ripl()
    v.assume('theta', '(beta 1 1)')
    v.observe('(flip theta)', 'true')
    v.infer("(incorporate)")
    # just make sure this doesn't crash
    v.save('/tmp/serialized.ripl')
    v.save('/tmp/serialized.ripl')

def test_foreign_sp():
    # make sure that foreign SP's are retained through serialization
    for mode in ['', '_serializing', '_threaded', '_thread_ser', '_multiprocess']:
        yield check_foreign_sp, mode

def check_foreign_sp(mode):
    v = get_ripl()
    builtins = builtin.builtInSPs()
    resample = '[INFER (resample{0} 1)]'.format(mode)
    v.execute_instruction(resample)
    v.bind_foreign_sp('test_binomial', builtins['binomial'])
    v.bind_foreign_sp('test_sym_dir_mult', builtins['make_sym_dir_mult'])
    test_binomial_result = 1
    test_sym_dir_result = {'alpha': 1.0, 'counts': [0], 'n': 1, 'type': 'sym_dir_mult'}
    eq_(v.sample('(test_binomial 1 1)'), test_binomial_result)
    eq_(v.sample('(test_sym_dir_mult 1 1)'), test_sym_dir_result)
    engine = v.sivm.core_sivm.engine
    dumped = engine.retrieve_dump(0)
    restored = engine.model.restore_trace(dumped)
    engine.model.create_trace_pool([restored])
    # Make sure that the restored trace still has the foreign SP's
    eq_(v.sample('(test_binomial 1 1)'), test_binomial_result)
    eq_(v.sample('(test_sym_dir_mult 1 1)'), test_sym_dir_result)
