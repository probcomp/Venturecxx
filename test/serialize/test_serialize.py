# Copyright (c) 2014, 2015, 2016 MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import tempfile

from nose import SkipTest
from nose.tools import eq_

from venture.lite import builtin
from venture.test.config import collectStateSequence
from venture.test.config import default_num_transitions_per_sample
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import reportSameDiscrete
from venture.test.stats import statisticalTest

def _test_serialize_program(v, label, action):
    engine = v.sivm.core_sivm.engine

    if action == 'serialize':
        trace1 = engine.getDistinguishedTrace()
        serialized = trace1.dump()
        trace2 = engine.model.restore_trace(serialized)
        assert isinstance(serialized, tuple)
        assert len(serialized) == 3
        assert isinstance(serialized[0], list)
        assert all(isinstance(x, dict) for x in serialized[0])
        assert isinstance(serialized[1], dict) # Mapping directive ids to directives
        for (key,val) in serialized[1].iteritems():
            assert isinstance(key, int)
            assert isinstance(val, list)
        assert isinstance(serialized[2], set) # Names of bound foreign sps
        for elem in serialized[2]:
            assert isinstance(elem, basestring)
        assert isinstance(trace2, type(trace1))
        assert isinstance(trace2.trace, type(trace1.trace))
    elif action == 'copy':
        trace1 = engine.getDistinguishedTrace()
        trace2 = engine.model.copy_trace(trace1)
        assert isinstance(trace2, type(trace1))
        assert isinstance(trace2.trace, type(trace1.trace))
    elif action == 'convert_puma':
        try:
            from venture.puma import trace
        except ImportError:
            raise SkipTest("Puma backend does not appear to be installed")
        trace1 = engine.getDistinguishedTrace()
        engine.to_puma()
        trace2 = engine.getDistinguishedTrace()
        assert 'venture.puma' in trace2.trace.__module__
    elif action == 'convert_lite':
        trace1 = engine.getDistinguishedTrace()
        engine.to_lite()
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
    @statisticalTest
    def check(action, seed):
        v = get_ripl(seed=seed)
        v.assume('is_tricky', '(flip 0.2)')
        v.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
        v.assume('flip_coin', '(lambda () (flip theta))')
        v.observe('(flip_coin)', 'true')
        v.predict('is_tricky', label='pid')
        return _test_serialize_program(v, 'pid', action)
    for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
        yield check, action

@gen_on_inf_prim("mh") # Easy to generalize but little testing value
def test_serialize_mem():
    @statisticalTest
    def check(action, seed):
        v = get_ripl(seed=seed)
        v.assume('coin', '(mem (lambda (x) (beta 1.0 1.0)))')
        v.assume('flip_coin', '(lambda (x) (flip (coin x)))')
        for _ in range(10):
            v.observe('(flip_coin 0)', 'true')
        v.predict('(flip_coin 0)', label='pid')
        return _test_serialize_program(v, 'pid', action)
    for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
        yield check, action

@gen_on_inf_prim("mh") # Easy to generalize but little testing value
def test_serialize_closure():
    @statisticalTest
    def check(action, seed):
        v = get_ripl(seed=seed)
        v.assume('make_coin', '(lambda (p) (lambda () (flip p)))')
        v.assume('flip_coin', '(make_coin (beta 1.0 1.0))')
        for _ in range(10):
            v.observe('(flip_coin)', 'true')
        v.predict('(flip_coin)', label='pid')
        return _test_serialize_program(v, 'pid', action)
    for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
        yield check, action

@gen_on_inf_prim("mh") # Easy to generalize but little testing value
def test_serialize_aaa():
    @statisticalTest
    def check_beta_bernoulli(maker, action, seed):
        if maker == "make_uc_beta_bernoulli" and action in ['serialize', 'convert_lite', 'convert_puma']:
            raise SkipTest("Cannot convert BetaBernoulliSP to a stack dictionary. Issue: https://app.asana.com/0/9277420529946/16149214487233")
        v = get_ripl(seed=seed)
        v.assume('a', '(normal 10.0 1.0)')
        v.assume('f', '({0} a a)'.format(maker))
        v.predict('(f)', label='pid')
        for _ in range(20):
            v.observe('(f)', 'true')
        return _test_serialize_program(v, 'pid', action)
    for maker in ["make_beta_bernoulli","make_uc_beta_bernoulli"]:
        for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
            yield check_beta_bernoulli, maker, action

    @statisticalTest
    def check_crp(maker, action, seed):
        v = get_ripl(seed=seed)
        v.assume('a', '(gamma 1.0 1.0)')
        v.assume('f', '({0} a)'.format(maker))
        v.predict('(f)', label='pid')
        for _ in range(10):
            v.observe('(f)', 'atom<1>')
            v.observe('(f)', 'atom<2>')
            v.observe('(f)', 'atom<3>')
        return _test_serialize_program(v, 'pid', action)
    for maker in ["make_crp"]:
        for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
            yield check_crp, maker, action

    @statisticalTest
    def check_cmvn(maker, action, seed):
        raise SkipTest("reportSameDiscrete doesn't work with numpy.ndarray")
        v = get_ripl(seed=seed)
        v.assume('m0','(array 5.0 5.0)')
        v.assume('k0','7.0')
        v.assume('v0','11.0')
        v.assume('S0','(matrix (array (array 13.0 0.0) (array 0.0 13.0)))')
        v.assume('f','({0} m0 k0 v0 S0)'.format(maker))
        v.predict('(f)', label='pid')
        return _test_serialize_program(v, 'pid', action)
    for maker in ["make_niw_normal"]:
        for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
            yield check_cmvn, maker, action

