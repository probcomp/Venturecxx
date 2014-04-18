from venture.shortcuts import * 
def testSimulator1():
  #path_to_folder = r"C:\Shell_runs\Shell_reformulated_5001\Matlab_code"  
  T = 4                                                                                    
  ripl = make_lite_church_prime_ripl()
  ripl.assume("sim","(make_simulator (quote not_used) (quote 201910502) 5010)")
  ripl.assume("get_init","(lambda () (scope_include 0 0 (sim (quote initialize))))")
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
  (sim (quote simulate) (get_params t) t (if (= t 0) (get_init) (get_state (- t 1))))))                                                                    
""")

  ripl.assume("get_emission","""                                                                                 
(mem (lambda (t)                                                                                                 
  (sim (quote emit) (get_state t))))                                                                                           
""")

  ripl.assume("get_distance","(mem (lambda (t) (sim (quote distance) (get_emission t))))")
  for t in range(T): ripl.observe("(log_flip (get_distance %d))" % t,"true")
  #ripl.infer({"kernel":"pgibbs","scope":0,"block":"ordered","particles":50,"with_mutation":False, "transitions":2})
  ripl.infer({"kernel":"mh","scope":0,"block":"one","transitions":5})
  
testSimulator1()
  

  
  
  
  
  
  
  
  