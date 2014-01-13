require("engine.jl")
require("utils.jl")

function printTest(testName,eps,ops)
  println(string("---Test: ",testName,"---"))
  print("Expected: ") ; show(eps) ; println("")
  print("Observed: ") ; show(ops) ; println("")
end


function countPredictions(predictions, seq)
  return [count(y->y==x,predictions) for x in seq]
end

function runJTests(N)
  testFlip0(N)
  testFlip1(N)
  testCategorical1(N)
  testMHNormal0(N)
  testMHNormal1(N)
  testSprinkler1(N)
  testSprinkler2(N)
  testMHHMM1(N)
  testOuterMix1(N)
  testGamma1(N)
  testIf1(N)
  testIf2(N)
  testBLOGCSI(N)
#  testGeometric1(N)
  testMem(N)
  testAAA(N)
  testGibbs(N)
end

function jprofile(N,filename="dump.txt")
  testMakeSymDirMult1("make_usym_dir_mult", 100)
  Profile.clear()
  @profile testMakeSymDirMult1("make_usym_dir_mult", N)
  f = open("dump.txt","w")  
  Profile.print(f,format = :flat)
end

function testAAA(N)
  testMakeSymDirMult1("make_sym_dir_mult", N)
  testMakeSymDirMult1("make_usym_dir_mult", N)
  testMakeSymDirMult2(N)
  testMakeSymDirMult3(N)
end



function testMem(N)
  testMem0(N)
  testMem1(N)
  testMem2(N)
  testMem3(N)
  testMem4(N)
end

function testGamma1(N)
  sivm = Engine()
  assume(sivm,"a","(gamma 10.0 10.0)")
  assume(sivm,"b","(gamma 10.0 10.0)")
  predict(sivm,"(gamma a b)")

  predictions = loggingInfer(sivm.trace,3,N=N)
  println("---TestMHGamma1---")
  println(string("(10000,",mean(predictions),")"))
end

function testIf1(N)
  sivm = Engine()
  assume(sivm,"IF","branch")
  assume(sivm,"IF2","(if (flip 0.5) IF IF)")
  predict(sivm,"(IF2 (flip 0.5) IF IF)")
  infer(sivm.trace,N=N)
  println("Passed TestIf1()")
end

function testIf2(N)
  sivm = Engine()
  assume(sivm,"if1", "(if (flip 0.5) branch branch)")
  assume(sivm,"if2", "(if (flip 0.5) if1 if1)")
  assume(sivm,"if3", "(if (flip 0.5) if2 if2)")
  assume(sivm,"if4", "(if (flip 0.5) if3 if3)")
  infer(sivm.trace,N=N)
  println("Passed TestIf2()")
end

function testBLOGCSI(N)
  sivm = Engine()
  assume(sivm,"u","(flip 0.3)")
  assume(sivm,"v","(flip 0.9)")
  assume(sivm,"w","(flip 0.1)")
  assume(sivm,"getParam","(lambda (z) (if z 0.8 0.2))")
  assume(sivm,"x","(flip (if u (getParam w) (getParam v)))")
  
  predictions = loggingInfer(sivm.trace,5,N=N)
  ps = [.596, .404]
  eps = normalizeList(countPredictions(predictions, [true, false]))
  printTest("TestBLOGCSI",ps,eps)
end

function testMHHMM1(N)
  sivm = Engine()
  assume(sivm,"f","""
(mem (lambda (i) (if (== i 0) (normal 0.0 1.0) (normal (f (- i 1)) 1.0))))
""")
  assume(sivm,"g","""
(mem (lambda (i) (normal (f i) 1.0)))
""")
  observe(sivm,"(g 0)",1.0)
  observe(sivm,"(g 1)",2.0)
  observe(sivm,"(g 2)",3.0)
  observe(sivm,"(g 3)",4.0)
  observe(sivm,"(g 4)",5.0)
  predict(sivm,"(f 4)")

  predictions = loggingInfer(sivm.trace,8,N=N)
  println("---TestMHHMM1---")
  println(string("(4.3ish,",mean(predictions),")"))
end

