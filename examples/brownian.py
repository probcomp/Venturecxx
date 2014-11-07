def build_brownian_model(step_form, noise_form):
  return """
[assume brown_step
  (scope_include (quote param) 0 {})]

[assume obs_noise
  (scope_include (quote param) 1 {})]

[assume position (mem (lambda (t)
  (scope_include (quote exp) t
   (if (<= t 0)
       (normal 0 brown_step)
       (normal (position (- t 1)) brown_step)))))]

[assume obs_fun (lambda (t)
  (normal (position t) obs_noise))]

[predict (position 10)]""".format(step_form, noise_form)