@gen_on_inf_prim("mh") # Easy to generalize but little testing value
def test_serialize_latents():
    @statisticalTest
    def check(action, seed):
        raise SkipTest("Cannot serialize latents https://github.com/probcomp/Venturecxx/issues/342")
        v = get_ripl(seed=seed)
        v.assume('f','''\
    (make_lazy_hmm
     (simplex 0.5 0.5)
     (matrix (array (array 0.7 0.3)
                   (array 0.3 0.7)))
     (matrix (array (array 0.9 0.2)
                   (array 0.1 0.8))))
    ''')
        v.observe('(f 1)', 'integer<0>')
        v.observe('(f 2)', 'integer<0>')
        v.observe('(f 3)', 'integer<1>')
        v.observe('(f 4)', 'integer<0>')
        v.observe('(f 5)', 'integer<0>')
        v.predict('(f 6)', label='pid')
        return _test_serialize_program(v, 'pid', action)
    for action in ['copy', 'serialize', 'convert_puma', 'convert_lite']:
        yield check, action

@gen_on_inf_prim("mh")
def test_serialize_ripl():
    def check(mode):
        with tempfile.NamedTemporaryFile(prefix='serialized.ripl') as f:
            v1 = get_ripl()
            v1.assume('is_tricky', '(flip 0.2)')
            v1.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
            v1.assume('flip_coin', '(lambda () (flip theta))')
            v1.observe('(flip_coin)', 'true')

            v1.infer(1)
            result1 = v1.predict('theta', label='theta_prediction')

            call(v1, 'save', f.name, mode)

            v2 = get_ripl()
            call(v2, 'load', f.name, mode)
            result2 = v2.report('theta_prediction')
            result3 = v2.predict('theta')

            assert result1 == result2 and result1 == result3

            text1 = v1.get_text(1)
            text2 = v2.get_text(1)
            assert text1 == text2
    def call(ripl, save_or_load, filename, mode):
        if mode == 'ripl':
            if save_or_load == 'save':
                ripl.save(filename)
            elif save_or_load == 'load':
                ripl.load(filename)
        elif mode == 'inference_language':
            ripl.infer('(%s_model "%s")' % (save_or_load, filename))
    for mode in ['ripl', 'inference_language']:
        yield check, mode

@on_inf_prim("mh") # Easy to generalize but little testing value
@statisticalTest
def test_serialize_forget(seed):
    with tempfile.NamedTemporaryFile(prefix='serialized.ripl') as f:
        v1 = get_ripl(seed=seed)
        v1.assume('is_tricky', '(flip 0.2)')
        v1.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
        v1.assume('flip_coin', '(lambda () (flip theta))')
        for i in range(10):
            v1.observe('(flip_coin)', 'true', label='y{}'.format(i))

        v1.infer("(incorporate)")
        v1.save(f.name)

        v2 = get_ripl()
        v2.load(f.name)

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
        with tempfile.NamedTemporaryFile(prefix='serialized.ripl') as f:
            v.save(f.name)
            v.load(f.name)
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
    with tempfile.NamedTemporaryFile(prefix='serialized.ripl') as f:
        v.save(f.name)
        v.load(f.name)

@gen_on_inf_prim("resample")
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
    v.bind_foreign_sp('test_sym_dir_cat', builtins['make_sym_dir_cat'])
    test_binomial_result = 1
    test_sym_dir_result = {'alpha': 1.0, 'counts': [0], 'n': 1, 'type': 'sym_dir_cat'}
    eq_(v.sample('(test_binomial 1 1)'), test_binomial_result)
    eq_(v.sample('(test_sym_dir_cat 1 1)'), test_sym_dir_result)
    engine = v.sivm.core_sivm.engine
    dumped = engine.model.retrieve_dump(0)
    restored = engine.model.restore_trace(dumped)
    engine.model.create_trace_pool([restored])
    # Make sure that the restored trace still has the foreign SP's
    eq_(v.sample('(test_binomial 1 1)'), test_binomial_result)
    eq_(v.sample('(test_sym_dir_cat 1 1)'), test_sym_dir_result)