function testGeometric1(N)
  sivm = Engine()
  assume(sivm,"alpha1","(gamma 50.0 50.0)")
  assume(sivm,"alpha2","(gamma 50.0 50.0)")
  assume(sivm,"p", "(beta alpha1 alpha2)")
  assume(sivm,"geo","(lambda (p) (if (flip p) 1 (+ 1 (geo p))))")
  predict(sivm,"(geo p)")
  
  predictions = loggingInfer(sivm.trace,5,N=N)

  k = 6
  ps = [^(2.0,-n) for n in 1:k]
  eps = normalizeList(countPredictions(predictions, 1:k))
  printTest("TestGeometric1",ps,eps)
end

function testFlip0(N)
  sivm = Engine()
  assume(sivm,"b", "((lambda () (flip 0.5)))")
  predict(sivm,"""
(if
  b
  (normal 0.0 1.0)
  (normal 10.0 1.0))
""")
  predictions = loggingInfer(sivm.trace,2,N=N)
  println("---TestFlip0---")
  println(string("(5.0,",mean(predictions),")"))
end

function testFlip1(N)
  sivm = Engine()
  assume(sivm,"b", "((lambda () (flip 0.7)))")
  predict(sivm,"""
(if
  b
  (normal 0.0 1.0)
  ((lambda () (normal 10.0 1.0))))
""")
  predictions = loggingInfer(sivm.trace,2,N=N)
  println("---TestFlip1---")
  println(string("(3.0,",mean(predictions),")"))
end

function testCategorical1(N)
  sivm = Engine()
  assume(sivm,"x", "(categorical (float_array 0.1 0.2 0.3 0.4))")
  assume(sivm,"y", "(categorical (float_array 0.2 0.6 0.2))")
  predict(sivm,"(+ x y)")

  predictions = loggingInfer(sivm.trace,3,N=N)
  ps = [0.1 * 0.2, 
        0.1 * 0.6 + 0.2 * 0.2,
        0.1 * 0.2 + 0.2 * 0.6 + 0.3 * 0.2,
        0.2 * 0.2 + 0.3 * 0.6 + 0.4 * 0.2,
        0.3 * 0.2 + 0.4 * 0.6,
        0.4 * 0.2]
  eps = normalizeList(countPredictions(predictions, [2,3,4,5,6,7]))
  printTest("testCategorical1",ps,eps)
end

function testMHNormal0(N)
  sivm = Engine()
  assume(sivm,"a", "(normal 10.0 1.0)")
  observe(sivm,"(normal a 1.0)", 14.0)
  predict(sivm,"(normal a 1.0)")

  predictions = loggingInfer(sivm.trace,3,N=N)
  println("---TestMHNormal0---")
  println(string("(12.0,",mean(predictions),")"))
end    

function testMHNormal1(N)
  sivm = Engine()
  assume(sivm,"a", "(normal 10.0 1.0)")
  assume(sivm,"b", "(normal a 1.0)")
  observe(sivm,"((lambda () (normal b 1.0)))", 14.0)
  predict(sivm,"""
(if (< a 100.0) 
        (normal (+ a b) 1.0)
        (normal (* a b) 1.0))
""")

  predictions = loggingInfer(sivm.trace,4,N=N)
  println("---TestMHNormal1---")
  println(string("(23.9,",mean(predictions),")"))
end

function testOuterMix1(N)
  sivm = Engine()
  predict(sivm,"""
(if (flip 0.5) 
  (if (flip 0.5) 2 3)
  1)
""")

  predictions = loggingInfer(sivm.trace,1,N=N)
  ps = [.5, .25,.25]
  eps = normalizeList(countPredictions(predictions, [1, 2, 3]))
  printTest("TestOuterMix1",ps,eps)
end

function testMem0(N)
  sivm = Engine()
  assume(sivm,"f","(mem (lambda (x) (flip 0.5)))")
  predict(sivm,"(f (flip 0.5))")
  predict(sivm,"(f (flip 0.5))")
  infer(sivm.trace,N=N)
  println("Passed TestMem0")
end

function testMem1(N)
  sivm = Engine()
  assume(sivm,"f","(mem (lambda (arg) (categorical (float_array 0.4 0.6))))")
  assume(sivm,"x","(f 1)")
  assume(sivm,"y","(f 1)")
  assume(sivm,"w","(f 2)")
  assume(sivm,"z","(f 2)")
  assume(sivm,"q","(categorical (float_array 0.1 0.9))")
  predict(sivm,"(+ x y w z q)")

  predictions = loggingInfer(sivm.trace,7,N=N)
  ps = [0.4 * 0.4 * 0.1, 0.6 * 0.6 * 0.9]
  eps = normalizeList(countPredictions(predictions, [5,10]),N)
  printTest("TestMem1",ps,eps)
