from venture.test.config import get_ripl
import venture.test.timing as timing

def test_double_recursion():
  def test(n):
    ripl = get_ripl()
    ripl.assume('a', '(normal 0 1)')
    ripl.assume('f', '''(mem (lambda (n)
         (if (= n 0) 0
             (+ a (f (- n 1)) (f (- n 1))))))''')
    ripl.predict('(f %d)' % n)
    ripl.infer(1) # Warm up the system s.t. subsequent timings are ok
    def thunk():
      ripl.infer(10)
    return thunk

  timing.assertLinearTime(test, verbose=True)
