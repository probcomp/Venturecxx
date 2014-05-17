import time
import math
from simulator import Simulator, observe_datum
# observe_datum(ripl, (observe_str, value), verbose=False):
#
from venture.shortcuts import make_puma_church_prime_ripl
from venture.shortcuts import make_lite_church_prime_ripl


N_mripls = 1
backend = 'puma'
N_infer = 100
N_steps = 4
local_ripl = None
if backend == 'lite':
    local_ripl = make_lite_church_prime_ripl()
    pass
else:
    local_ripl = make_puma_church_prime_ripl()
    pass


ripl = local_ripl

simulate_motion_str = """
(simulate_motion
  (quote pose)
  (quote control)
  (quote dt)
  )
  """
simulate_laser_str = """
(simulate_laser
  (quote pose)
  (quote map)
  )
  """
simulate_gps_str = """
(simulate_gps
  (quote pose)
  )
  """
predict_N = lambda predict_str: map(local_ripl.predict, [predict_str] * N_steps)
random_poses = predict_N(simulate_motion_str)
random_lasers = predict_N(simulate_laser_str)
random_gpss = predict_N(simulate_gps_str)
random_controls = [(.5, .5)] * N_steps
my_map = ripl.predict('(simulate_map)')


observe_laser_strs = [
        ('(get_laser %s)' % i, random_laser)
        for i, random_laser in enumerate(random_lasers)
        ]
observe_gps_strs = [
        ('(get_gps %s)' % i, random_gps)
        for i, random_gps in enumerate(random_gpss)
        ]
observe_control_strs = [
        ('(get_control %s)' % i, random_control)
        for i, random_control in enumerate(random_controls)
        ]

observe_strs_list = zip(
        # # breaks if you do this
        # observe_laser_strs,
        observe_gps_strs,
        # # breaks if you do this
        # observe_control_strs,
        )
sample_strs_list = [['(repeat (lambda()(get_pose %s)) 2)' % i] for i in range(N_steps)]



program_utils = """

[ASSUME repeat
  (lambda (thunk n)
    (if (= n 0)
      (list)
      (pair (thunk) (repeat thunk (- n 1) ) )
      )
    )
  ]

"""

program_assumes = """

[ASSUME get_map (mem (lambda () (simulate_map)))]

[ASSUME get_control
  (mem (lambda (t)
    (list
      (uniform_continuous 0 1)
      (uniform_continuous 0 1)
      )
    ))
]

[ASSUME get_pose
  (mem (lambda (t)
    (if (= t 0)
      (list 0 0 0)
      (simulate_motion
        (get_pose (- t 1))
        (get_control t)
        1
        )
      )
    ))
]

[ASSUME get_laser
  (mem (lambda (t)
    (simulate_laser
      (get_pose t)
      (get_map)
      )
    ))
]

[ASSUME get_gps
  (mem (lambda (t)
    (simulate_gps
      (get_pose t)
      )
    ))
]

    

"""

# In[ ]:



program = program_utils + program_assumes
print 'read program'
simulator = Simulator(program, observe_strs_list, sample_strs_list,
        N_mripls, backend, N_infer)
print 'initialized simulator'

local_ripl.execute_program(program)

#def _wrap_real(val):
#    return {"type":"real","value":val}
#def _wrap(val):
#    if isinstance(val, (list, tuple)):
#        print "MRipl.observe: converting to dict"
#        val = {"type":"vector","value":map(_wrap, val)}
#        pass
#    else:
#        val = _wrap_real(val)
#        pass
#    return val


samples_list = []
import time
for step_i in range(N_steps):
    start = time.time()
    samples_i = simulator.step()
    stop = time.time()
    delta = stop - start
    print 'step_i=%s took %s seconds' % (step_i, delta)
    samples_list.append(samples_i)
    pass

import numpy
import scene_plot_utils as spu
_samples_list = map(lambda x: numpy.array(x)[0, :, :], samples_list)
_samples_list = numpy.array(_samples_list)[:, :, 1:].tolist()
fig = spu.plot_scene(_samples_list, [(X_L, Y_L)],
        min_value=('dynamic', 5))
