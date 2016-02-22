Parallelism Across Traces
Notes circa mid-late 2014
Status: Implemented

There is an opportunity for an "embarassingly parallel" kind of win
from running independent chains in parallel.  The mripl does this, but
a) is tied up with IPCluster as a parallelization strategy
b) is tied up with tons of other pieces of code for reporting, etc

The parallelism in question can also be recovered at the trace-engine
interface.  The minimum-viable version of that is to:
- Factor weighted-trace-set out of engine and teach it to be able
  to operate on its traces in parallel.  Options:
  - Python multiprocessing with new processes per operation: Sucks;
    error reporting is pretty bad; huge overhead (presumably) for
    spawning processes and returning results (whole traces!) from them
    - Only even remotely useful for long inference programs
  - Python multiprocessing with persistent processes: Sucks; error
    reporting is pretty bad; some processes may die stochastically
  - Python multiprocessing via IPCluster: Isn't this what we were
    trying to avoid by moving off mripl?  Also sucks because engines
    die, etc.
  - Migrate the structure to C++ and use threads: Sucks in a different
    way, but should be doable.  Vlad?  Downside: Puma only.  Upside:
    much faster collection of results, since serialization is not
    needed for inter-process transmission.  Much more feasible to
    parallelize finer-grain operations.
  - Does Python have a story for shared-memory threading as opposed to
    multiprocessing, or does the global interpreter lock just make
    that a complete nonstarter?
- Add supported ways to query all the particles in the weighted set
  instead of just one: {sample,report}_all_available or such.
- Downside of this approach: the samples are only iid if the only
  resampling was done at the beginning; no way to do multiple SMC
  chains.

To recover SMC, additionally do this:
- Change the data structure from a weighted set to an independent set
  of weighted sets (whatever the parallelism strategy was).
- Change reinit_inference_problem to take an additional argument for
  the number of independent weighted sets to have.
- Add a "grow new iid" command (either as an infer command or as a
  method on engine) that does the same thing but leaves the existing
  iid sets in place instead of replaying them.  These two are the only
  way to increase the number of weighted sets.
- Add a "drop iid" command (ditto).
- INFER (resample n) is mapped across the independent sets but
  resamples inside the weighted sets.
- Everything that is currently mapped across the weighted set is now
  mapped across the entire structure.
- Everything that currently relies on a distinguished trace should
  still rely on a distinguished trace, but appropriate ones should
  grow versions that map over the independent weighted sets.
- If there is any reason for it, can add a block_resample command that
  takes a list of particle counts whose length must be the same as the
  current number of independent weighted sets.  Problem with this:
  samples from the independent sets will now remain independent but
  will not be from the same distribution.