end

function testMem2(N)
  sivm = Engine()
  assume(sivm,"f","(mem (lambda (arg) (categorical (float_array 0.4 0.6))))")
  assume(sivm,"g","((lambda () (mem (lambda (y) (f (+ y 1))))))")
  assume(sivm,"x","(f ((branch (flip 0.5) (quote (lambda () 1)) (quote (lambda () 1)))))")
  assume(sivm,"y","(g ((lambda () 0)))")
  assume(sivm,"w","((lambda () (f 2)))")
  assume(sivm,"z","(g 1)")
  assume(sivm,"q","(categorical (float_array 0.1 0.9))")
  predict(sivm,"(+ x y w z q)")

  predictions = loggingInfer(sivm.trace,8,N=N)
  ps = [0.4 * 0.4 * 0.1, 0.6 * 0.6 * 0.9]
  eps = normalizeList(countPredictions(predictions, [5,10]),N)
  printTest("TestMem2",ps,eps)
end

function testMem3(N)
  sivm = Engine()
  assume(sivm,"f","(mem (lambda (arg) (categorical (float_array 0.4 0.6))))")
  assume(sivm,"g","((lambda () (mem (lambda (y) (f (+ y 1))))))")
  assume(sivm,"x","(f ((lambda () 1)))")
  assume(sivm,"y","(g ((lambda () (branch (flip 1.0) (quote 0) (quote 100)))))")
  assume(sivm,"w","((lambda () (f 2)))")
  assume(sivm,"z","(g 1)")
  assume(sivm,"q","(categorical (float_array 0.1 0.9))")
  predict(sivm,"(+ x y w z q)")

  predictions = loggingInfer(sivm.trace,8,N=N)
  ps = [0.4 * 0.4 * 0.1, 0.6 * 0.6 * 0.9]
  eps = normalizeList(countPredictions(predictions, [5,10]),N)
  printTest("TestMem3",ps,eps)
end

function testMem4(N)
  sivm = Engine()
  assume(sivm,"f","(mem (lambda (x) (uniform_discrete 1 10000)))")
  (id1,val1) = predict(sivm,"(f 1)")
  (id2,val2) = predict(sivm,"(f 1)")
  for n = 1:N
    infer(sivm.trace)
    @assert extractValue(sivm.trace,id1) == extractValue(sivm.trace,id2)
  end
  println("Passed TestMem4")
end


function testSprinkler1(N)
  sivm = Engine()
  assume(sivm,"rain","(flip 0.2)")
  assume(sivm,"sprinkler","(branch rain (quote (flip 0.01)) (quote (flip 0.4)))")
  assume(sivm,"grassWet","""
(if rain 
(if sprinkler (flip 0.99) (flip 0.8))
(if sprinkler (flip 0.9) (flip 0.00001)))
""")
  observe(sivm,"grassWet", true)

  predictions = loggingInfer(sivm.trace,1,N=N)
  ps = [.3577,.6433]
  eps = normalizeList(countPredictions(predictions, [true,false]))
  printTest("TestSprinkler1",ps,eps)
end

function testSprinkler2(N)
  # this test needs more iterations than most others, because it mixes badly
  N = 5*N

  sivm = Engine()
  assume(sivm,"rain","(flip 0.2)")
  assume(sivm,"sprinkler","(flip (if rain 0.01 0.4))")
  assume(sivm,"grassWet","""
(flip (if rain 
(if sprinkler 0.99 0.8)
(if sprinkler 0.9 0.00001)))
""")
  observe(sivm,"grassWet", true)

  predictions = loggingInfer(sivm.trace,1,N=N)
  ps = [.3577,.6433]
  eps = normalizeList(countPredictions(predictions, [true,false]))
  printTest("TestSprinkler2 (mixes terribly)",ps,eps)
end


function testMakeSymDirMult1(name::String, N::Int)
  sivm = Engine()
  assume(sivm,"a","(normal 10.0 1.0)")
  assume(sivm,"f",string("(",name," a 4)"))
  predict(sivm,"(f)")
  testDirichletMultinomial1(name,sivm,3,N)
