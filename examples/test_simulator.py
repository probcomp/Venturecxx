
# coding: utf-8

# In[ ]:

import time
import math
#
from venture.venturemagics.ip_parallel import MRipl


# In[ ]:

# inference settings
N_mripls = 64
N_infer = 200
backend = 'lite'

# simulation settings
Y_L = 100
velocity = 100
X_L = 200
X_0 = 0
N_steps = 5


# In[ ]:

# general helpers
def printif(boolean, to_print):
    if boolean:
        print to_print
    return
pi_over_180 = math.pi / 180
pi_over_2 = math.pi / 2
def convert_X_L_rel_to_theta(X_L_rel):
    theta = None
    if X_L_rel == 0:
        theta = pi_over_2
    else:
        slope = Y_L / float(X_L_rel)
        theta = math.atan(slope)
    return theta
def get_hypotenuse(x, y):
    return math.sqrt(x**2 + y**2)
def convert_X_L_rel_to_d(X_L_rel):
    return get_hypotenuse(X_L_rel, Y_L)

# observation data
xs = [step_i * velocity for step_i in range(N_steps)]
X_L_rels = [X_L - x for x in xs]
ds = map(convert_X_L_rel_to_d, X_L_rels)
thetas = map(convert_X_L_rel_to_theta, X_L_rels)
distance_observation_data = [('get_noisy_distance_observation', d) for d in ds]
angle_observation_data = [('get_noisy_angle_observation', theta) for theta in thetas]
#
observe_list = zip(distance_observation_data, angle_observation_data)
sample_list = ['(repeat (lambda()(get_state %s)) 16)' % i for i range(N_steps)]

# In[ ]:

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

program_constants = """

[ASSUME velocity %s]

[ASSUME Y_L %s]

[ASSUME X_L %s]

[ASSUME X_0 %s]

[ASSUME HEADING_0 0]

[ASSUME pi_over_180 %s]

""" % (velocity, Y_L, X_L, X_0, pi_over_180)

program_assumes = """

[ASSUME velocity_error_std (scope_include (quote hypers) 0 (gamma 1.0 1.0))]

[ASSUME heading_error_std (scope_include (quote hypers) 0 (gamma 1.0 1.0))]

[ASSUME angle_observation_error_std (scope_include (quote hypers) 0 (gamma 1.0 0.1))]

[ASSUME distance_observation_error_std (scope_include (quote hypers) 0 (gamma 1.0 1.0))]

[ASSUME get_noisy_velocity
  (mem
    (lambda (t) (normal velocity velocity_error_std))
  )
]

[ASSUME get_noisy_heading
  (mem
    (lambda (heading t) (normal heading heading_error_std))
  )
]

[ASSUME get_noisy_distance_observation
  (lambda (t) (
    normal
    (sub X_L (get_x (get_state t)))
    distance_observation_error_std
  ))
]

[ASSUME state_to_theta
  (lambda (state)
    (atan (div Y_L (sub X_L (get_x state))))
  )
]

[ASSUME degrees_to_radians
  (lambda (degrees)
    (mul degrees pi_over_180)
    )
]
    
[ASSUME get_noisy_angle_observation
  (lambda (t)
    (normal (state_to_theta (get_state t)) (degrees_to_radians angle_observation_error_std))
    )
]

[ASSUME get_heading
  (lambda (state)
    (lookup state 0)
  )
]

[ASSUME get_x
  (lambda (state)
    (lookup state 1)
  )
]

[ASSUME get_y
  (lambda (state)
    (lookup state 2)
  )
]

[ASSUME increment_x
  (lambda (state t)
    (+
      (get_x state)
      (mul
        (get_noisy_velocity t)
        (cos (degrees_to_radians (get_heading state)))
        )
      )
    )
]

[ASSUME increment_y
  (lambda (state t)
    (+
      (get_y state)
      (mul
        (get_noisy_velocity t)
        (sin (degrees_to_radians (get_heading state)))
        )
      )
    )
]

[ASSUME increment_state
  (lambda (state t)
    (list
      (get_noisy_heading (get_heading state) t)
      (increment_x state t)
      (increment_y state t)
      )
  )
]
    
[ASSUME get_state
  (mem (lambda (t)
    (if (= t 0)
        (list 0 0 0)
        (increment_state (get_state (- t 1)) t)
    )
  ))
]
"""


# In[ ]:

v=MRipl(N_mripls, backend=backend)


# In[ ]:

constants_out = v.execute_program(program_constants);
assumes_out = v.execute_program(program_assumes)


# In[ ]:

deadreckon_heading_out = v.snapshot(exp_list=exp_list_heading, plot=True);


# In[ ]:

deadreckon_x_out = v.snapshot(exp_list=exp_list_x, plot=True);


# In[ ]:

deadreckon_y_out = v.snapshot(exp_list=exp_list_y, plot=True);


# In[ ]:

angle_observes_out = observe_data(v, angle_observation_data)
distance_observes_out = observe_data(v, distance_observation_data)
start = time.time()
infer_out = v.infer(N_infer)
first_infer_duration = time.time() - start


# In[ ]:

post_observe_x_out = v.snapshot(exp_list=exp_list_x, plot=True)


# In[ ]:

post_observe_y_out = v.snapshot(exp_list=exp_list_y, plot=True)


# In[ ]:

new_x = N_steps * velocity
new_X_L_rel = X_L - new_x
new_d = convert_X_L_rel_to_d(new_X_L_rel)
new_distance_observation_datum = ('get_noisy_distance_observation', new_d)
new_theta = convert_X_L_rel_to_theta(new_X_L_rel)
new_angle_observation_datum = ('get_noisy_angle_observation', new_theta)
#
observe_datum(v, (N_steps, new_distance_observation_datum))
observe_datum(v, (N_steps, new_angle_observation_datum))
start = time.time()
new_infer_out = v.infer(N_infer)
new_infer_duration = time.time() - start


# In[ ]:

print N_steps
print first_infer_duration
print new_infer_duration


# In[ ]:

nth_state = 2
x = post_observe_x_out['values']['(get_x (get_state %s))' % nth_state]
y = post_observe_y_out['values']['(get_y (get_state %s))' % nth_state]
scatter(x, y)
title('\n'.join([
    'Particles for state %s' % nth_state,
    '"Ground truth" is (%s, %s)' % (xs[nth_state], 0),
]))

