General Principles
==================

- This document is meant to be normative, and therefore changes only
  by unanimous consent.

- We treat a skipped test an a issue.  To wit, resolution is required
  but need not be immediate.  The actual skipped test should be linked
  to an issue in the issue tracker. [*] When that issue is closed, the
  test should be re-enabled.  Issues that have skipped tests
  associated with them should be marked as such, so the tests can be
  found (by grep) and turned back on.

[*] While we're using Asana as the main issue tracker, this means copy
the Asana URL of the task into the message given to the SkipTest
exception.

Tools
=====

- We use [Asana](http://asana.com) to coordinate tasks.

- We use nosetests for running the test suite (but the nosetests
  branch has not yet been merged into master, and see sanity_tests.sh
  for some additional that has not yet been ported to nose).

- We use Starcluster over EC2 for cloud compute.

- We use Jenkins for the continuous build.  As of this writing, the
  server listens to http://ec2-54-84-30-252.compute-1.amazonaws.com:8080/
