from venture.shortcuts import * 
#path_to_folder = r"C:\Shell_runs\Shell_reformulated_5001\Matlab_code"  
T = 4                                                                                    
ripl = make_lite_church_prime_ripl()
ripl.assume("sim","(make_simulator 201910502 5010)")
ripl.assume("get_params","""                                                                                   
(mem (lambda (t)                                                                                                 
(scope_include 0 t                                                                                             
  (array (uniform_continuous 0 1)                                                                              
         (uniform_continuous 0 1)                               
         (uniform_continuous 0 1)                                                                              
         (uniform_continuous 0 1)                                                                              
         (uniform_continuous 0 1)))))                                                                          
""")
ripl.assume("get_state","""                                                                                    
(mem (lambda (t)
(if (= t 0)
  (sim (quote initialize))
  (sim (quote simulate) (get_state (- t 1)) (get_params t)))))
""")

ripl.assume("get_emission","""
(lambda (t)                                                                                                 
(sim (quote emit) (get_state t)))
""")

ripl.assume("get_distance","(lambda (t) (sim (quote distance) (get_emission t)))")
for t in range(1, T+1): ripl.observe("(log_flip (get_distance %d))" % t,"true")
#ripl.infer({"kernel":"pgibbs","scope":0,"block":"ordered","particles":3,"with_mutation":False, "transitions":2})
#ripl.infer({"kernel":"mh","scope":0,"block":"one","transitions":1})