end

function testMakeSymDirMult2(N::Int)
  sivm = Engine()
  assume(sivm,"a","(normal 10.0 1.0)")
  assume(sivm,"f","(if (flip 0.5) (make_sym_dir_mult a 4) (make_usym_dir_mult a 4))")
  predict(sivm,"(f)")
  testDirichletMultinomial1("testMakeSymDirMult2",sivm,3,N)
end

function testMakeSymDirMult3(N::Int)
  sivm = Engine()
  assume(sivm,"a","(normal 10.0 1.0)")
  assume(sivm,"f","""
((if (flip 0.4) 
     make_sym_dir_mult 
    (if (flip .66)
        make_usym_dir_mult
        (lambda (alpha k) ((lambda (theta) (lambda () (categorical theta))) (dirichlet k alpha)))))
 a 4)
""")
  predict(sivm,"(f)")
  testDirichletMultinomial1("testMakeSymDirMult3",sivm,3,N)
end


function testDirichletMultinomial1(name::String, sivm::Engine, index::Int, N::Int)
  for i = 2:4
    for j = 1:20
      observe(sivm,"(f)",i)
    end
  end

  predictions = loggingInfer(sivm.trace,index,N=N)
  ps = [.1,.3,.3,.3]
  eps = normalizeList(countPredictions(predictions, [1,2,3,4]))
  printTest(string("testDirichletMultinomial(",name,")"),ps,eps)
end


function testScope1(N)
  # this test needs more iterations than most others, because it mixes badly
  N = 5*N

  sivm = Engine()
  assume(sivm,"rain","(apply_in_scope 0 0 (flip 0.2))")
  assume(sivm,"sprinkler","(apply_in_scope 0 0 (flip (if rain 0.01 0.4)))")
  assume(sivm,"grassWet","""
(flip (if rain 
(if sprinkler 0.99 0.8)
(if sprinkler 0.9 0.00001)))
""")
  observe(sivm,"grassWet", true)

  predictions = loggingInfer(sivm.trace,1,N=N)
  ps = [.3577,.6433]
  eps = normalizeList(countPredictions(predictions, [true,false]))
  printTest("TestSprinkler2 (mixes terribly)",ps,eps)
end

function testGibbs1(N)
  sivm = Engine()
  (id,val) = predict(sivm,"(bernoulli)")
  predictions = loggingGibbsInfer(sivm.trace,id,"default",N)
  ps = [.5,.5]
  println(predictions)
  eps = normalizeList(countPredictions(predictions, [1,0]))
  printTest("testGibbs1",ps,eps)
end

function testGibbs2(N)
  sivm = Engine()
  (xid,_) = assume(sivm,"x","(apply_in_scope \"xor\" 0 (bernoulli 0.001))")
  (yid,_) = assume(sivm,"y","(apply_in_scope \"xor\" 0 (bernoulli 0.001))")
  observe(sivm,"(noisy_true (== (+ x y) 1) .001)",true)
  predictions = loggingGibbsInfer(sivm.trace,xid,"xor",N)
  println(predictions)

  ps = [.5,.5]
  eps = normalizeList(countPredictions(predictions, [1,0]))
  printTest(string("testGibbs2"),ps,eps)

end

function testPGibbs1(N,P)
  sivm = Engine()
  assume(sivm,"f","""
(mem (lambda (i) 
  (if (== i 0) 
    (apply_in_scope \"hmm\" i (normal 0.0 1.0)) 
    (apply_in_scope \"hmm\" i (normal (f (- i 1)) 1.0)))))
""")
  assume(sivm,"g","""
(mem (lambda (i) (normal (f i) 1.0)))
""")
  observe(sivm,"(g 0)",1.0)
  observe(sivm,"(g 1)",2.0)
  observe(sivm,"(g 2)",3.0)
  observe(sivm,"(g 3)",4.0)
  observe(sivm,"(g 4)",5.0)
  (id,_) = predict(sivm,"(f 4)")

  predictions = loggingPGibbsInfer(sivm.trace,id,"hmm",N,P)
  println("---TestMHHMM1---")
  println(string("(4.3ish,",mean(predictions),")"))
end
