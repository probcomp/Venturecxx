Overview
========

This document is meant to be normative, and therefore changes only by
unanimous consent.

- We use [Asana](http://asana.com) to coordinate tasks.

- We use [nosetests](https://nose.readthedocs.org/en/latest/) for running the test suite.

- We use [Starcluster](http://star.mit.edu/cluster/) over EC2 for cloud compute.

- We use [Jenkins](http://jenkins-ci.org/) for the continuous build.  As of this writing, the
  server listens to http://ec2-54-84-30-252.compute-1.amazonaws.com:8080/

- We use [pylint](http://www.pylint.org/) to maintain our Python code style.  The normative
  pylint configuration file is in `tool/pylintrc`.

Particulars
===========

Testing
-------

- `nosetests` at the top level runs our test suite.  At present,
  the suite defaults to confidence above speed.

- The test suite can be run in parallel via the nose multiprocessing
  plugin:
  `--processes=[NUM] --process-timeout=[SECONDS]`
  Note that the timeout is essentially for the whole suite rather than
  per test.

- The test suite can be sliced by test/group in the usual way.

- There is a test configuration for quickly checking for crashes (as
  opposed to poor inferences) in `crashes.cfg`; run it with
  `nosetests -c crashes.cfg`.

- The test suite can be configured to go faster at the cost of giving
  less confidence by setting configuration parameters:
  `--tc=num_samples:5 --tc=num_transitions_per_sample:5`

- The test suite can be configured to test different inference
  strategies and backends by choosing other parameters.  See
  `test/nconfig.py`.

- We treat a skipped test as an issue.  To wit, resolution is required
  but need not be immediate.  The actual skipped test should be linked
  to an issue in the issue tracker. [*] When that issue is closed, the
  test should be re-enabled.  Issues that have skipped tests
  associated with them should be marked as such, so the tests can be
  found (by grep) and turned back on.

  [*] While we're using Asana as the main issue tracker, this means
  copy the Asana URL of the task into the message given to the
  SkipTest exception.

- Python-side code coverage can be obtained via coverage.py and the
  nose-cov plugin by uncommenting the appropriate section in
  `setup.cfg`.

- Ideally, we would define task-oriented test launch patterns:
  - Confirm that there are no stupid crashes (quickly)
  - Confirm that inference method X in backend Y is correct (slower)
  - Confirm that inference method X in backend Y has the right asymptotic performance (very slow)
  - Confirm that all inference methods and backends are correct (even slower)
  - Confirm that all inference methods and backends have the right asymptotic performance (very even slower)
  - Benchmark some or all inference methods and backends
    - speed per transition
    - convergence per transition
    - convergence per computron
  - Profile the computations triggered by the tests (statistically or by instrumentation)
  - Issue: https://app.asana.com/0/9277419963067/9924589720829

Starcluster
-----------

- Right now, you're basically on your own here.  The only piece of
  help is an EC2 AMI with Venture CXX (and all its dependencies!)
  preinstalled: ami-59c9f930 .  Ask Dan Lovell for access to it if you want.

- Ideally, we would have a Starcluster Venture plugin that lets you
  type `starcluster start venture {master|release}` and get a cluster
  with Ventures as of the specified branch up and running with zero
  effort.  Issue: https://app.asana.com/0/9277419963067/9892931948558

Pylint
------

- Our pylint config doesn't work with the version packaged for Ubuntu,
  so install pylint from pip:
  `sudo pip install pylint`

- You can run pylint in batch mode using the Venture style with, e.g.,
  `pylint --rcfile=tool/pylintrc backend/lite/wttree.py`

- Pylint is more useful if the feedback is instantaneous.  If you edit
    in Emacs, this can be achieved using Flymake Mode:

    1. Either add the `tool/` directory to your PATH, or put a symlink
       on your path named `venture-epylint.py` and pointing to
       `tool/venture-epylint.py`

    2. Make sure your Emacs loads `tool/python-flymake.el` on startup,
       for example by adding `(load-file "/path/to/venture/tool/python-flymake.el")`
       to your `.emacs` file.

- Our attitude towards style violations is:

  - Code you recently understood (i.e., wrote, or heavily modified)
    should conform to the project style.
  - If there is a good reason to deviate from style, add a comment
    with `pylint: disable=<violation-type>` and a comment explaining
    why.
  - If you feel that a particular style constraint is too strict or
    inappropriate in general, let's discuss it.
