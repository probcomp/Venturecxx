# TODO this is a reasonable refactor, but it is not used yet.
def checkAsymptotics(Ns,loadRIPLfn,params,validate):
  inferTimes = []
  for N in Ns:
    ripl = loadRIPLfn(N)
    start = time.clock()
    ripl.infer(params)
    end = time.clock()
    inferTimes.append(end - start)

  assert validate(inferTimes)

